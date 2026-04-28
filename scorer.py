# scorer.py — EscudoAI

from config import SCORES, FRAUD_SCORE_THRESHOLD
import json
import os
from datetime import datetime

# Current session state
session_score = 0
triggered_signals = []  # ✅ Single source of truth — was 'session_signals' in some places (caused crash)


def get_total_score():
    """Returns sum of all signal points in this session."""
    return sum(s["points"] for s in triggered_signals)  # ✅ Fixed: was 'session_signals'


def add_signal(signal_name):
    """Add a suspicious signal and update score."""
    global session_score

    # ✅ Moved print AFTER docstring, and fixed logic
    if signal_name in ["private_file", "phone_recording"]:  # ✅ Fixed: 'phone_recording' matches config.py
        print("[EscudoAI] ⚠️  HIGH RISK ACTION DETECTED!")

    if signal_name in SCORES:
        points = SCORES[signal_name]
        session_score += points
        triggered_signals.append({
            "signal": signal_name,
            "points": points,
            "time": datetime.now().strftime("%H:%M:%S")
        })
        print(f"[EscudoAI] Signal: {signal_name} | +{points} pts | Total: {session_score}/{FRAUD_SCORE_THRESHOLD}")
        log_signal(signal_name, points)
    else:
        print(f"[EscudoAI] Unknown signal: '{signal_name}' — check config.py SCORES dict")


def is_fraud():
    """Returns True if current session meets fraud criteria."""
    total = get_total_score()
    signals = [s["signal"] for s in triggered_signals]  # ✅ Fixed: was 'session_signals'

    # Instant fraud triggers (regardless of score)
    if "private_file" in signals:
        print("[EscudoAI] 🚨 Instant fraud: private file accessed!")
        return True

    if "phone_recording" in signals:  # ✅ Fixed: was 'phone_detected' (not in config)
        print("[EscudoAI] 🚨 Instant fraud: phone recording detected!")
        return True

    # Score-based fraud
    if total >= FRAUD_SCORE_THRESHOLD:
        print(f"[EscudoAI] 🚨 Score fraud: {total} >= {FRAUD_SCORE_THRESHOLD}")
        return True

    return False


def get_score():
    """Returns current session score."""
    return session_score


def get_report():
    """Returns full session report as a dict."""
    return {
        "total_score": session_score,
        "threshold": FRAUD_SCORE_THRESHOLD,
        "is_fraud": is_fraud(),
        "triggered_signals": triggered_signals  # ✅ Renamed key to be accurate
    }


def reset_score():
    """Reset session score and signals for a new session."""
    global session_score, triggered_signals
    session_score = 0
    triggered_signals = []
    print("[EscudoAI] Session score reset.")


def log_signal(signal_name, points):
    """Append signal event to log file."""
    os.makedirs("logs", exist_ok=True)
    log_path = "logs/session_log.txt"
    with open(log_path, "a") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {signal_name} | +{points} pts | Total: {session_score}/{FRAUD_SCORE_THRESHOLD}\n")


if __name__ == "__main__":
    print("Testing EscudoAI scorer...")
    add_signal("camera_blocked")
    add_signal("usb_inserted")
    add_signal("private_file")
    print(f"\nFraud detected: {is_fraud()}")
    print(f"\nFull report:\n{json.dumps(get_report(), indent=2)}")
