# config.py - EscudoAI

# Telegram bot settings
TELEGRAM_BOT_TOKEN = "8748793433:AAEdc01HzlBD6m5M5GYRiD9eancndcX7hNY"
TELEGRAM_CHAT_ID   = "8229599480"

# Security settings
MAX_PASSWORD_ATTEMPTS = 3
FRAUD_SCORE_THRESHOLD = 60

# Signal scores
SCORES = {
    "camera_blocked":   30,
    "usb_inserted":     25,
    "phone_recording":   40,
    "unusual_app":      15,
    "private_file":     60,
     "cable_conected":  35
    
}

# Private files/folders to watch
PRIVATE_PATHS = [
    r"C:\Users\hp\Documents",
    r"C:\Users\hp\Desktop",
]

# Passwords
UNLOCK_PASSWORD = "secure123"
EMERGENCY_PASSWORD = "adminrecover999"
# Private file indicators
PRIVATE_FILES = {
    # Financial
    ".xlsx": "Financial spreadsheet",
    ".xls": "Financial data",
    
    # Documents
    ".docx": "Private document",
    ".pdf": "Private PDF",
    
    # Passwords & Keys
    ".key": "Encryption key",
    ".pem": "SSH key",
    ".ppk": "Private key",
    ".db": "Database file",
    
    # Code & Config
    ".env": "Configuration file",
    ".config": "Config file",
    
    # Sensitive
    ".txt": "Text file (if in private folder)",
}

# Private folder names to monitor
PRIVATE_FOLDERS = [
    "Documents",
    "Desktop", 
    "Downloads",
    "Pictures",
    "Videos",
    "OneDrive",
]
