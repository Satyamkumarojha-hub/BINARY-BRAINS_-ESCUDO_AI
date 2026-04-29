# **EscudoAI - AI That Never Sleeps**

An intelligent cybersecurity system that protects your laptop from unauthorized access, insider threats, and physical attacks using AI, Computer Vision, and real-time monitoring.

## **Problem Statement :-**

Traditional laptop security relies only on passwords, which fail when:  

Someone knows or guesses your password  
An insider accesses sensitive files  
Physical attacks like USB data theft or HDMI spying occur  

This project solves that by adding multi-layer AI-based protection.

## **Key Features :-**

**1.Face Recognition Authentication**

Detects whether the current user is the real owner  
Works alongside password (not replaces it)  
Reduces false rejection with optimized threshold   

**2.Smart Password Security**

Allows login but tracks suspicious behavior  
On 3 wrong attempts:  
Captures intruder photo + screen  
Sends real-time alert  
Locks system  

**3. File Access Monitoring**

Tracks sensitive folders:  
Documents, Desktop, Downloads, Pictures, Videos, OneDrive  
On access:  
Sends instant Telegram alert  
Includes:  
Screenshot  
File name  
ALLOW / DENY control  

**4.Cable / Hardware Attack Detection**

Detects:  
USB devices (pen drives, storage devices)  
HDMI connections (external displays)  
Assigns risk scores:  
USB → +25 (data theft risk)  
HDMI → +30 (screen spying risk)  
Unknown cable → +35  
Sends instant alert with device name  

**5.ML-Based Fraud Detection Engine**

Combines multiple signals:  
Face mismatch  
File access  
Cable insertion  
Suspicious behavior  
If fraud score ≥ 60:  
Sends detailed alert  
Owner decides ALLOW / DENY  

**6.Real-Time Telegram Alerts**

Alerts include:  
Screenshot  
Intruder photo (if applicable)  
File / Device details  
Risk explanation    
Interactive controls:  
ALLOW  
DENY (locks system instantly)  

## **System Workflow :-**

System starts → Camera begins monitoring  
Face Recognition runs  
Password authentication  
On success → Monitoring starts:  
File activity  
Cable detection  
Behavior signals  
Signals → ML Fraud Scoring  
Alerts sent in real-time  
Owner controls system remotely  

## **Tech Stack:-**

Python  
OpenCV (Face Detection & Camera)  
Machine Learning (Custom Scoring System)  
System Monitoring  
OS-level file tracking  
PowerShell (for hardware detection on Windows)   
Communication  
Telegram Bot API (alerts & control system)  
Concurrency  
Multi-threading (real-time monitoring)  

## **Project Structure:-**

├── main.py              # Main execution & threads  
├── auth.py              # Login & authentication logic  
├── signal_detector.py   # Detects suspicious activities  
├── scorer.py            # ML fraud scoring engine  
├── alerter.py           # Telegram alerts system  
├── config.py            # Signal weights & configs  
 
## **Real-World Use Cases:-**

Prevent data theft via USB drives  
Detect insider threats (friends/roommates/colleagues)  
Stop unauthorized file access  
Protect against screen spying via HDMI   
Useful for:  
Students  
Developers  
Corporate employees  

## **Future Improvements:-**

Mobile app instead of Telegram  
Face re-authentication during the session  
Auto-lock on high-risk actions  
Cloud-based monitoring dashboard  
Behavioral biometrics (typing pattern, mouse usage)  

## **Disclaimer:-**

This project is for educational and research purposes.
Some system-level monitoring may require administrator permissions depending on the OS.

## **Author:-**

Developed by :  
  Satyam Ojha  
  Parth Sharma  
  Krish Kumar  
