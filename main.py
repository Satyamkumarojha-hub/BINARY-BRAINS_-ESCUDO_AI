# main.py - EscudoAI

import cv2
import asyncio
import threading
import time
from face_detector import verify_face
from auth import show_lock_screen
from scorer import add_signal, is_fraud, reset_score, get_score
from alerter import trigger_alert
from monitor import start_bot_listener
from signal_detector import check_all_signals, start_file_monitor, detect_phone_in_frame

last_alert_time = 0
ALERT_COOLDOWN = 15  # seconds
CAMERA_INDEX = 1
alert_sent = False
unauthorized_user_active = False
phone_alert_sent = False

# Timing constants
NORMAL_CHECK_INTERVAL = 10   # seconds between checks in normal mode
RAPID_CHECK_INTERVAL  = 5    # seconds between checks in rapid mode
RAPID_CHECK_COUNT     = 4    # how many rapid checks before asking password

# Shared camera frame (updated by camera thread, read by phone monitor)
latest_frame = None
frame_lock = threading.Lock()


def monitor_camera():
    """
    Normal mode  : verify face every 10 sec.
    Rapid mode   : if unauthorized found, verify every 5 sec × 4 times.
    Password     : only if ALL 4 rapid checks are unauthorized.
    Resume       : if owner found during rapid checks, go back to 10 sec.
    """
    global alert_sent, unauthorized_user_active, latest_frame
    print("[EscudoAI] Starting camera monitor...")
    cam = cv2.VideoCapture(CAMERA_INDEX)

    while True:

        # Always keep reading frames so phone monitor stays fresh
        ret, frame = cam.read()
        if ret:
            with frame_lock:
                latest_frame = frame.copy()

        # ── Skip face checks while an authorized stranger is being monitored ──
        if unauthorized_user_active:
            print("[EscudoAI] Unauthorized user active — monitoring fraud only.")
            time.sleep(NORMAL_CHECK_INTERVAL)
            continue

        if not ret:
            print("[EscudoAI] Camera read failed — retrying...")
            time.sleep(2)
            continue

        is_owner = verify_face(frame)

        if is_owner:
            print("[EscudoAI] ✅ Owner verified. System secure.")
            time.sleep(NORMAL_CHECK_INTERVAL)
            continue

        # ── UNAUTHORIZED DETECTED → enter rapid-check mode ────────────────────
        print("[EscudoAI] ⚠️  Unauthorized face detected! Entering rapid-check mode...")

        rapid_unauthorized_count = 0

        for i in range(1, RAPID_CHECK_COUNT + 1):
            time.sleep(RAPID_CHECK_INTERVAL)

            ret, frame = cam.read()
            if ret:
                with frame_lock:
                    latest_frame = frame.copy()

            if not ret:
                print(f"[EscudoAI] Rapid check {i}/{RAPID_CHECK_COUNT}: camera read failed — skipping.")
                continue

            is_owner = verify_face(frame)

            if is_owner:
                print(f"[EscudoAI] ✅ Owner found on rapid check {i}/{RAPID_CHECK_COUNT}. Resuming normal mode.")
                rapid_unauthorized_count = 0
                break
            else:
                rapid_unauthorized_count += 1
                print(f"[EscudoAI] 🔴 Rapid check {i}/{RAPID_CHECK_COUNT}: still unauthorized ({rapid_unauthorized_count} confirmed).")

        # ── ALL 4 RAPID CHECKS FAILED → ask for password ──────────────────────
        if rapid_unauthorized_count == RAPID_CHECK_COUNT:
            print(f"[EscudoAI] 🚨 Unauthorized confirmed {RAPID_CHECK_COUNT}/{RAPID_CHECK_COUNT} times! Showing lock screen...")

            # Grab intruder photo BEFORE releasing cam
            intruder_photo = None
            ret2, snap = cam.read()
            if ret2:
                import os, cv2 as _cv2
                os.makedirs("screenshots", exist_ok=True)
                intruder_photo = "screenshots/intruder_face.jpg"
                _cv2.imwrite(intruder_photo, snap)

            cam.release()
            result = show_lock_screen(intruder_photo=intruder_photo)

            if result >= 3:
                print("[EscudoAI] ❌ 3 wrong attempts — Owner alerted!")
            else:
                print("[EscudoAI] ✅ Password correct — Access granted. Monitoring fraud...")
                unauthorized_user_active = True
                reset_score()
                alert_sent = False
                # ── Start file-access monitor now that stranger has access ──
                threading.Thread(
                    target=_start_file_watcher,
                    daemon=True
                ).start()

            cam = cv2.VideoCapture(CAMERA_INDEX)

        time.sleep(NORMAL_CHECK_INTERVAL)


def _start_file_watcher():
    """
    Starts watchdog file monitor and sends an IMMEDIATE Telegram alert
    whenever a private file/folder is accessed by the unauthorized user.
    Keeps running until unauthorized_user_active is False.
    """
    global unauthorized_user_active
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    from alerter import send_file_access_alert
    import os

    class _FileAlertHandler(FileSystemEventHandler):
        def __init__(self):
            super().__init__()
            self._alerted = {}  # path → last alert time

        def _should_alert(self, path):
            now = time.time()
            if now - self._alerted.get(path, 0) > 5:
                self._alerted[path] = now
                return True
            return False

        def _is_private(self, path):
            skip = ["logs", "venv", "screenshots", ".git", "AppData",
                    "Windows", "__pycache__", "Temp", "temp"]
            if any(s.lower() in path.lower() for s in skip):
                return False
            private_exts = [
                '.docx', '.pdf', '.xlsx', '.pptx', '.txt', '.key',
                '.db', '.doc', '.xls', '.ppt', '.csv', '.sql', '.env',
                '.json', '.xml', '.config', '.pem', '.ppk'
            ]
            private_folders = [
                "Documents", "Desktop", "Downloads", "Pictures",
                "Videos", "OneDrive"
            ]
            ext = os.path.splitext(path)[1].lower()
            if ext in private_exts:
                return True
            for folder in private_folders:
                if folder.lower() in path.lower():
                    return True
            return False

        def _handle(self, event_type, path):
            if not unauthorized_user_active:
                return
            if not self._is_private(path):
                return
            if not self._should_alert(path):
                return
            fname = os.path.basename(path)
            print(f"[EscudoAI] 📂 {event_type}: {fname} — sending IMMEDIATE alert!")
            add_signal("private_file")
            send_file_access_alert(event_type, path)

        def on_modified(self, event):
            if not event.is_directory:
                self._handle("MODIFIED", event.src_path)

        def on_created(self, event):
            if not event.is_directory:
                self._handle("CREATED", event.src_path)

        def on_opened(self, event):
            if not event.is_directory:
                self._handle("OPENED", event.src_path)

    observer = Observer()
    handler  = _FileAlertHandler()

    watch_dirs = [
        os.path.expanduser("~"),
        r"C:\Users\hp\Documents",
        r"C:\Users\hp\Desktop",
    ]
    for d in watch_dirs:
        if os.path.isdir(d):
            observer.schedule(handler, d, recursive=True)

    observer.start()
    print("[EscudoAI] 📂 File-access watcher started (unauthorized session).")

    try:
        while unauthorized_user_active:
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()
        print("[EscudoAI] 📂 File-access watcher stopped.")


def monitor_behaviour():
    global alert_sent, last_alert_time
    print("[EscudoAI] Behaviour monitor started...")

    while True:
        if is_fraud():
            current_time = time.time()
            if current_time - last_alert_time > ALERT_COOLDOWN:
                print("[EscudoAI] Fraud threshold reached! Sending consolidated alert...")
                trigger_alert()
                last_alert_time = current_time
                alert_sent = True
                asyncio.run(start_bot_listener())
                reset_score()
                alert_sent = False
            else:
                print("[EscudoAI] Fraud detected but cooldown active — waiting...")
        time.sleep(2)


def monitor_phone_recording():
    """Monitor for phone recording attempts — IMMEDIATE ALERT."""
    global phone_alert_sent, unauthorized_user_active
    print("[EscudoAI] Phone recording monitor started...")

    while True:
        if unauthorized_user_active and not phone_alert_sent:
            with frame_lock:
                frame = latest_frame.copy() if latest_frame is not None else None

            if frame is not None and detect_phone_in_frame(frame):
                print("\n[EscudoAI] 🚨 PHONE RECORDING ATTEMPT DETECTED!")
                add_signal("phone_recording")
                print("[EscudoAI] Sending IMMEDIATE alert for phone recording...")
                from alerter import send_phone_recording_alert
                send_phone_recording_alert()
                phone_alert_sent = True
                asyncio.run(start_bot_listener())
                phone_alert_sent = False
                unauthorized_user_active = False
        time.sleep(1)


if __name__ == "__main__":
    print("""
    ███████╗███████╗ ██████╗██╗   ██╗██████╗  ██████╗      █████╗ ██╗
    ██╔════╝██╔════╝██╔════╝██║   ██║██╔══██╗██╔═══██╗    ██╔══██╗██║
    █████╗  ███████╗██║     ██║   ██║██║  ██║██║   ██║    ███████║██║
    ██╔══╝  ╚════██║██║     ██║   ██║██║  ██║██║   ██║    ██╔══██║██║
    ███████╗███████║╚██████╗╚██████╔╝██████╔╝╚██████╔╝    ██║  ██║██║
    ╚══════╝╚══════╝ ╚═════╝ ╚═════╝ ╚═════╝  ╚═════╝     ╚═╝  ╚═╝╚═╝
    The Shield That Never Sleeps
    """)

    print("[EscudoAI] System starting...")
    print("[EscudoAI] Press Ctrl+C to stop\n")

    cam_thread   = threading.Thread(target=monitor_camera,          daemon=True)
    beh_thread   = threading.Thread(target=monitor_behaviour,       daemon=True)
    phone_thread = threading.Thread(target=monitor_phone_recording,  daemon=True)

    cam_thread.start()
    beh_thread.start()
    phone_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[EscudoAI] System stopped.")
