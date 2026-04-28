# auth.py — EscudoAI

import tkinter as tk
import asyncio
import os
import cv2
import pyautogui
from datetime import datetime
from telegram import Bot
from config import UNLOCK_PASSWORD, MAX_PASSWORD_ATTEMPTS, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

attempt_count = 0


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def take_screenshot() -> str:
    """Take a screenshot and return the saved path."""
    os.makedirs("screenshots", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"screenshots/attempt_{timestamp}.png"
    pyautogui.screenshot(path)
    return path


def take_camera_photo(intruder_photo: str | None) -> str | None:
    """
    Use the pre-captured intruder photo if available,
    otherwise try to capture a fresh one from the camera.
    Returns file path or None.
    """
    # Prefer the snapshot taken just before lock screen was shown
    if intruder_photo and os.path.exists(intruder_photo):
        return intruder_photo

    # Fallback: open camera ourselves
    try:
        cam = cv2.VideoCapture(1)
        import time; time.sleep(0.5)        # warm-up
        ret, frame = cam.read()
        cam.release()
        if ret:
            os.makedirs("screenshots", exist_ok=True)
            path = "screenshots/intruder_fallback.jpg"
            cv2.imwrite(path, frame)
            return path
    except Exception as e:
        print(f"[EscudoAI] Camera photo error: {e}")
    return None


async def _send_alert(message: str, *image_paths):
    """Send a Telegram message followed by one photo per path."""
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    for path in image_paths:
        if path and os.path.exists(path):
            with open(path, "rb") as f:
                await bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=f)


def send_telegram_alert(message: str, *image_paths):
    """Sync wrapper to fire the async alert."""
    asyncio.run(_send_alert(message, *image_paths))


# ─────────────────────────────────────────────────────────────
# Lock screen
# ─────────────────────────────────────────────────────────────

def show_lock_screen(intruder_photo: str | None = None) -> int:
    """
    Show full-screen password lock.

    Returns attempt_count so caller can decide:
      >= MAX_PASSWORD_ATTEMPTS  →  owner was alerted (intruder)
      <  MAX_PASSWORD_ATTEMPTS  →  correct password entered
    """
    global attempt_count
    attempt_count = 0

    root = tk.Tk()
    root.title("EscudoAI — Locked")
    root.attributes("-fullscreen", True)
    root.configure(bg="#1a1a2e")
    root.attributes("-topmost", True)

    # ── UI ──────────────────────────────────────────────────
    tk.Label(root, text="🛡️ EscudoAI", font=("Arial", 36, "bold"),
             bg="#1a1a2e", fg="#e94560").pack(pady=60)

    tk.Label(root, text="Unauthorised access detected",
             font=("Arial", 16), bg="#1a1a2e", fg="#ffffff").pack(pady=10)

    tk.Label(root, text="Enter password to continue",
             font=("Arial", 14), bg="#1a1a2e", fg="#aaaaaa").pack(pady=5)

    password_var = tk.StringVar()
    entry = tk.Entry(root, textvariable=password_var, show="*",
                     font=("Arial", 18), width=20, justify="center")
    entry.pack(pady=20)
    entry.focus()

    status_label = tk.Label(root, text="", font=("Arial", 12),
                             bg="#1a1a2e", fg="#e94560")
    status_label.pack(pady=5)

    # ── Password check ───────────────────────────────────────
    def check_password(event=None):
        global attempt_count
        entered = password_var.get()

        if entered == UNLOCK_PASSWORD:
            status_label.config(text="✅ Access granted", fg="#00ff88")
            root.after(1000, root.destroy)

        else:
            attempt_count += 1
            remaining = MAX_PASSWORD_ATTEMPTS - attempt_count

            if attempt_count >= MAX_PASSWORD_ATTEMPTS:
                status_label.config(
                    text="❌ Too many attempts! Owner alerted!", fg="#e94560"
                )
                # ── Capture evidence ─────────────────────────
                screenshot   = take_screenshot()
                camera_photo = take_camera_photo(intruder_photo)

                print("[EscudoAI] 🚨 3 wrong attempts — sending full alert (photo + screenshot)...")

                send_telegram_alert(
                    "🚨 EscudoAI ALERT!\n\n"
                    "❌ An intruder entered the WRONG PASSWORD 3 times!\n"
                    "📸 Intruder photo attached.\n"
                    "🖥️  Screen screenshot attached.\n\n"
                    f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    camera_photo,   # photo 1 — intruder face
                    screenshot,     # photo 2 — screen
                )

                root.after(2000, root.destroy)

            else:
                status_label.config(
                    text=f"❌ Wrong password! {remaining} attempt(s) left",
                    fg="#e94560",
                )
                password_var.set("")

    entry.bind("<Return>", check_password)

    tk.Button(root, text="Unlock", command=check_password,
              font=("Arial", 14), bg="#e94560", fg="white",
              padx=20, pady=8).pack(pady=10)

    root.mainloop()
    return attempt_count


if __name__ == "__main__":
    show_lock_screen()
