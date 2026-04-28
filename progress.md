# EscudoAI - Progress Report

## Project Overview
EscudoAI is an ML-powered laptop security system that uses facial recognition,
behavioural anomaly detection, and real-time owner alerts to stop unauthorised
access before it becomes a threat.

> "You left your laptop open. Someone sat down. EscudoAI already knows."

---

## Tasks Completed

### 1. Environment Setup
- [x] Python 3.10 virtual environment created
- [x] All core libraries installed (OpenCV, DeepFace, FastAPI, Telegram, Watchdog)
- [x] Project folder structure created

### 2. Face Detection Module (face_detector.py)
- [x] Owner face enrollment via webcam
- [x] Face saved to faces/owner.jpg
- [x] Face verification function using DeepFace
- [x] Camera index auto-detection

### 3. Configuration (config.py)
- [x] Telegram bot token and chat ID configured
- [x] ML fraud score threshold set (60 points)
- [x] Signal weights defined
- [x] Private paths configured

### 4. Authentication Module (auth.py)
- [x] Fullscreen lock screen UI built with Tkinter
- [x] Password attempt counter (max 3 attempts)
- [x] Telegram alert on 3 wrong password attempts
- [x] Screenshot captured on failed attempts
- [x] Correct password unlocks the screen

### 5. ML Scoring Engine (scorer.py)
- [x] Weighted signal scoring system
- [x] Fraud threshold detection (score >= 60)
- [x] Session logging to logs/session_log.txt
- [x] Full session report generation
- [x] Score reset functionality

### 6. Alerter Module (alerter.py)
- [x] Real-time screenshot capture
- [x] Telegram fraud alert with screenshot
- [x] Fraud score and verdict in alert message
- [x] ALLOW and DENY and LOCK inline buttons
- [x] Suspicious activity list with timestamps

---

## ML Signal Weights

| Signal | Points |
|--------|--------|
| Private file accessed | +50 pts |
| Camera blocked | +30 pts |
| USB/cable inserted | +25 pts |
| Phone photo detected | +20 pts |
| Unusual app behaviour | +15 pts |

Fraud Threshold: 60 points

---

## Current Progress
- Core security pipeline: 80% complete
- Face detection: Working
- Lock screen: Working
- ML Scorer: Working
- Telegram alerts with buttons: Working
- Monitor module: In Progress
- Main entry point: Pending
- Full system integration: Pending

---

## Project Structure
EscudoAI/
- faces/ - Enrolled owner face
- screenshots/ - Fraud screenshots
- logs/ - Session logs
- config.py - Configuration
- face_detector.py - Face recognition
- auth.py - Lock screen and auth
- scorer.py - ML scoring engine
- alerter.py - Telegram alerts
- monitor.py - Behaviour monitor
- main.py - Entry point
- progress.md - This file

---

## Next Steps
- Complete monitor.py (Allow/Deny button handler)
- Implement hard lock on Deny
- Write main.py to tie all modules together
- Add USB insertion detection
- Add file system watcher for private files
- Add camera block detection
- Full end-to-end system test
- Final demo preparation

---

## Team
- Hackathon: 24-Hour Build
- Project: EscudoAI
- Stack: Python, OpenCV, DeepFace, Telegram Bot API, Tkinter, FastAPI

Built at the hackathon - April 2026
