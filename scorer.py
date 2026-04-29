# scorer.py — EscudoAI

from config import SCORES, FRAUD_SCORE_THRESHOLD
import json
import os
from datetime import datetime

session_score     = 0
triggered_signals = []


def get_total_score():
    return sum(s["points"] for s in triggered_signals)


def add_signal(signal_name: str, detail: str = ""):
    """
    Add a suspicious signal and update score.
    detail = optional extra context shown in Telegram alerts, e.g. USB device name.
    """
    global session_score

    if signal_name in ["private_file", "phone_recording"]:
        print("[EscudoAI] ⚠️  HIGH RISK ACTION DETECTED!")

    if signal_name in SCORES:
        points = SCORES[signal_name]
        session_score += points

        entry = {
            "signal": signal_name,
            "points": points,
            "time":   datetime.now().strftime("%H:%M:%S"),
        }
        if detail:
            entry["detail"] = detail

        triggered_signals.append(entry)

        detail_str = f" ({detail})" if detail else ""
        print(f"[EscudoAI] Signal: {signal_name}{detail_str} | "
              f"+{points} pts | Total: {session_score}/{FRAUD_SCORE_THRESHOLD}")
        log_signal(signal_name, points)
    else:
        print(f"[EscudoAI] Unknown signal: '{signal_name}' — check config.py SCORES dict")


def is_fraud():
    total   = get_total_score()
    signals = [s["signal"] for s in triggered_signals]

    if "private_file" in signals:
        print("[EscudoAI] 🚨 Instant fraud: private file accessed!")
        return True

    if "phone_recording" in signals:
        print("[EscudoAI] 🚨 Instant fraud: phone recording detected!")
        return True

    if total >= FRAUD_SCORE_THRESHOLD:
        print(f"[EscudoAI] 🚨 Score fraud: {total} >= {FRAUD_SCORE_THRESHOLD}")
        return True

    return False


def get_score():
    return session_score


def get_report():
    return {
        "total_score":       session_score,
        "threshold":         FRAUD_SCORE_THRESHOLD,
        "is_fraud":          is_fraud(),
        "triggered_signals": triggered_signals,
    }


def reset_score():
    global session_score, triggered_signals
    session_score     = 0
    triggered_signals = []
    print("[EscudoAI] Session score reset.")


def log_signal(signal_name, points):
    os.makedirs("logs", exist_ok=True)
    with open("logs/session_log.txt", "a") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {signal_name} | +{points} pts | "
                f"Total: {session_score}/{FRAUD_SCORE_THRESHOLD}\n")


if __name__ == "__main__":
    add_signal("usb_inserted", "SanDisk Ultra USB 3.0")
    add_signal("private_file", "C:/Users/hp/Documents/salary.xlsx")
    print(f"\nFraud: {is_fraud()}")
    print(json.dumps(get_report(), indent=2))
