# auth.py — EscudoAI

import tkinter as tk
from tkinter import messagebox
import asyncio
from telegram import Bot
from config import UNLOCK_PASSWORD, MAX_PASSWORD_ATTEMPTS, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
import pyautogui
import os
from datetime import datetime

attempt_count = 0

def take_screenshot():
    """Take a screenshot and save it."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"screenshots/attempt_{timestamp}.png"
    pyautogui.screenshot(path)
    return path

async def send_alert(message, image_path=None):
    """Send Telegram alert to owner."""
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    if image_path and os.path.exists(image_path):
        with open(image_path, 'rb') as photo:
            await bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=photo)

def send_telegram_alert(message, image_path=None):
    """Wrapper to run async alert."""
    asyncio.run(send_alert(message, image_path))

def show_lock_screen():
    """Show password lock screen."""
    global attempt_count
    attempt_count = 0

    root = tk.Tk()
    root.title("EscudoAI — Locked")
    root.attributes('-fullscreen', True)
    root.configure(bg='#1a1a2e')
    root.attributes('-topmost', True)

    # Title
    tk.Label(root, text="🛡️ EscudoAI", font=("Arial", 36, "bold"),
             bg='#1a1a2e', fg='#e94560').pack(pady=60)

    tk.Label(root, text="Unauthorised access detected",
             font=("Arial", 16), bg='#1a1a2e', fg='#ffffff').pack(pady=10)

    tk.Label(root, text="Enter password to continue",
             font=("Arial", 14), bg='#1a1a2e', fg='#aaaaaa').pack(pady=5)

    # Password entry
    password_var = tk.StringVar()
    entry = tk.Entry(root, textvariable=password_var, show='*',
                     font=("Arial", 18), width=20, justify='center')
    entry.pack(pady=20)
    entry.focus()

    # Status label
    status_label = tk.Label(root, text="", font=("Arial", 12),
                             bg='#1a1a2e', fg='#e94560')
    status_label.pack(pady=5)

    def check_password(event=None):
        global attempt_count
        entered = password_var.get()

        if entered == UNLOCK_PASSWORD:
            status_label.config(text="✅ Access granted", fg='#00ff88')
            root.after(1000, root.destroy)
        else:
            attempt_count += 1
            remaining = MAX_PASSWORD_ATTEMPTS - attempt_count
            if attempt_count >= MAX_PASSWORD_ATTEMPTS:
                status_label.config(text="❌ Too many attempts! Owner alerted!", fg='#e94560')
                screenshot = take_screenshot()
                send_telegram_alert(
                    "🚨 EscudoAI ALERT!\n\nUnauthorised user tried 3 wrong passwords on your laptop!\nImmediate attention required!",
                    screenshot
                )
                root.after(2000, root.destroy)
            else:
                status_label.config(
                    text=f"❌ Wrong password! {remaining} attempt(s) left",
                    fg='#e94560'
                )
                password_var.set("")

    entry.bind('<Return>', check_password)

    tk.Button(root, text="Unlock", command=check_password,
              font=("Arial", 14), bg='#e94560', fg='white',
              padx=20, pady=8).pack(pady=10)

    root.mainloop()
    return attempt_count

if __name__ == "__main__":
    show_lock_screen()