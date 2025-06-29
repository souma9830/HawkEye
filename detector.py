import cv2
import time
import threading
import math
import os
import json
import requests
from datetime import datetime, timedelta
import numpy as np
from ultralytics import YOLO
from processor import process_screenshot
from emailer import send_alert_email
from call_service import CallService

runtime_logs = []

def log(msg):
    print(msg)
    runtime_logs.append(msg)

def trigger_alarm_system(threat_level, location, image_path=None):
    """Interface with external alarm systems via API"""
    log(f"[ALARM] Triggering alarm system for {threat_level} threat at {location}")
    
    if threat_level in ["MEDIUM", "HIGH", "CRITICAL"]:
        try:
            # Initialize call service
            log("[ALARM] Initializing call service...")
            call_service = CallService()
            
            # Get threat summary and analysis if available
            summary = None
            analysis_data = None
            if image_path:
                log(f"[ALARM] Processing image for analysis: {image_path}")
                analysis = process_screenshot(image_path)
                summary = analysis.get('summary', 'No additional details available')
                analysis_data = analysis  # Pass the complete analysis data
                log(f"[ALARM] Analysis completed. Summary: {summary[:100]}...")
            
            # Make alert call with AI guidance
            log("[ALARM] Making alert call...")
            call_result = call_service.make_alert_call(threat_level, location, summary, analysis_data)
            
            if call_result:
                log("[ALARM] ✓ Alert call initiated successfully")
            else:
                log("[ALARM] ✗ Failed to initiate alert call")
            
            # Continue with existing alarm system
            alarm_url = os.getenv('ALARM_SYSTEM_URL')
            alarm_api_key = os.getenv('ALARM_API_KEY')
            
            if alarm_url and alarm_api_key:
                payload = {
                    "level": threat_level,
                    "location": location,
                    "timestamp": datetime.now().isoformat()
                }
                
                requests.post(
                    f"{alarm_url}/api/alarm",
                    json=payload,
                    headers={"Authorization": f"Bearer {alarm_api_key}"}
                )
                log(f"[EXTERNAL ALARM] Triggered for {threat_level} threat")
            else:
                log("[CONFIG] External alarm system not configured")
        except Exception as e:
            log(f"[ERROR] Failed to trigger alarm: {e}")
    else:
        log(f"[ALARM] Threat level {threat_level} not high enough for alarm trigger")

class PersonTracker:
    def __init__(self):
        self.tracks = {}
        self.next_id = 0
        self.max_distance = 50
        
    def update(self, boxes, frame):
        current_ids = []
        
        for box in boxes:
            matched = False
            for track_id, track in list(self.tracks.items()):
                distance = self.euclidean_distance(box, track["last_position"])
                if distance < self.max_distance:
                    self.tracks[track_id]["last_position"] = box
                    self.tracks[track_id]["frames_visible"] += 1
                    
                    self.tracks[track_id]["path"].append(box)
                    
                    current_ids.append(track_id)
                    matched = True
                    break
            
            if not matched:
                self.tracks[self.next_id] = {
                    "first_seen": time.time(),
                    "last_position": box,
                    "frames_visible": 1,
                    "path": [box],
                }
                current_ids.append(self.next_id)
                self.next_id += 1
                
        for track_id in list(self.tracks.keys()):
            if track_id not in current_ids:
                self.tracks[track_id]["frames_missing"] = self.tracks[track_id].get("frames_missing", 0) + 1
                
                if self.tracks[track_id]["frames_missing"] > 30:
                    del self.tracks[track_id]
                    
        return self.tracks
    
    def euclidean_distance(self, a, b):
        return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)
    
    def get_persistent_tracks(self):
        """Return tracks that have been visible for a significant time"""
        return {k: v for k, v in self.tracks.items() if v["frames_visible"] > 15}

class HumanMovementDetector:
    def __init__(self, video_source):
        self.video_source = video_source
        self.model = YOLO("yolov8n.pt")
        self.running = False
        self.thread = None
        self.prev_boxes = []
        self.cooldown = 5
        self.last_trigger_video_time = -float('inf')
        self.user_email = None
        self.output_dir = "static/saves"
        os.makedirs(self.output_dir, exist_ok=True)
        self.person_tracker = PersonTracker()
        self.monitoring_zones = []
        self.recent_activity = False
        self.potential_threats = [] 
        self.confirmation_threshold = 2
        self.privacy_blur = False
        self.current_frame = None

    def euclidean_distance(self, a, b):
        return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)

    def extract_person_boxes(self, results):
        boxes = []
        for r in results:
            for box in r.boxes:
                if int(box.cls[0]) == 0:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    cx = (x1 + x2) / 2
                    cy = (y1 + y2) / 2
                    boxes.append((cx, cy))
        return boxes

    def extract_full_boxes(self, results):
        boxes = []
        for r in results:
            for box in r.boxes:
                if int(box.cls[0]) == 0:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    boxes.append((x1, y1, x2, y2))
        return boxes

    def has_movement(self, prev_boxes, curr_boxes, threshold=40):
        if not prev_boxes or not curr_boxes:
            return False
        for cb in curr_boxes:
            closest = min((self.euclidean_distance(cb, pb) for pb in prev_boxes), default=1e9)
            if closest > threshold:
                return True
        return False

    def set_monitoring_zones(self, zones):
        """
        Set specific monitoring zones where movement is concerning
        zones: list of dictionaries with x, y, width, height coordinates
        """
        self.monitoring_zones = zones
        log(f"[CONFIG] Set {len(zones)} monitoring zones")
        
    def is_in_monitoring_zone(self, person_box):
        if not self.monitoring_zones:
            return True
            
        x, y = person_box
        for zone in self.monitoring_zones:
            if (zone['x'] <= x <= zone['x'] + zone['width'] and 
                zone['y'] <= y <= zone['y'] + zone['height']):
                return True
        return False

    def apply_privacy_mask(self, frame, alert_boxes):
        """Blur everything except areas with detected threats"""
        if not self.privacy_blur:
            return frame

        blurred = cv2.GaussianBlur(frame, (45, 45), 0)
        
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        
        for x1, y1, x2, y2 in alert_boxes:
            cv2.rectangle(mask, (int(x1), int(y1)), (int(x2), int(y2)), 255, -1)
        
        kernel = np.ones((20, 20), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=1)
        
        mask_inv = cv2.bitwise_not(mask)
        
        fg = cv2.bitwise_and(frame, frame, mask=mask)
        bg = cv2.bitwise_and(blurred, blurred, mask=mask_inv)
        
        result = cv2.add(fg, bg)
        
        return result

    def _handle_confirmed_threat(self, threat_data):
        """Process a confirmed threat after multiple detections"""
        log(f"[CONFIRMED THREAT] Starting threat processing...")
        
        analysis = threat_data["analysis"]
        image_path = threat_data["image_path"]
        threat_level = analysis.get("danger", "LOW")
        
        # Determine location based on video source
        if isinstance(self.video_source, int):
            location = f"Live Camera {self.video_source}"
        else:
            location = os.path.basename(self.video_source)
        
        log(f"[CONFIRMED THREAT] {threat_level} threat at {location}")
        log(f"[CONFIRMED THREAT] Image path: {image_path}")
        log(f"[CONFIRMED THREAT] Analysis: {analysis}")
        
        # Trigger alarm system (calls and external alarms)
        log(f"[CONFIRMED THREAT] Triggering alarm system...")
        trigger_alarm_system(threat_level, location, image_path)
        
        # Send email alert
        if self.user_email:
            log(f"[CONFIRMED THREAT] Sending email alert to {self.user_email}")
            subject = f"🔴 HawkEye Alert – {threat_level} Threat"
            body = (
                f"Timestamp: {analysis['timestamp']}\n\n"
                f"Danger: {threat_level}\n\n"
                f"Summary: {analysis.get('summary', 'No summary available')}\n\n"
                f"Recommended Action: {analysis.get('recommended_response', 'Investigate')}\n\n"
                "See attached image and log file for more information."
            )
            send_alert_email(
                recipient=self.user_email,
                subject=subject,
                body=body,
                attachments=[image_path]
            )
            log(f"[CONFIRMED THREAT] Email alert sent successfully")
        else:
            log(f"[CONFIRMED THREAT] No email configured, skipping email alert")
        
        log(f"[CONFIRMED THREAT] Threat processing completed")

    def _detect_loop(self):
        cap = cv2.VideoCapture(self.video_source)
        log(f"[STARTED] Monitoring source: {self.video_source}")
        
        current_frame_path = "static/current_frame.jpg"
        
        while self.running and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                log("[VIDEO END] Stopping monitoring as video has ended.")
                self.running = False
                break

            self.current_frame = frame.copy()
            
            current_video_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
            if current_video_time - self.last_trigger_video_time < self.cooldown:
                continue

            results = self.model(frame)
            curr_boxes = self.extract_person_boxes(results)
            full_boxes = self.extract_full_boxes(results)
            
            self.person_tracker.update(curr_boxes, frame)
            
            try:
                # Ensure the frame is properly formatted before saving
                frame_to_save = self.apply_privacy_mask(frame, full_boxes)
                if frame_to_save is not None and frame_to_save.size > 0:
                    cv2.imwrite(current_frame_path, frame_to_save)
                else:
                    log("[WARNING] Invalid frame format, skipping save")
            except Exception as e:
                log(f"[ERROR] Failed to save current frame: {e}")

            movement_detected = False
            for box in curr_boxes:
                if self.is_in_monitoring_zone(box) and self.has_movement(self.prev_boxes, [box]):
                    movement_detected = True
                    break
                    
            if movement_detected:
                self.recent_activity = True
                timestamp_str = datetime.fromtimestamp(time.time()).strftime("%Y%m%d_%H%M%S")
                image_filename = f"{timestamp_str}.jpg"
                image_path = os.path.join(self.output_dir, image_filename)
                
                try:
                    # Save the frame
                    cv2.imwrite(image_path, frame)
                    if not os.path.exists(image_path):
                        raise FileNotFoundError(f"Failed to save image to {image_path}")
                    
                    # Process the image
                    try:
                        analysis = process_screenshot(image_path)
                        if analysis.get("status") == "error":
                            error_msg = analysis.get("error", "Unknown error")
                            log(f"[ERROR] Image analysis failed: {error_msg}")
                            log(f"[LOGGED] {image_filename} | Action: False | Danger: {error_msg}")
                        else:
                            log(f"[LOGGED] {image_filename} | Action: {analysis.get('action_required')} | Danger: {analysis.get('danger')}")
                    except Exception as e:
                        log(f"[ERROR] Failed to process image: {str(e)}")
                        log(f"[LOGGED] {image_filename} | Action: False | Danger: Failed to process image")
                        analysis = {
                            "status": "error",
                            "error": str(e),
                            "action_required": False,
                            "danger": "Failed to process image"
                        }
                    
                    # Save the log
                    log_filename = f"{timestamp_str}.json"
                    log_path = os.path.join(self.output_dir, log_filename)
                    with open(log_path, 'w') as log_file:
                        log_data = {
                            "timestamp": timestamp_str,
                            "image": image_filename,
                            "analysis": analysis
                        }
                        json.dump(log_data, log_file, indent=2)

                    if analysis.get("action_required"):
                        log(f"[THREAT] Adding threat to potential threats list. Current count: {len(self.potential_threats)}")
                        self.potential_threats.append({
                            "time": current_video_time,
                            "analysis": analysis,
                            "image_path": image_path
                        })
                        
                        log(f"[THREAT] Potential threats count: {len(self.potential_threats)}/{self.confirmation_threshold}")
                        
                        # Check if this is a HIGH or CRITICAL threat - trigger immediately
                        threat_level = analysis.get("danger", "LOW")
                        if threat_level in ["HIGH", "CRITICAL"]:
                            log(f"[THREAT] HIGH/CRITICAL threat detected! Triggering alarm immediately...")
                            self._handle_confirmed_threat(self.potential_threats[-1])
                            self.last_trigger_video_time = current_video_time
                            self.potential_threats = []
                            log(f"[THREAT] Immediate alarm triggered for {threat_level} threat")
                        elif len(self.potential_threats) >= self.confirmation_threshold:
                            log(f"[THREAT] Confirmation threshold reached! Triggering alarm system...")
                            self._handle_confirmed_threat(self.potential_threats[-1])
                            self.last_trigger_video_time = current_video_time
                            self.potential_threats = []
                            log(f"[THREAT] Alarm triggered and threats list cleared")
                        else:
                            log(f"[THREAT] Waiting for more threats to reach confirmation threshold")
                    else:
                        log(f"[THREAT] No action required, clearing potential threats list")
                        self.potential_threats = []
                        
                except Exception as e:
                    log(f"[ERROR] Failed to process movement detection: {str(e)}")
                    log(f"[LOGGED] {image_filename} | Action: False | Danger: Failed to process movement")

            else:
                self.recent_activity = False

            self.prev_boxes = curr_boxes
            time.sleep(0.05)

        cap.release()
        
        if os.path.exists(current_frame_path):
            try:
                os.remove(current_frame_path)
                log("[CLEANUP] Removed current frame file")
            except Exception as e:
                log(f"[ERROR] Failed to remove current frame file: {e}")
        
        log("[STOPPED] Monitoring session ended.")

    def start(self, email=None, privacy_blur=False):
        if not self.running:
            self.running = True
            self.user_email = email
            self.privacy_blur = privacy_blur
            self.thread = threading.Thread(target=self._detect_loop)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
            self.thread = None

class SecuritySystem:
    def __init__(self):
        self.cameras = {}
        self.active_camera = None
        self.idle_time = {}
        
    def add_camera(self, camera_id, source):
        self.cameras[camera_id] = HumanMovementDetector(source)
        self.idle_time[camera_id] = 0
        log(f"[SYSTEM] Added camera: {camera_id}")
        
    def start_monitoring(self, email=None):
        for camera_id, detector in self.cameras.items():
            detector.start(email=email)
            log(f"[SYSTEM] Started camera: {camera_id}")
            
    def stop_monitoring(self):
        for camera_id, detector in self.cameras.items():
            detector.stop()
        log("[SYSTEM] Stopped all cameras")
            
    def prioritize_cameras(self):
        """Switch focus to cameras with most activity"""
        prioritizing = True
        log("[SYSTEM] Starting camera prioritization")
        
        while prioritizing:
            for camera_id, detector in self.cameras.items():
                if detector.recent_activity:
                    if self.active_camera != camera_id:
                        log(f"[SYSTEM] Prioritizing camera: {camera_id} due to activity")
                        self.active_camera = camera_id
                        self.idle_time[camera_id] = 0
                else:
                    self.idle_time[camera_id] += 1
            
            time.sleep(10)
        
        log("[SYSTEM] Camera prioritization stopped")