"""
ATELIX ViralClip AI Pipeline — Face Tracker
Uses MediaPipe Face Mesh to detect and track the speaker's face for smart 9:16 cropping.
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
    Samples frames at regular intervals, detects faces, and returns
    smoothed tracking data for the smart crop algorithm.

    Uses MediaPipe Face Mesh for robust face detection.
    """
    import cv2
    import mediapipe as mp
    import numpy as np

    mp_face_detection = mp.solutions.face_detection
    mp_drawing = mp.solutions.drawing_utils

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

    with mp_face_detection.FaceDetection(
        model_selection=1, min_detection_confidence=0.5
    ) as detector:
        for frame_num in range(start_frame, end_frame + 1, sample_every_n_frames):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()

            if not ret:
                continue

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = detector.process(rgb_frame)

            timestamp = frame_num / fps - start_time

            if results.detections:
                detection = results.detections[0]

                bbox = detection.location_data.relative_bounding_box
                cx = bbox.xmin + bbox.width / 2
                cy = bbox.ymin + bbox.height / 2

                face_positions.append({
                    "timestamp": round(timestamp, 2),
                    "center_x": round(cx, 4),
                    "center_y": round(cy, 4),
                    "width": round(bbox.width, 4),
                    "height": round(bbox.height, 4),
                    "confidence": round(detection.score[0], 4),
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
        "method": "mediapipe_face_mesh",
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


def _kalman_smooth_positions(
    positions: list[dict],
    process_noise: float = 1e-3,
    measurement_noise: float = 1e-1,
) -> list[dict]:
    """
    Apply simple Kalman-like smoothing to reduce jitter in face tracking.
    Uses exponential moving average as a lightweight approximation.
    """
    if len(positions) <= 2:
        return positions

    alpha = 0.3

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
    Calculate how stable the face position is throughout the clip.
    Returns 0 (very unstable) to 1 (perfectly stable).
    """
    if len(positions) < 2:
        return 1.0

    import math

    dx = [abs(positions[i]["center_x"] - positions[i - 1]["center_x"]) for i in range(1, len(positions))]
    dy = [abs(positions[i]["center_y"] - positions[i - 1]["center_y"]) for i in range(1, len(positions))]

    avg_movement = sum(dx) / len(dx) + sum(dy) / len(dy)
    stability = max(0.0, min(1.0, 1.0 - avg_movement * 5))

    return stability
