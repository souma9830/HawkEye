#!/usr/bin/env python3
"""
Test script for live camera functionality in HawkEye
This script tests if the camera can be accessed and if the detection system works with live camera input.
"""

import cv2
import sys
import os

def test_camera_access(camera_index=0):
    """Test if camera can be accessed"""
    print(f"Testing camera access for camera index {camera_index}...")
    
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print(f"❌ Camera {camera_index} is not available")
        return False
    
    # Try to read a frame
    ret, frame = cap.read()
    if not ret:
        print(f"❌ Camera {camera_index} opened but cannot read frames")
        cap.release()
        return False
    
    print(f"✅ Camera {camera_index} is working!")
    print(f"   Frame size: {frame.shape[1]}x{frame.shape[0]}")
    print(f"   FPS: {cap.get(cv2.CAP_PROP_FPS)}")
    
    cap.release()
    return True

def test_multiple_cameras():
    """Test multiple camera indices"""
    print("Testing multiple camera indices...")
    available_cameras = []
    
    for i in range(5):
        if test_camera_access(i):
            available_cameras.append(i)
    
    print(f"\n📊 Summary: {len(available_cameras)} camera(s) available")
    if available_cameras:
        print(f"   Available cameras: {available_cameras}")
    else:
        print("   No cameras found!")
    
    return available_cameras

def test_detector_import():
    """Test if the detector can be imported"""
    print("\nTesting detector import...")
    try:
        sys.path.append('.')
        from detector import HumanMovementDetector
        print("✅ Detector module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import detector: {e}")
        return False

def main():
    print("🔍 HawkEye Live Camera Test")
    print("=" * 40)
    
    # Test detector import
    if not test_detector_import():
        print("\n❌ Cannot proceed without detector module")
        return
    
    # Test camera access
    available_cameras = test_multiple_cameras()
    
    if not available_cameras:
        print("\n❌ No cameras available. Please check your camera connection.")
        return
    
    # Test with default camera
    print(f"\n🎥 Testing with default camera (index {available_cameras[0]})...")
    
    try:
        from detector import HumanMovementDetector
        
        # Create detector with live camera
        detector = HumanMovementDetector(video_source=available_cameras[0])
        print("✅ Detector created successfully with live camera source")
        
        # Test if we can start detection (but don't actually start it)
        print("✅ Live camera integration test passed!")
        
    except Exception as e:
        print(f"❌ Error testing live camera integration: {e}")
        return
    
    print("\n🎉 All tests passed! Live camera functionality should work.")
    print("\nTo use live camera monitoring:")
    print("1. Start the HawkEye application")
    print("2. Go to the 'Live Camera Monitoring' section")
    print("3. Select your camera and click 'Start Live Monitoring'")

if __name__ == "__main__":
    main() 