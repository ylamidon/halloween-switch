"""Counts the people in the original photo, to pick the solo or group edit prompt (see presets.py).

YuNet face detector (OpenCV Zoo, MIT, models/face_detection_yunet_2023mar.onnx) through cv2.FaceDetectorYN.
Only 1 vs. several matters; 0 detected (masks, faces turned away) falls back to the group prompt.
"""

from __future__ import annotations

from pathlib import Path

import cv2

MODEL = Path(__file__).resolve().parent / "models" / "face_detection_yunet_2023mar.onnx"
MAX_SIDE = 1024  # px: detection input; small faces in group photos survive at this size
SCORE = 0.7


def count_faces(photo: Path) -> int:
    img = cv2.imread(str(photo))
    if img is None:
        raise ValueError(f"unreadable image: {photo}")
    scale = MAX_SIDE / max(img.shape[:2])
    if scale < 1:
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    h, w = img.shape[:2]
    detector = cv2.FaceDetectorYN.create(str(MODEL), "", (w, h), score_threshold=SCORE)
    _, faces = detector.detect(img)
    return 0 if faces is None else len(faces)
