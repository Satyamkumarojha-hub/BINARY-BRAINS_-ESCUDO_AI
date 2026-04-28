# face_detector.py — EscudoAI

import cv2
import os
import time
import numpy as np
from deepface import DeepFace

FACES_DIR  = "faces"
TEMP_PATH  = os.path.join(FACES_DIR, "temp.jpg")

# ─────────────────────────────────────────────────────────────
# Tuning knobs — adjust here only
# ─────────────────────────────────────────────────────────────
MODEL           = "Facenet512"   # much more accurate than VGG-Face
METRIC          = "cosine"
THRESHOLD       = 0.55           # Facenet512+cosine sweet spot (0.40 was VGG-Face only)
ENROLL_SAMPLES  = 5              # capture N frames and save the best one
VERIFY_VOTES    = 3              # cast N votes per verify() call; majority wins
# ─────────────────────────────────────────────────────────────


def _has_face(frame) -> bool:
    """Return True if at least one face is detectable in the frame."""
    try:
        faces = DeepFace.extract_faces(
            img_path=frame,
            enforce_detection=True,
            detector_backend="opencv",
        )
        return len(faces) > 0
    except Exception:
        return False


def _compare(owner_path: str, probe_path: str) -> tuple[bool, float]:
    """
    Run DeepFace.verify and return (verified, distance).
    Returns (False, 1.0) on any error.
    """
    try:
        result = DeepFace.verify(
            img1_path=owner_path,
            img2_path=probe_path,
            enforce_detection=True,
            model_name=MODEL,
            distance_metric=METRIC,
            threshold=THRESHOLD,
        )
        return result["verified"], round(result["distance"], 4)
    except Exception as e:
        print(f"[EscudoAI] Verify error: {e}")
        return False, 1.0


# ─────────────────────────────────────────────────────────────
# Enroll
# ─────────────────────────────────────────────────────────────

def enroll_user():
    """Capture multiple frames and save the clearest one as owner.jpg."""
    cam = cv2.VideoCapture(1)
    os.makedirs(FACES_DIR, exist_ok=True)
    print(f"[EscudoAI] Enrolling owner — will capture {ENROLL_SAMPLES} samples.")
    print("[EscudoAI] Look straight at the camera. Press SPACE to start capture.")

    # Wait for SPACE
    while True:
        ret, frame = cam.read()
        if not ret:
            continue
        cv2.putText(frame, "Look straight — press SPACE to enroll",
                    (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow("EscudoAI Enroll", frame)
        if cv2.waitKey(1) == 32:
            break

    # Capture ENROLL_SAMPLES frames and pick the one where DeepFace
    # extracts a face with the highest confidence score
    best_frame  = None
    best_conf   = -1.0

    print(f"[EscudoAI] Capturing {ENROLL_SAMPLES} samples…")
    collected = 0
    while collected < ENROLL_SAMPLES:
        ret, frame = cam.read()
        if not ret:
            continue

        cv2.putText(frame, f"Capturing {collected+1}/{ENROLL_SAMPLES}…",
                    (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.imshow("EscudoAI Enroll", frame)
        cv2.waitKey(1)

        try:
            faces = DeepFace.extract_faces(
                img_path=frame,
                enforce_detection=True,
                detector_backend="opencv",
            )
            if faces:
                conf = faces[0].get("confidence", 0.0)
                if conf > best_conf:
                    best_conf  = conf
                    best_frame = frame.copy()
                collected += 1
                time.sleep(0.3)
        except Exception:
            pass   # no face in this frame — skip

    cam.release()
    cv2.destroyAllWindows()

    if best_frame is not None:
        path = os.path.join(FACES_DIR, "owner.jpg")
        cv2.imwrite(path, best_frame)
        print(f"[EscudoAI] ✅ Owner enrolled → {path}  (confidence: {best_conf:.3f})")
    else:
        print("[EscudoAI] ❌ Enrollment failed — no clear face detected. Try again.")


# ─────────────────────────────────────────────────────────────
# Verify  (called every 10 s by monitor_camera)
# ─────────────────────────────────────────────────────────────

def verify_face(frame) -> bool:
    """
    Returns True ONLY if the face in `frame` matches the enrolled owner.

    Uses majority-vote across VERIFY_VOTES comparisons to handle
    occasional bad frames / lighting changes.
    """
    owner_path = os.path.join(FACES_DIR, "owner.jpg")

    if not os.path.exists(owner_path):
        print("[EscudoAI] ⚠️  No enrolled face — run enroll first.")
        return False

    # ── Step 1: quick face presence check ────────────────────
    if not _has_face(frame):
        print("[EscudoAI] No face in frame — treating as unauthorized.")
        return False

    # ── Step 2: majority-vote verification ───────────────────
    os.makedirs(FACES_DIR, exist_ok=True)
    cv2.imwrite(TEMP_PATH, frame)

    votes_yes = 0
    votes_no  = 0
    distances = []

    for vote in range(VERIFY_VOTES):
        verified, dist = _compare(owner_path, TEMP_PATH)
        distances.append(dist)
        if verified:
            votes_yes += 1
        else:
            votes_no  += 1

    avg_dist = round(sum(distances) / len(distances), 4)
    is_owner = votes_yes > votes_no   # simple majority

    if is_owner:
        print(f"[EscudoAI] ✅ Owner matched  "
              f"(votes {votes_yes}/{VERIFY_VOTES}, avg dist: {avg_dist})")
    else:
        print(f"[EscudoAI] ❌ Not recognised "
              f"(votes {votes_yes}/{VERIFY_VOTES}, avg dist: {avg_dist} > {THRESHOLD})")

    return is_owner


if __name__ == "__main__":
    enroll_user()
