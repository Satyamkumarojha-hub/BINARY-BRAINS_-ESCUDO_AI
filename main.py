# main.py - EscudoAI

import cv2
import asyncio
import threading
import time
from face_detector import verify_face
from auth import show_lock_screen
from scorer import add_signal, is_fraud, reset_score, get_score
from alerter import trigger_alert
from monitor import start_bot_listener
from signal_detector import check_all_signals, start_file_monitor, detect_phone_in_frame
last_alert_time = 0
ALERT_COOLDOWN = 15  # seconds
CAMERA_INDEX = 1
alert_sent = False
unauthorized_user_active = False
phone_alert_sent = False

def monitor_camera():
    """Continuously monitor camera for unauthorised faces."""
    global alert_sent, unauthorized_user_active
    print("[EscudoAI] Starting camera monitor...")
    cam = cv2.VideoCapture(CAMERA_INDEX)

    while True:
        # If unauthorized user is already working, skip face checking
        if unauthorized_user_active:
            print("[EscudoAI] Unauthorized user active - monitoring fraud only")
            time.sleep(10)
            continue
        
        # ONLY check face if no unauthorized user is active
        if not unauthorized_user_active:
            unauthorised_count = 0
            total_checks = 5

            for i in range(total_checks):
                ret, frame = cam.read()
                if not ret:
                    continue

                is_owner = verify_face(frame)
                if not is_owner:
                    unauthorised_count += 1
                time.sleep(0.6)

            if unauthorised_count >= 4:
                print(f"[EscudoAI] Unauthorised detected ({unauthorised_count}/{total_checks})!")
                cam.release()
                result = show_lock_screen()

                if result >= 3:
                    print("[EscudoAI] 3 wrong attempts - Owner alerted!")
                else:
                    print("[EscudoAI] Password correct - Access granted")
                    unauthorized_user_active = True
                    reset_score()
                    alert_sent = False
                cam = cv2.VideoCapture(CAMERA_INDEX)
            else:
                if unauthorised_count > 0:
                    print(f"[EscudoAI] Minor movement ({unauthorised_count}/{total_checks}) - ignoring.")
                else:
                    print("[EscudoAI] Owner verified. System secure.")

        time.sleep(8)

def monitor_behaviour():
   
    global alert_sent, last_alert_time
    print("[EscudoAI] Behaviour monitor started...")

    while True:
        if is_fraud():
            current_time = time.time()

            # Prevent multiple alerts in short time
            if current_time - last_alert_time > ALERT_COOLDOWN:
                print("[EscudoAI] Fraud threshold reached! Sending consolidated alert...")

                trigger_alert()
                last_alert_time = current_time
                alert_sent = True

                asyncio.run(start_bot_listener())

                reset_score()
                alert_sent = False
            else:
                print("[EscudoAI] Fraud detected but waiting (cooldown active)...")

        time.sleep(2)

def monitor_phone_recording():
    """Monitor for phone recording attempts - IMMEDIATE ALERT."""
    global phone_alert_sent, unauthorized_user_active
    print("[EscudoAI] Phone recording monitor started...")
    cam = cv2.VideoCapture(CAMERA_INDEX)
    
    while True:
        # Only monitor for phone if unauthorized user is active
        if unauthorized_user_active and not phone_alert_sent:
            ret, frame = cam.read()
            if ret:
                if detect_phone_in_frame(frame):
                    print("\n[EscudoAI] PHONE RECORDING ATTEMPT DETECTED!")
                    add_signal("phone_recording")
                    
                    # IMMEDIATE ALERT - Don't wait for threshold
                    print("[EscudoAI] Sending IMMEDIATE alert for phone recording...")
                    from alerter import send_phone_recording_alert
                    send_phone_recording_alert()
                    
                    phone_alert_sent = True
                    
                    # Listen for response
                    asyncio.run(start_bot_listener())
                    
                    # Reset
                    phone_alert_sent = False
                    unauthorized_user_active = False
        
        time.sleep(1)

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

    # Run monitors in parallel
    cam_thread = threading.Thread(target=monitor_camera, daemon=True)
    beh_thread = threading.Thread(target=monitor_behaviour, daemon=True)
    phone_thread = threading.Thread(target=monitor_phone_recording, daemon=True)

    cam_thread.start()
    beh_thread.start()
    phone_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[EscudoAI] System stopped.")
