# scorer.py — EscudoAI

from config import SCORES, FRAUD_SCORE_THRESHOLD
import json
import os
from datetime import datetime

# Current session score
session_score = 0
triggered_signals = []

def add_signal(signal_name):
    """Add a suspicious signal and update score."""
    global session_score

    if signal_name in SCORES:
        points = SCORES[signal_name]
        session_score += points
        triggered_signals.append({
            "signal": signal_name,
            "points": points,
            "time": datetime.now().strftime("%H:%M:%S")
        })
        print(f"[EscudoAI] Signal detected: {signal_name} +{points} pts | Total: {session_score}")
        log_signal(signal_name, points)
    else:
        print(f"[EscudoAI] Unknown signal: {signal_name}")

def is_fraud():
    """Returns True if score exceeds fraud threshold."""
    return session_score >= FRAUD_SCORE_THRESHOLD

def get_score():
    """Returns current session score."""
    return session_score

def get_report():
    """Returns full session report."""
    return {
        "total_score": session_score,
        "threshold": FRAUD_SCORE_THRESHOLD,
        "is_fraud": is_fraud(),
        "signals": triggered_signals
    }

def reset_score():
    """Reset session score and signals."""
    global session_score, triggered_signals
    session_score = 0
    triggered_signals = []
    print("[EscudoAI] Session score reset.")

def log_signal(signal_name, points):
    """Log signal to file."""
    os.makedirs("logs", exist_ok=True)
    log_path = "logs/session_log.txt"
    with open(log_path, "a") as f:
        f.write(f"{datetime.now()} | {signal_name} | +{points} pts | Total: {session_score}\n")

if __name__ == "__main__":
    # Test the scorer
    print("Testing EscudoAI scorer...")
    add_signal("camera_blocked")
    add_signal("usb_inserted")
    add_signal("private_file")
    print(f"\nFraud detected: {is_fraud()}")
    print(f"Full report: {json.dumps(get_report(), indent=2)}")