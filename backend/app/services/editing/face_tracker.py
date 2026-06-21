"""
ATELIX ViralClip AI Pipeline — Face Tracker
Uses MediaPipe Face Detector (new task API) with OpenCV Haar Cascade fallback.
Tracks speaker face for smart 9:16 cropping.
"""

from typing import Optional


def analyze_clip_face_positions(
    source_path: str,
    start_time: float,
    end_time: float,
    sample_interval: float = 1.0,
) -> dict:
    """
    Analyze face positions throughout the clip segment.
    Samples frames at regular intervals and returns smoothed tracking data.

    Priority: MediaPipe task API → OpenCV Haar Cascade → center fallback
    """
    import cv2
    import numpy as np

    cap = cv2.VideoCapture(source_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {source_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if fps <= 0 or width <= 0 or height <= 0:
        cap.release()
        raise RuntimeError(f"Invalid video metadata: {source_path}")

    clip_duration = end_time - start_time
    start_frame = int(start_time * fps)
    end_frame = min(int(end_time * fps), total_frames - 1)
    sample_every_n_frames = max(int(sample_interval * fps), 1)

    face_positions = []

    detector = _create_face_detector()

    for frame_num in range(start_frame, end_frame + 1, sample_every_n_frames):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()

        if not ret:
            continue

        timestamp = frame_num / fps - start_time
        detection = _detect_face(frame, detector)

        if detection:
            face_positions.append({
                "timestamp": round(timestamp, 2),
                "center_x": round(detection["center_x"], 4),
                "center_y": round(detection["center_y"], 4),
                "width": round(detection["width"], 4),
                "height": round(detection["height"], 4),
                "confidence": round(detection["confidence"], 4),
            })

    cap.release()

    if not face_positions:
        return {
            "method": "center_fallback",
            "face_detected": False,
            "crop_x": 0.5,
            "crop_y": 0.5,
        }

    smoothed = _kalman_smooth_positions(face_positions)
    stability = _calculate_stability(smoothed)

    return {
        "method": detection.get("method", "unknown") if 'detection' in locals() and detection else "unknown",
        "face_detected": True,
        "samples": smoothed,
        "samples_count": len(smoothed),
        "stability_score": round(stability, 4),
        "average_center_x": round(
            sum(s["center_x"] for s in smoothed) / len(smoothed), 4
        ),
        "average_center_y": round(
            sum(s["center_y"] for s in smoothed) / len(smoothed), 4
        ),
    }


def _create_face_detector() -> dict:
    """
    Create face detector instance.
    Returns a dict with 'type' and 'instance' keys, or None.
    """
    try:
        import mediapipe as mp
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision

        base_options = mp_python.BaseOptions(
            model_asset_buffer=_get_mediapipe_model_buffer()
        )
        options = vision.FaceDetectorOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            min_detection_confidence=0.5,
        )
        detector = vision.FaceDetector.create_from_options(options)
        return {"type": "mediapipe_task", "instance": detector}
    except Exception as e_mp:
        pass

    try:
        import cv2
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        cascade = cv2.CascadeClassifier(cascade_path)
        if not cascade.empty():
            return {"type": "opencv_haar", "instance": cascade}
    except Exception:
        pass

    return None


def _get_mediapipe_model_buffer() -> bytes:
    """
    Get the MediaPipe face detector model.
    Downloads if not cached.
    """
    import os

    cache_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "models")
    cache_dir = os.path.abspath(cache_dir)
    model_path = os.path.join(cache_dir, "blaze_face_short_range.tflite")

    if os.path.exists(model_path):
        with open(model_path, "rb") as f:
            return f.read()

    try:
        import urllib.request
        os.makedirs(cache_dir, exist_ok=True)
        url = "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite"
        urllib.request.urlretrieve(url, model_path)
        with open(model_path, "rb") as f:
            return f.read()
    except Exception:
        pass

    return b""


def _detect_face(frame, detector: Optional[dict]) -> Optional[dict]:
    """
    Detect the primary face in a frame.
    Returns dict with center_x, center_y, width, height, confidence, method.
    """
    if detector is None:
        return None

    h, w = frame.shape[:2]

    if detector["type"] == "mediapipe_task":
        try:
            import mediapipe as mp
            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=frame,
            )
            result = detector["instance"].detect(mp_image)

            if result.detections:
                det = result.detections[0]
                bbox = det.bounding_box
                return {
                    "center_x": (bbox.origin_x + bbox.width / 2) / w,
                    "center_y": (bbox.origin_y + bbox.height / 2) / h,
                    "width": bbox.width / w,
                    "height": bbox.height / h,
                    "confidence": det.categories[0].score if det.categories else 1.0,
                    "method": "mediapipe",
                }
        except Exception:
            pass

    if detector["type"] == "opencv_haar":
        import cv2
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector["instance"].detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )

        if len(faces) > 0:
            x, y, fw, fh = faces[0]
            return {
                "center_x": (x + fw / 2) / w,
                "center_y": (y + fh / 2) / h,
                "width": fw / w,
                "height": fh / h,
                "confidence": 0.8,
                "method": "opencv_haar",
            }

    return None


def _kalman_smooth_positions(
    positions: list[dict],
    alpha: float = 0.3,
) -> list[dict]:
    """
    Apply exponential moving average smoothing to reduce jitter.
    """
    if len(positions) <= 2:
        return positions

    smoothed = [positions[0].copy()]

    for i in range(1, len(positions)):
        prev = smoothed[-1]
        curr = positions[i]

        smoothed.append({
            "timestamp": curr["timestamp"],
            "center_x": round(prev["center_x"] * (1 - alpha) + curr["center_x"] * alpha, 4),
            "center_y": round(prev["center_y"] * (1 - alpha) + curr["center_y"] * alpha, 4),
            "width": round(prev["width"] * (1 - alpha) + curr["width"] * alpha, 4),
            "height": round(prev["height"] * (1 - alpha) + curr["height"] * alpha, 4),
            "confidence": curr["confidence"],
        })

    return smoothed


def _calculate_stability(positions: list[dict]) -> float:
    """
    Calculate how stable the face position is (0 = jittery, 1 = stable).
    """
    if len(positions) < 2:
        return 1.0

    dx = [
        abs(positions[i]["center_x"] - positions[i - 1]["center_x"])
        for i in range(1, len(positions))
    ]
    dy = [
        abs(positions[i]["center_y"] - positions[i - 1]["center_y"])
        for i in range(1, len(positions))
    ]

    if not dx or not dy:
        return 1.0

    avg_movement = sum(dx) / len(dx) + sum(dy) / len(dy)
    stability = max(0.0, min(1.0, 1.0 - avg_movement * 5))

    return stability
