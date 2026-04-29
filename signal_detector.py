# signal_detector.py — EscudoAI Signal Detection

import cv2
import os
import time
import subprocess
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from scorer import add_signal

# ── Keep track of known devices so we only alert on NEW insertions ──
_known_usb_count  = None
_known_hdmi_count = None


# ============================================================
# CABLE / USB / HDMI DETECTION  (Windows — PowerShell)
# ============================================================

def _run_ps(command: str) -> str:
    """Run a PowerShell command and return stdout, empty string on error."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True, text=True, timeout=4
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _count_usb_devices() -> int:
    """Count currently connected USB storage / data devices."""
    out = _run_ps(
        "Get-PnpDevice -Class USB | "
        "Where-Object { $_.Status -eq 'OK' } | "
        "Measure-Object | Select-Object -ExpandProperty Count"
    )
    try:
        return int(out)
    except ValueError:
        return 0


def _count_hdmi_devices() -> int:
    """Count active display/monitor outputs (HDMI / DisplayPort / VGA)."""
    out = _run_ps(
        "Get-PnpDevice -Class Monitor | "
        "Where-Object { $_.Status -eq 'OK' } | "
        "Measure-Object | Select-Object -ExpandProperty Count"
    )
    try:
        return int(out)
    except ValueError:
        return 0


def _get_new_usb_names() -> list[str]:
    """Return friendly names of newly connected USB devices."""
    out = _run_ps(
        "Get-PnpDevice -Class USB | "
        "Where-Object { $_.Status -eq 'OK' } | "
        "Select-Object -ExpandProperty FriendlyName"
    )
    return [line.strip() for line in out.splitlines() if line.strip()]


def detect_cable_insertion() -> dict:
    """
    Compare current USB & HDMI device counts against baseline.
    Returns a dict:
        {
          "usb_new":  True/False,
          "hdmi_new": True/False,
          "devices":  ["Device name", ...]   # newly added device names
        }
    Updates the baseline so repeated polls don't re-alert on same device.
    """
    global _known_usb_count, _known_hdmi_count

    current_usb  = _count_usb_devices()
    current_hdmi = _count_hdmi_devices()

    result = {"usb_new": False, "hdmi_new": False, "devices": []}

    # First call — just set baseline, don't alert
    if _known_usb_count is None:
        _known_usb_count  = current_usb
        _known_hdmi_count = current_hdmi
        print(f"[EscudoAI] 🔌 Cable baseline — USB: {current_usb}, HDMI: {current_hdmi}")
        return result

    # USB increased → new device plugged in
    if current_usb > _known_usb_count:
        result["usb_new"] = True
        result["devices"] = _get_new_usb_names()
        print(f"[EscudoAI] 🔌 NEW USB device detected! "
              f"({_known_usb_count} → {current_usb})")
        _known_usb_count = current_usb

    # HDMI / display output increased → possible screen-capture cable
    if current_hdmi > _known_hdmi_count:
        result["hdmi_new"] = True
        print(f"[EscudoAI] 🖥️  NEW display cable detected! "
              f"({_known_hdmi_count} → {current_hdmi})")
        _known_hdmi_count = current_hdmi

    return result


# ============================================================
# PHONE CAMERA DETECTION
# ============================================================

def detect_phone_in_frame(frame) -> bool:
    """Detect if a phone camera is pointed at the screen."""
    try:
        gray     = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges    = cv2.Canny(gray, 100, 200)
        contours, _ = cv2.findContours(
            edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )
        for contour in contours:
            area = cv2.contourArea(contour)
            if 5000 < area < 50000:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = float(w) / h if h > 0 else 0
                if 0.4 < aspect_ratio < 0.8:
                    print("[EscudoAI] 🚨 PHONE CAMERA DETECTED — recording attempt!")
                    return True
    except Exception:
        pass
    return False


# ============================================================
# PRIVATE FILE ACCESS DETECTION  (watchdog)
# ============================================================

class PrivateFileHandler(FileSystemEventHandler):
    """Monitor private file access and feed scorer."""

    def __init__(self):
        super().__init__()
        self._last_alert: dict[str, float] = {}

    def _is_private(self, path: str) -> bool:
        skip = ["logs", "venv", "screenshots", ".git",
                "AppData", "Windows", "__pycache__", "Temp"]
        if any(s.lower() in path.lower() for s in skip):
            return False

        private_exts = [
            '.docx', '.pdf', '.xlsx', '.pptx', '.txt', '.key',
            '.db', '.doc', '.xls', '.ppt', '.csv', '.sql', '.env',
            '.json', '.xml', '.config', '.pem', '.ppk',
        ]
        ext = os.path.splitext(path)[1].lower()
        if ext in private_exts:
            return True

        private_folders = [
            "Documents", "Desktop", "Downloads",
            "Pictures", "Videos", "OneDrive",
        ]
        for folder in private_folders:
            if folder.lower() in path.lower():
                return True
        return False

    def _should_alert(self, path: str) -> bool:
        now = time.time()
        if now - self._last_alert.get(path, 0) > 5:
            self._last_alert[path] = now
            return True
        return False

    def _handle(self, label: str, path: str):
        if self._is_private(path) and self._should_alert(path):
            fname = os.path.basename(path)
            print(f"[EscudoAI] 📄 {label}: {fname}")
            add_signal("private_file")

    def on_modified(self, event):
        if not event.is_directory:
            self._handle("MODIFIED", event.src_path)

    def on_created(self, event):
        if not event.is_directory:
            self._handle("CREATED", event.src_path)

    def on_opened(self, event):
        if not event.is_directory:
            self._handle("OPENED", event.src_path)


def start_file_monitor() -> Observer:
    """Start monitoring private file access. Returns the Observer."""
    observer = Observer()
    handler  = PrivateFileHandler()
    home     = os.path.expanduser("~")
    observer.schedule(handler, home, recursive=True)
    observer.start()
    print("[EscudoAI] 👁️  Private file monitor started")
    return observer


# ============================================================
# COMBINED SIGNAL CHECK  (called from main loop)
# ============================================================

def check_all_signals(frame):
    """
    Check all suspicious signals in one call.
    Feeds scorer and sends Telegram alerts for cables.
    """
    # ── Phone recording ──────────────────────────────────────
    if detect_phone_in_frame(frame):
        add_signal("phone_recording")

    # ── Cable / USB / HDMI ───────────────────────────────────
    cable = detect_cable_insertion()
    if cable["usb_new"]:
        add_signal("usb_inserted", ", ".join(cable["devices"]) if cable["devices"] else "")
        print(f"[EscudoAI] 🔌 USB signal recorded — score updated.")

    if cable["hdmi_new"]:
        add_signal("hdmi_connected")
        print(f"[EscudoAI] 🖥️  HDMI signal recorded — score updated.")
     


def _alert_cable(cable_type: str, devices: list[str]):
    """Fire an immediate Telegram alert when a cable is plugged in."""
    try:
        from alerter import send_cable_alert
        send_cable_alert(cable_type, devices)
    except Exception as e:
        print(f"[EscudoAI] Cable alert error: {e}")

# ============================================================
if __name__ == "__main__":
    observer = start_file_monitor()
    try:
        print("[EscudoAI] File + cable monitor running… Ctrl+C to stop")
        while True:
            result = detect_cable_insertion()
            if result["usb_new"]:
                add_signal("usb_inserted", ", ".join(cable["devices"]) if cable["devices"] else "")
            if result["hdmi_new"]:
                add_signal("hdmi_connected")
            time.sleep(3)
    except KeyboardInterrupt:
        observer.stop()
        print("[EscudoAI] Stopped.")
    observer.join()
