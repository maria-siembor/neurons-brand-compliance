import logging
import cv2
import numpy as np
from PIL import Image
import io
import pytesseract

from app.clip_model import assess_image_with_clip
from app.blip_model import ask_blip_question
from app.image_analyzer_helpers import (
    check_logo_safe_zone,
    check_logo_colors,
    check_palette_compliance,
    hex_to_hsv_range,
    rgb_to_hex
)

logger = logging.getLogger("neurons_api.image_analyzer")

def crop_largest_text_region(image_bytes: bytes, min_confidence: float = 0.5):
    """
    Uses OpenCVs EAST text detector to find text regions. Returns the
    cropped PIL image of the largest text bounding box, or None if none found.
    """
    pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    orig_w, orig_h = pil_img.size
    cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    (H, W) = cv_img.shape[:2]

    newW, newH = (320, 320)
    rW = W / float(newW)
    rH = H / float(newH)

    blob = cv2.dnn.blobFromImage(
        cv_img,
        scalefactor=1.0,
        size=(newW, newH),
        mean=(123.68, 116.78, 103.94),
        swapRB=True,
        crop=False
    )

    net = cv2.dnn.readNet("frozen_east_text_detection.pb")
    net.setInput(blob)
    (scores, geometry) = net.forward(["feature_fusion/Conv_7/Sigmoid", "feature_fusion/concat_3"])

    (numRows, numCols) = scores.shape[2:4]
    rects = []
    confidences = []

    for y in range(numRows):
        scoresData = scores[0, 0, y]
        xData0 = geometry[0, 0, y]
        xData1 = geometry[0, 1, y]
        xData2 = geometry[0, 2, y]
        xData3 = geometry[0, 3, y]
        anglesData = geometry[0, 4, y]

        for x in range(numCols):
            if scoresData[x] < min_confidence:
                continue
            offsetX = x * 4.0
            offsetY = y * 4.0
            angle = anglesData[x]
            cos = np.cos(angle)
            sin = np.sin(angle)
            h = xData0[x] + xData2[x]
            w = xData1[x] + xData3[x]
            endX = int(offsetX + (cos * xData1[x]) + (sin * xData2[x]))
            endY = int(offsetY - (sin * xData1[x]) + (cos * xData2[x]))
            startX = int(endX - w)
            startY = int(endY - h)

            rects.append((startX, startY, endX, endY))
            confidences.append(float(scoresData[x]))

    if not rects:
        return None

    boxes = cv2.dnn.NMSBoxes(rects, confidences, min_confidence, 0.4)
    if len(boxes) == 0:
        return None

    max_area = 0
    best_box = None
    for i in boxes.flatten():
        (startX, startY, endX, endY) = rects[i]
        area = (endX - startX) * (endY - startY)
        if area > max_area:
            max_area = area
            best_box = (startX, startY, endX, endY)

    if best_box is None:
        return None

    (sx, sy, ex, ey) = best_box
    sx = int(sx * rW)
    sy = int(sy * rH)
    ex = int(ex * rW)
    ey = int(ey * rH)

    sx, sy = max(0, sx), max(0, sy)
    ex, ey = min(W, ex), min(H, ey)

    cropped = cv_img[sy:ey, sx:ex]
    cropped_pil = Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))
    return cropped_pil


def analyze_image(image_bytes: bytes, brandkit_data: dict) -> dict:
    """
    Returns a dict matching ImageAnalysis:
    {
      "clip_score": float,
      "detected_fonts": [str],
      "font_style_ok": bool,
      "logo_safe_zone_ok": bool,
      "logo_colors_ok": bool,
      "palette_ok": bool
    }
    """
    try:
        clip_res = assess_image_with_clip(image_bytes)
        clip_score = clip_res.get("clip_score", 0.0)
        is_compliant_clip = clip_score > 0.5
    except Exception as e:
        logger.error(f"CLIP model error: {e}")
        clip_score = 0.0
        is_compliant_clip = False

    try:
        safe_zone_px = brandkit_data.get("safe_zone_px", 0)
        logo_safe_zone_ok = check_logo_safe_zone(
            image_bytes,
            safe_zone_px,
            logo_colors_hex=brandkit_data.get("logo_colors", [])
        )
    except Exception as e:
        logger.error(f"Logo safe‐zone check error: {e}")
        logo_safe_zone_ok = False


    try:
        logo_colors_ok = check_logo_colors(
            image_bytes,
            logo_colors_hex=brandkit_data.get("logo_colors", [])
        )
    except Exception as e:
        logger.error(f"Logo color check error: {e}")
        logo_colors_ok = False


    try:
        palette_ok = check_palette_compliance(
            image_bytes,
            primary_colors_hex=brandkit_data.get("primary_colors", [])
        )
    except Exception as e:
        logger.error(f"Palette compliance check error: {e}")
        palette_ok = False


    try:
        cropped = crop_largest_text_region(image_bytes)
        if cropped is not None:
            buf = io.BytesIO()
            cropped.save(buf, format="PNG")
            cropped_bytes = buf.getvalue()
            font_answer = ask_blip_question(cropped_bytes, "What font is used in this image?")
        else:
            font_answer = ask_blip_question(image_bytes, "What font is used in this image?")

        expected_fonts = [
            brandkit_data.get("primary_font", ""),
            brandkit_data.get("secondary_font", "")
        ]
        ans_lower = font_answer.lower()
        if any(f.lower() in ans_lower for f in expected_fonts):
            font_style_ok = True
        else:
            font_style_ok = False
            if cropped is not None:
                ocr_text = pytesseract.image_to_string(cropped).lower()
                if any(f.lower() in ocr_text for f in expected_fonts):
                    font_style_ok = True

        detected_fonts = [font_answer]

    except Exception as e:
        logger.error(f"Font detection error: {e}")
        font_style_ok = False
        detected_fonts = []

    if not any([logo_safe_zone_ok, logo_colors_ok, palette_ok, font_style_ok]) and is_compliant_clip:
        logo_safe_zone_ok = logo_colors_ok = palette_ok = font_style_ok = True

    return {
        "clip_score": clip_score,
        "detected_fonts": detected_fonts,
        "font_style_ok": font_style_ok,
        "logo_safe_zone_ok": logo_safe_zone_ok,
        "logo_colors_ok": logo_colors_ok,
        "palette_ok": palette_ok
    }