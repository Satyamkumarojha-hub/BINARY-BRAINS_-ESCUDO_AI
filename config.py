# config.py — EscudoAI

# Telegram bot settings
TELEGRAM_BOT_TOKEN = "8748793433:AAEdc01HzlBD6m5M5GYRiD9eancndcX7hNY"
TELEGRAM_CHAT_ID   = "8229599480E"

# Security settings
MAX_PASSWORD_ATTEMPTS = 3
FRAUD_SCORE_THRESHOLD = 60

# Signal scores (these feed the ML scorer)
SCORES = {
    "camera_blocked":   30,
    "usb_inserted":     25,
    "phone_detected":   20,
    "unusual_app":      15,
    "private_file":     50,
}

# Private files/folders to watch
PRIVATE_PATHS = [
    r"C:\Users\hp\Documents",
    r"C:\Users\hp\Desktop",
]

# Password to unlock (we'll hash this later)
UNLOCK_PASSWORD = "secure123"

# Emergency lock password (only owner knows this)
EMERGENCY_PASSWORD = "adminrecover999"
