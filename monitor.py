# monitor.py - EscudoAI

import asyncio
import subprocess
import sys
import threading
from telegram.ext import Application, CallbackQueryHandler
from telegram import Update
from config import TELEGRAM_BOT_TOKEN

lock_requested  = threading.Event()
allow_requested = threading.Event()


async def handle_response(update: Update, context):
    """Handle button clicks from Telegram."""
    query = update.callback_query
    
    # ✅ Always answer the callback query (removes hourglass/loading spinner)
    try:
        await query.answer()
    except Exception as e:
        print(f"[EscudoAI] Callback answer error: {e}")

    if query.data == "allow":
        try:
            await query.edit_message_caption(
                caption="✅ Access ALLOWED. EscudoAI continues monitoring...",
                reply_markup=None,
            )
        except Exception as e:
            print(f"[EscudoAI] Message edit error: {e}")
        
        print("[EscudoAI] ✅ Owner ALLOWED access.")
        allow_requested.set()

    elif query.data == "deny":
        try:
            await query.edit_message_caption(
                caption="🔴 Access DENIED. Locking laptop RIGHT NOW!",
                reply_markup=None,
            )
        except Exception as e:
            print(f"[EscudoAI] Message edit error: {e}")
        
        print("[EscudoAI] 🔴 Owner DENIED — locking NOW!")
        lock_laptop()        # ← Lock fires IMMEDIATELY here
        lock_requested.set()
    
    else:
        print(f"[EscudoAI] Unknown callback data: {query.data}")


def lock_laptop():
    """Lock the Windows workstation immediately."""
    print("[EscudoAI] 🔒 Executing lock command...")
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["rundll32.exe", "user32.dll,LockWorkStation"],
                check=True, timeout=5,
            )
        else:
            subprocess.run(["loginctl", "lock-session"], check=False)
        print("[EscudoAI] 🔒 Laptop locked.")
    except subprocess.TimeoutExpired:
        subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"])
    except Exception as e:
        print(f"[EscudoAI] Lock error: {e}")


async def _run_bot_listener(timeout: int = 120):
    """
    Start Telegram bot polling and wait for button response.
    Timeout: max seconds to wait for owner response.
    """
    print(f"[EscudoAI] 📡 Waiting for owner response (up to {timeout}s)...")
    lock_requested.clear()
    allow_requested.clear()

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # ✅ Add the callback query handler FIRST before starting
    app.add_handler(CallbackQueryHandler(handle_response))
    
    print("[EscudoAI] 🤖 Bot initialized and listening for button clicks...")
    
    # Initialize and start the application
    await app.initialize()
    await app.start()
    
    # ✅ FIXED: Removed drop_pending_updates=True
    # This was causing button clicks to be ignored!
    # Now with drop_pending_updates=False, all updates are processed
    await app.updater.start_polling(
        allowed_updates=Update.ALL_TYPES,  # ✅ Listen to ALL updates
        drop_pending_updates=False         # ✅ Don't drop pending updates
    )

    print("[EscudoAI] ✅ Polling started — waiting for button click...")
    
    elapsed = 0
    while elapsed < timeout:
        if lock_requested.is_set():
            print("[EscudoAI] 🔴 DENY button was pressed!")
            break
        if allow_requested.is_set():
            print("[EscudoAI] ✅ ALLOW button was pressed!")
            break
        
        await asyncio.sleep(1)
        elapsed += 1
        
        # Every 10 sec, remind user
        if elapsed % 10 == 0:
            print(f"[EscudoAI] Still waiting for response... ({timeout - elapsed}s remaining)")

    # Shutdown the bot gracefully
    try:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        print("[EscudoAI] ✅ Bot listener stopped.")
    except Exception as e:
        print(f"[EscudoAI] Shutdown note (safe to ignore): {e}")


def start_bot_listener(timeout: int = 120):
    """
    Sync wrapper to start the async bot listener.
    Uses SelectorEventLoop on Windows to avoid __del__ crashes.
    """
    if sys.platform == "win32":
        loop = asyncio.SelectorEventLoop()
    else:
        loop = asyncio.new_event_loop()

    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_run_bot_listener(timeout))
    finally:
        try:
            # Clean up any pending tasks
            pending = asyncio.all_tasks(loop)
            for t in pending:
                t.cancel()
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        except Exception:
            pass
        finally:
            loop.close()
            asyncio.set_event_loop(None)


if __name__ == "__main__":
    # Test mode
    print("[EscudoAI] Testing bot listener...")
    start_bot_listener(timeout=30)
    print("[EscudoAI] Test complete.")
