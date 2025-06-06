# 🦅 HawkEye

**HawkEye** is a real-time threat monitoring system that detects dangerous human activity from CCTV footage. Built with Flask, YOLOv8, and OpenAI's GPT-4 Vision, it automatically analyzes human movement in video files and sends email alerts when suspicious behavior is detected.

---

## 📌 About the Project

HawkEye focuses primarily on **backend technology** — combining real-time object detection, contextual AI analysis, and intelligent alerting — to build a meaningful safety solution. While a basic frontend dashboard is included for demonstration purposes, the **core innovation lies in the detection and analysis pipeline**.

---

## 💡 Key Features

* 📂 Uses **YOLOv8** to detect humans and movements in CCTV-like footage
* 🤖 Uses **GPT-4 Vision** to analyze screenshots for dangerous behavior
* ✉️ Sends detailed email alerts with images and structured threat logs
* 🔒 Supports **privacy masking** and **multi-level threat detection**
* 🧍‍♂️ **Tracks people** across multiple frames for consistency
* 📈 Provides **advanced analytics** and visual logs
* 📢 Supports **external alarm system triggers**
* 📁 Stores logs and reports for post-event investigation
* ⚙️ Backend-driven — minimal dependencies and frontend bloat

---

## 📽 Intended Use

HawkEye is designed to run locally on systems such as:

* Schools
* Retail environments
* Residential security systems

It currently processes local video files and requires internet for AI-based analysis, but future versions will support **offline AI models** for complete local operation.

---

## 🧪 How It Works

1. Select a video file (placed in `/static/videos/`)
2. Optionally enable email alerts
3. Click **Start Monitoring**
4. The system:
   * Detects human movement and extracts frames
   * Applies AI for scene interpretation and threat assessment
   * Sends email alerts for threats (if enabled)
   * Logs activity with timestamps, labels, and screenshots

Logs are accessible at:
* `/logs`: General activity logs
* `/logs/action-required`: Only critical or high-risk events

---

## 🧰 Technical Overview

* **Backend**: Python (Flask)
* **Frontend**: HTML/CSS/JavaScript (lightweight dashboard)
* **Detection**: Computer vision with YOLOv8
* **AI Analysis**: GPT-4 Vision via OpenAI API
* **Tracking**: Person ID consistency across frames
* **Data Handling**: Structured logs and visual evidence
* **Connectivity**: External alarm integration (planned)

---

## 🚧 Future Improvements

* Optimize detector for more efficient frame sampling
* Reduce false positives with custom ML models
* Integrate **real-time CCTV stream monitoring**
* Build **mobile app** for remote alerts and control
* Implement **user accounts** and **role-based access control**
* Support **fully offline AI models** for private deployments

---

## 🧱 Project Structure

```
HawkEye/
├── app.py              # Flask routes and control logic
├── detector.py         # Movement + frame capture + alert trigger
├── processor.py        # OpenAI GPT-4 Vision analysis
├── emailer.py          # Email alert system
├── templates/
│   ├── index.html      # Demo UI for hackathon
│   └── analytics.html  # Threat analytics dashboard
├── static/
│   ├── saves/          # Captured screenshots + logs
│   ├── videos/         # Uploaded video files
│   ├── style.css       # Custom CSS styles
│   └── script.js       # JavaScript for UI interactions
├── .env                # Environment variables
```

---

## 🛠 Setup Instructions

### 1. Clone and set up virtualenv

```bash
git clone https://github.com/yourusername/HawkEye.git
cd HawkEye
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create `.env` file

```env
OPENAI_API_KEY=your-openai-api-key
OPENAI_BASE_URL=your-openai-base-url  # Optional
OPENAI_MODEL=gpt-4-vision-preview     # Optional, defaults to gpt-4o
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 4. Run the app

```bash
python app.py
```

Then open:  
`http://localhost:8080`

---

## 📃 License

Apache License 2.0

---

## 👏 Credits

- YOLOv8 by [Ultralytics](https://github.com/ultralytics/ultralytics)
- GPT-4 Vision by [OpenAI](https://openai.com/) 