# alerter.py — EscudoAI

import asyncio
import os
import pyautogui
from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from scorer import get_report

def take_screenshot():
    """Take screenshot and save it."""
    os.makedirs("screenshots", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"screenshots/fraud_{timestamp}.png"
    pyautogui.screenshot(path)
    return path

async def send_fraud_alert():
    """Send fraud alert with screenshot and Allow/Deny buttons."""
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    report = get_report()

    # Build signal summary
    signals_text = ""
    for s in report["signals"]:
        signals_text += f"  • {s['signal']} → +{s['points']} pts at {s['time']}\n"

    message = (
        f"🚨 *EscudoAI FRAUD ALERT* 🚨\n\n"
        f"*Fraud Score:* {report['total_score']}/100\n"
        f"*Verdict:* {'🔴 FRAUD DETECTED' if report['is_fraud'] else '🟡 SUSPICIOUS'}\n\n"
        f"*Suspicious Activities:*\n{signals_text}\n"
        f"*Time:* {datetime.now().strftime('%H:%M:%S')}\n\n"
        f"What do you want to do?"
    )

    # Allow / Deny buttons
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ ALLOW", callback_data="allow"),
            InlineKeyboardButton("🔴 DENY & LOCK", callback_data="deny")
        ]
    ])

    # Take and send screenshot
    screenshot = take_screenshot()
    with open(screenshot, 'rb') as photo:
        await bot.send_photo(
            chat_id=TELEGRAM_CHAT_ID,
            photo=photo,
            caption=message,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    print("[EscudoAI] Fraud alert sent to owner!")

def trigger_alert():
    """Trigger the fraud alert."""
    asyncio.run(send_fraud_alert())

if __name__ == "__main__":
    # Test the alerter
    from scorer import add_signal
    add_signal("camera_blocked")
    add_signal("private_file")
    trigger_alert()