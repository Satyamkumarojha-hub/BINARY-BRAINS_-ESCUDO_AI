# monitor.py — EscudoAI

import asyncio
import subprocess
import sys
from telegram.ext import Application, CallbackQueryHandler
from telegram import Update
from config import TELEGRAM_BOT_TOKEN, EMERGENCY_PASSWORD
from scorer import add_signal, is_fraud, reset_score
from alerter import trigger_alert

alert_sent = False

async def handle_response(update: Update, context):
    """Handle owner's Allow/Deny response from Telegram."""
    query = update.callback_query
    await query.answer()

    if query.data == "allow":
        await query.edit_message_caption(
            caption="✅ Access ALLOWED by owner.\nEscudoAI continues monitoring...",
            reply_markup=None
        )
        reset_score()
        print("[EscudoAI] Owner allowed access. Monitoring continues.")

    elif query.data == "deny":
        await query.edit_message_caption(
            caption="🔴 Access DENIED by owner.\nLaptop is being locked NOW!",
            reply_markup=None
        )
        print("[EscudoAI] Owner denied access. Locking laptop!")
        lock_laptop()

def lock_laptop():
    """Hard lock the laptop immediately."""
    print("[EscudoAI] Initiating hard lock...")
    if sys.platform == "win32":
        subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])

async def start_bot_listener():
    """Start listening for Allow/Deny button presses."""
    print("[EscudoAI] Listening for owner response on Telegram...")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CallbackQueryHandler(handle_response))
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    print("[EscudoAI] Bot listener active! Waiting for owner response...")
    await asyncio.sleep(60)
    await app.updater.stop()
    await app.stop()
    await app.shutdown()

if __name__ == "__main__":
    from scorer import add_signal
    add_signal("camera_blocked")
    add_signal("usb_inserted")
    add_signal("private_file")
    if is_fraud():
        print("[EscudoAI] Fraud detected! Sending alert...")
        trigger_alert()
    asyncio.run(start_bot_listener())
