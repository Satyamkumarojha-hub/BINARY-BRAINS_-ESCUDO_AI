# main.py - EscudoAI

import cv2
import asyncio
import threading
import time
from face_detector import verify_face
from auth import show_lock_screen
from scorer import add_signal, is_fraud, reset_score
from alerter import trigger_alert
from monitor import start_bot_listener

CAMERA_INDEX = 1
alert_sent = False

def monitor_camera():
    
    """Continuously monitor camera for unauthorised faces."""
    global alert_sent
    print("[EscudoAI] Starting camera monitor...")
    cam = cv2.VideoCapture(CAMERA_INDEX)

    while True:
        unauthorised_count = 0
        total_checks = 5

        # Take 5 quick checks over 3 seconds
        for i in range(total_checks):
            ret, frame = cam.read()
            if not ret:
                continue
            is_owner = verify_face(frame)
            if not is_owner:
                unauthorised_count += 1
            time.sleep(0.6)

        # Only trigger if 4 out of 5 checks say unauthorised
        if unauthorised_count >= 4:
            print(f"[EscudoAI] Unauthorised confirmed ({unauthorised_count}/{total_checks} checks failed)!")
            cam.release()
            result = show_lock_screen()

            if result >= 3:
                print("[EscudoAI] 3 wrong attempts - already alerted!")
            else:
                print("[EscudoAI] Access granted via password.")
                reset_score()
                alert_sent = False
            cam = cv2.VideoCapture(CAMERA_INDEX)
        else:
            if unauthorised_count > 0:
                print(f"[EscudoAI] Minor movement detected ({unauthorised_count}/{total_checks}) - ignoring.")
            else:
                print("[EscudoAI] Owner verified. All good.")

        time.sleep(11)
def monitor_behaviour():
    """Monitor suspicious behaviour and trigger alerts."""
    global alert_sent
    print("[EscudoAI] Behaviour monitor started...")

    while True:
        if is_fraud() and not alert_sent:
            print("[EscudoAI] Fraud threshold reached! Alerting owner...")
            trigger_alert()
            alert_sent = True
            asyncio.run(start_bot_listener())
            reset_score()
            alert_sent = False
        time.sleep(3)

if __name__ == "__main__":
    print("""
    ███████╗███████╗ ██████╗██╗   ██╗██████╗  ██████╗      █████╗ ██╗
    ██╔════╝██╔════╝██╔════╝██║   ██║██╔══██╗██╔═══██╗    ██╔══██╗██║
    █████╗  ███████╗██║     ██║   ██║██║  ██║██║   ██║    ███████║██║
    ██╔══╝  ╚════██║██║     ██║   ██║██║  ██║██║   ██║    ██╔══██║██║
    ███████╗███████║╚██████╗╚██████╔╝██████╔╝╚██████╔╝    ██║  ██║██║
    ╚══════╝╚══════╝ ╚═════╝ ╚═════╝ ╚═════╝  ╚═════╝     ╚═╝  ╚═╝╚═╝
    The Shield That Never Sleeps
    """)

    print("[EscudoAI] System starting...")
    print("[EscudoAI] Press Ctrl+C to stop\n")

    # Run both monitors in parallel threads
    cam_thread = threading.Thread(target=monitor_camera, daemon=True)
    beh_thread = threading.Thread(target=monitor_behaviour, daemon=True)

    cam_thread.start()
    beh_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[EscudoAI] System stopped.")

