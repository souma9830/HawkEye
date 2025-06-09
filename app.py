from flask import Flask, request, jsonify, send_from_directory, render_template, redirect, url_for, flash
import os
import json
import time
import threading
from datetime import datetime, timedelta
from detector import HumanMovementDetector, SecuritySystem, runtime_logs
from werkzeug.utils import secure_filename
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
SAVE_DIR = "static/saves"
VIDEO_DIR = "static/videos"
FRAME_PATH = "static/current_frame.jpg"
UPLOAD_EXTENSIONS = ['.mp4', '.avi']
UPLOAD_PATH = os.path.join('static', 'videos')
app.config['UPLOAD_FOLDER'] = UPLOAD_PATH
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max
app.secret_key = 'supersecretkey'  # Needed for flash messages

# Ensure all required directories exist with proper permissions
for directory in [SAVE_DIR, VIDEO_DIR, "static"]:
    try:
        os.makedirs(directory, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create directory {directory}: {e}")

# Ensure the current frame file exists (even if empty)
try:
    if not os.path.exists(FRAME_PATH):
        with open(FRAME_PATH, 'wb') as f:
            f.write(b'')
except Exception as e:
    logger.error(f"Failed to create current frame file: {e}")

detector = None
security_system = SecuritySystem()

def cleanup_old_data():
    """Remove data older than the retention period"""
    retention_days = int(os.getenv("DATA_RETENTION_DAYS", 30))
    cutoff_time = datetime.now() - timedelta(days=retention_days)
    
    cleanup_count = 0
    for filename in os.listdir(SAVE_DIR):
        try:
            if not filename.endswith((".jpg", ".json")):
                continue
                
            file_time_str = filename.split('.')[0]
            file_time = datetime.strptime(file_time_str, "%Y%m%d_%H%M%S")
            
            if file_time < cutoff_time:
                os.remove(os.path.join(SAVE_DIR, filename))
                cleanup_count += 1
        except Exception as e:
            print(f"Error processing file {filename}: {e}")
    
    if cleanup_count > 0:
        runtime_logs.append(f"[CLEANUP] Removed {cleanup_count} expired files")

def start_cleanup_task():
    """Start background task for periodic cleanup"""
    def cleanup_task():
        while True:
            cleanup_old_data()
            time.sleep(86400)
            
    thread = threading.Thread(target=cleanup_task)
    thread.daemon = True
    thread.start()
    runtime_logs.append("[SYSTEM] Started cleanup background task")

@app.route("/")
def home():
    try:
        video_files = [f for f in os.listdir(VIDEO_DIR) if f.endswith((".mp4", ".avi"))]
        running = detector.running if detector else False
        return render_template("index.html", running=running, video_files=video_files)
    except Exception as e:
        logger.error(f"Error in home route: {e}")
        return render_template("error.html", error="Failed to load home page"), 500

@app.route("/current_frame")
def current_frame():
    """Return the current frame being processed"""
    try:
        if not os.path.exists(FRAME_PATH):
            logger.warning("Current frame file not found")
            return jsonify({"error": "No current frame available"}), 404
            
        if os.path.getsize(FRAME_PATH) == 0:
            logger.warning("Current frame file is empty")
            return jsonify({"error": "Frame is empty"}), 404
            
        response = send_from_directory("static", "current_frame.jpg")
        # Add cache control headers to prevent browser caching
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        logger.error(f"Error serving current frame: {e}")
        return jsonify({"error": "Error serving frame"}), 500

@app.route("/start", methods=["POST"])
def start_detection():
    global detector
    data = request.get_json()
    email = data.get("email")
    filename = data.get("filename")
    privacy_blur = data.get("privacy_blur", False)
    zones = data.get("zones", [])

    video_path = os.path.join(VIDEO_DIR, filename)
    if not os.path.isfile(video_path):
        runtime_logs.append(f"[ERROR] File not found: {video_path}")
        return jsonify({"status": "error", "message": "Video file not found."}), 400

    if detector and detector.running:
        detector.stop()

    detector = HumanMovementDetector(video_source=video_path)
    
    if zones:
        detector.set_monitoring_zones(zones)
        
    detector.start(email=email, privacy_blur=privacy_blur)
    return jsonify({"status": "started", "email": email})

@app.route("/stop", methods=["POST"])
def stop_detection():
    global detector
    if detector:
        detector.stop()
    return jsonify({"status": "stopped"})

@app.route("/reset", methods=["POST"])
def reset_logs():
    try:
        for f in os.listdir(SAVE_DIR):
            try:
                os.remove(os.path.join(SAVE_DIR, f))
            except Exception as e:
                logger.error(f"Error removing file {f}: {e}")
                continue
                
        if os.path.exists(FRAME_PATH):
            try:
                os.remove(FRAME_PATH)
            except Exception as e:
                logger.error(f"Error removing current frame: {e}")
                
        runtime_logs.append("[RESET] Logs and screenshots cleared.")
        return jsonify({"status": "reset"})
    except Exception as e:
        logger.error(f"Error resetting logs: {e}")
        return jsonify({"error": "Failed to reset logs"}), 500

@app.route("/save-zones", methods=["POST"])
def save_zones():
    global detector
    data = request.get_json()
    zones = data.get("zones", [])
    
    if detector:
        detector.set_monitoring_zones(zones)
    
    return jsonify({"status": "success", "zones": zones})

@app.route("/status", methods=["GET"])
def status():
    try:
        running = detector.running if detector else False
        return jsonify({"running": running})
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({"error": "Failed to get status"}), 500

@app.route("/logs")
def list_logs():
    try:
        logs = []
        for filename in os.listdir(SAVE_DIR):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(SAVE_DIR, filename), "r") as f:
                        data = json.load(f)
                        logs.append(data)
                except Exception as e:
                    logger.error(f"Error reading log file {filename}: {e}")
                    continue
        return jsonify(sorted(logs, key=lambda x: x["timestamp"], reverse=True))
    except Exception as e:
        logger.error(f"Error listing logs: {e}")
        return jsonify({"error": "Failed to list logs"}), 500

@app.route("/logs/action-required")
def logs_action_required():
    try:
        flagged = []
        for filename in os.listdir(SAVE_DIR):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(SAVE_DIR, filename), "r") as f:
                        data = json.load(f)
                        if data.get("analysis", {}).get("action_required"):
                            flagged.append(data)
                except Exception as e:
                    logger.error(f"Error reading log file {filename}: {e}")
                    continue
        return jsonify(sorted(flagged, key=lambda x: x["timestamp"], reverse=True))
    except Exception as e:
        logger.error(f"Error getting action required logs: {e}")
        return jsonify({"error": "Failed to get action required logs"}), 500

@app.route("/logs/live")
def live_logs():
    try:
        return jsonify(runtime_logs[-100:])
    except Exception as e:
        logger.error(f"Error getting live logs: {e}")
        return jsonify({"error": "Failed to get live logs"}), 500

@app.route("/analytics")
def analytics():
    logs = []
    try:
        for filename in os.listdir("static/saves"):
            if filename.endswith(".json"):
                with open(os.path.join("static/saves", filename), "r") as f:
                    log_data = json.load(f)
                    logs.append(log_data)
    except Exception as e:
        print(f"Error loading logs: {e}")

    logs = sorted(logs, key=lambda x: x["timestamp"], reverse=True)
    
    total_alerts = len(logs)
    danger_levels = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    hourly_breakdown = {}
    weapons_detected = {}
    response_actions = {}
    objects_detected = {}
    
    for log in logs:
        analysis = log.get("analysis", {})
        
        danger = analysis.get("danger", "LOW")
        danger_levels[danger] = danger_levels.get(danger, 0) + 1
        
        hour = log["timestamp"][:9]
        hourly_breakdown[hour] = hourly_breakdown.get(hour, 0) + 1
        
        for weapon in analysis.get("weapons", []):
            weapons_detected[weapon] = weapons_detected.get(weapon, 0) + 1
        
        for profile in analysis.get("profiles", []):
            desc = profile.get("description", "Unknown person")
            parts = desc.split(',')
            if parts:
                key = parts[0].strip()
                objects_detected[key] = objects_detected.get(key, 0) + 1
                
        if analysis.get("recommended_response"):
            response = analysis["recommended_response"].split(".")[0] + "."
            response_actions[response] = response_actions.get(response, 0) + 1
    
    detailed_incidents = logs[:20]
    
    return render_template(
        "analytics.html",
        total_alerts=total_alerts,
        danger_levels=danger_levels,
        hourly_breakdown=hourly_breakdown,
        weapons_detected=weapons_detected,
        objects_detected=objects_detected,
        action_summary=response_actions,
        detailed_incidents=detailed_incidents
    )

@app.route("/images/<filename>")
def get_image(filename):
    return send_from_directory(SAVE_DIR, filename)

@app.route("/system/add-camera", methods=["POST"])
def add_camera():
    data = request.get_json()
    camera_id = data.get("camera_id")
    source = data.get("source")
    
    if not camera_id or not source:
        return jsonify({"status": "error", "message": "Missing camera ID or source"}), 400
        
    security_system.add_camera(camera_id, source)
    return jsonify({"status": "success", "camera_id": camera_id})

@app.route("/system/start-all", methods=["POST"])
def start_all_cameras():
    data = request.get_json()
    email = data.get("email")
    security_system.start_monitoring(email=email)
    return jsonify({"status": "success"})

@app.route("/system/stop-all", methods=["POST"])
def stop_all_cameras():
    security_system.stop_monitoring()
    return jsonify({"status": "success"})

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        flash('No file part')
        return redirect(url_for('home'))
    file = request.files['video']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('home'))
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in UPLOAD_EXTENSIONS:
        flash('Invalid file type. Only .mp4 and .avi allowed.')
        return redirect(url_for('home'))
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    flash('Video uploaded successfully!')
    return redirect(url_for('home'))

@app.before_request
def before_request_func():
    global cleanup_task_started
    if not getattr(app, 'cleanup_task_started', False):
        app.cleanup_task_started = True
        start_cleanup_task()

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)