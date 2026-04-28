# face_detector.py — EscudoAI

import cv2
import os
import numpy as np
from deepface import DeepFace

FACES_DIR = "faces"

def enroll_user():
    """Capture and save the authorised user's face."""
    cam = cv2.VideoCapture(1)
    print("[EscudoAI] Look at the camera. Press SPACE to capture your face.")
    while True:
        ret, frame = cam.read()
        cv2.imshow("Enroll Face - Press SPACE", frame)
        key = cv2.waitKey(1)
        if key == 32:  # SPACE
            path = os.path.join(FACES_DIR, "owner.jpg")
            cv2.imwrite(path, frame)
            print(f"[EscudoAI] Face enrolled and saved to {path}")
            break
    cam.release()
    cv2.destroyAllWindows()

def verify_face(frame):
    """Returns True if face in frame matches owner."""
    owner_path = os.path.join(FACES_DIR, "owner.jpg")
    if not os.path.exists(owner_path):
        print("[EscudoAI] No enrolled face found. Run enroll first.")
        return False
    try:
        temp_path = os.path.join(FACES_DIR, "temp.jpg")
        cv2.imwrite(temp_path, frame)
        result = DeepFace.verify(
            img1_path=owner_path,
            img2_path=temp_path,
            enforce_detection=False
        )
        return result["verified"]
    except Exception as e:
        print(f"[EscudoAI] Face verify error: {e}")
        return False

if __name__ == "__main__":
    enroll_user()