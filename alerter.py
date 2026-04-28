# alerter.py — EscudoAI

import asyncio
import os
import pyautogui
from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from scorer import get_report


# ─────────────────────────────────────────────────────────────
# Screenshot helper
# ─────────────────────────────────────────────────────────────

def take_screenshot() -> str:
    """Take a screenshot and return the saved path."""
    os.makedirs("screenshots", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"screenshots/fraud_{timestamp}.png"
    pyautogui.screenshot(path)
    return path


# ─────────────────────────────────────────────────────────────
# Fraud alert  (existing — unchanged logic)
# ─────────────────────────────────────────────────────────────

async def send_fraud_alert():
    bot    = Bot(token=TELEGRAM_BOT_TOKEN)
    report = get_report()

    signals_text = ""
    for s in report.get("triggered_signals", []):
        signals_text += f"  • {s['signal']}  +{s['points']} pts  @ {s['time']}\n"

    message = (
        "🚨 EscudoAI FRAUD ALERT\n\n"
        f"Fraud Score : {report['total_score']}/100\n"
        f"Verdict     : {'FRAUD DETECTED' if report['is_fraud'] else 'SUSPICIOUS'}\n\n"
        f"Suspicious Activities:\n{signals_text}\n"
        f"Time: {datetime.now().strftime('%H:%M:%S')}\n\n"
        "What do you want to do?"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ ALLOW",          callback_data="allow"),
            InlineKeyboardButton("🔴 DENY AND LOCK",  callback_data="deny"),
        ]
    ])

    screenshot = take_screenshot()
    with open(screenshot, "rb") as photo:
        await bot.send_photo(
            chat_id=TELEGRAM_CHAT_ID,
            photo=photo,
            caption=message,
            reply_markup=keyboard,
        )
    print("[EscudoAI] Fraud alert sent to owner!")


def trigger_alert():
    asyncio.run(send_fraud_alert())


# ─────────────────────────────────────────────────────────────
# Phone recording alert  (existing — unchanged logic)
# ─────────────────────────────────────────────────────────────

async def _send_phone_alert():
    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    message = (
        "🚨 EscudoAI CRITICAL ALERT\n\n"
        "📱 PHONE RECORDING DETECTED\n\n"
        "An unauthorized user is attempting to record your screen with their phone camera!\n\n"
        f"Time: {datetime.now().strftime('%H:%M:%S')}\n\n"
        "What do you want to do?"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ ALLOW",         callback_data="allow"),
            InlineKeyboardButton("🔴 DENY AND LOCK", callback_data="deny"),
        ]
    ])

    screenshot = take_screenshot()
    with open(screenshot, "rb") as photo:
        await bot.send_photo(
            chat_id=TELEGRAM_CHAT_ID,
            photo=photo,
            caption=message,
            reply_markup=keyboard,
        )
    print("[EscudoAI] Phone recording alert sent to owner!")


def send_phone_recording_alert():
    asyncio.run(_send_phone_alert())


# ─────────────────────────────────────────────────────────────
# ✅ NEW — Immediate file-access alert
# ─────────────────────────────────────────────────────────────

async def _send_file_access_alert(event_type: str, file_path: str):
    """
    Fires an IMMEDIATE Telegram alert when an unauthorized user
    opens / modifies / creates a private file or folder.
    Includes a live screenshot so you can see exactly what they're doing.
    Gives you ALLOW / DENY AND LOCK buttons to respond instantly.
    """
    bot      = Bot(token=TELEGRAM_BOT_TOKEN)
    filename = os.path.basename(file_path)

    message = (
        f"📂 FILE ACCESS ALERT — {event_type}\n\n"
        f"⚠️  An unauthorized user just accessed a private file!\n\n"
        f"File : {filename}\n"
        f"Path : {file_path}\n"
        f"Time : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        "What do you want to do?"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ ALLOW",         callback_data="allow"),
            InlineKeyboardButton("🔴 DENY AND LOCK", callback_data="deny"),
        ]
    ])

    # Attach a live screenshot so you can see what's on screen RIGHT NOW
    screenshot = take_screenshot()
    with open(screenshot, "rb") as photo:
        await bot.send_photo(
            chat_id=TELEGRAM_CHAT_ID,
            photo=photo,
            caption=message,
            reply_markup=keyboard,
        )
    print(f"[EscudoAI] 📨 File-access alert sent: {filename}")


def send_file_access_alert(event_type: str, file_path: str):
    """Sync wrapper — safe to call from any thread."""
    asyncio.run(_send_file_access_alert(event_type, file_path))


# ─────────────────────────────────────────────────────────────
# Quick test
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from scorer import add_signal
    add_signal("camera_blocked")
    add_signal("private_file")
    trigger_alert()
