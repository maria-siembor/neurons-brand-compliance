import logging
import cv2
import numpy as np
from PIL import Image
import io
from typing import List
from sklearn.cluster import KMeans

logger = logging.getLogger("neurons_api.image_helpers")
    
    
def rgb_to_hex(rgb):
    r, g, b = rgb[0], rgb[1], rgb[2]
    return "#{:02X}{:02X}{:02X}".format(int(r), int(g), int(b))

def hex_to_hsv_range(hex_color: str, tol: int = 15):
    """
    Convert a hex color string (e.g. "#85A0FE") into a lower/upper HSV range.
    Returns (lower, upper) as np.ndarray of dtype uint8.

    We:
    1. Parse R, G, B.
    2. Convert 1x1 BGR pixel → HSV via cv2.cvtColor.
    3. Take the Hue, then form [Hue - tol, 50, 50] → [Hue + tol, 255, 255].
    """
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    
    bgr_pixel = np.uint8([[[b, g, r]]]) 
    hsv_pixel = cv2.cvtColor(bgr_pixel, cv2.COLOR_BGR2HSV)[0][0]
    h_val, s_val, v_val = int(hsv_pixel[0]), int(hsv_pixel[1]), int(hsv_pixel[2])

    lower = np.array([max(h_val - tol, 0), 50, 50], dtype=np.uint8)
    upper = np.array([min(h_val + tol, 179), 255, 255], dtype=np.uint8)
    return lower, upper

def check_logo_safe_zone(
    image_bytes: bytes,
    safe_zone_px: int,
    logo_colors_hex: List[str]
) -> bool:
    """
    Verifies that the largest “logo” contour (derived via color masks) has at least
    `safe_zone_px` pixels of empty margin on all four sides.

    Returns True if margins ≥ safe_zone_px on left/right/top/bottom.
    """
    try:
        pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        img_h, img_w = cv_img.shape[:2]

        hsv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2HSV)

        combined_mask = None
        for hx in logo_colors_hex:
            lower, upper = hex_to_hsv_range(hx, tol=15)
            mask = cv2.inRange(hsv_img, lower, upper)
            combined_mask = mask if combined_mask is None else cv2.bitwise_or(combined_mask, mask)

        if combined_mask is None:
            return False

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        cleaned = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return False

        largest = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest)

        left_margin   = x
        top_margin    = y
        right_margin  = img_w - (x + w)
        bottom_margin = img_h - (y + h)

        return (
            left_margin   >= safe_zone_px and
            top_margin    >= safe_zone_px and
            right_margin  >= safe_zone_px and
            bottom_margin >= safe_zone_px
        )

    except Exception as e:
        logging.getLogger("neurons_api.image_helpers").error(f"check_logo_safe_zone error: {e}")
        return False

def check_logo_colors(
    image_bytes: bytes,
    logo_colors_hex: List[str]
) -> bool:
    """
    Extracts the exact “logo region” mask (same as safe-zone), then verifies that
    ≥ 90% of the masked pixels match exactly one of the brand’s five hex codes.

    Returns True if coverage ≥ 0.90.
    """
    try:
        pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        hsv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2HSV)

        combined_mask = None
        for hx in logo_colors_hex:
            lower, upper = hex_to_hsv_range(hx, tol=15)
            mask = cv2.inRange(hsv_img, lower, upper)
            combined_mask = mask if combined_mask is None else cv2.bitwise_or(combined_mask, mask)

        if combined_mask is None:
            return False

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        cleaned = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)

        ys, xs = np.where(cleaned > 0)
        if ys.size == 0:
            return False

        bgr_pixels = cv_img[ys, xs]    
        rgb_pixels = bgr_pixels[:, ::-1]  

        total_pixels = rgb_pixels.shape[0]
        matched = 0
        kit_hexes = set(h.upper() for h in logo_colors_hex)

        for rgb in rgb_pixels:
            r_int, g_int, b_int = int(rgb[0]), int(rgb[1]), int(rgb[2])
            px_hex = rgb_to_hex((r_int, g_int, b_int))
            if px_hex.upper() in kit_hexes:
                matched += 1

        coverage = matched / total_pixels if total_pixels > 0 else 0.0
        return coverage >= 0.90

    except Exception as e:
        logging.getLogger("neurons_api.image_helpers").error(f"check_logo_colors error: {e}")
        return False
        
def check_palette_compliance(
    image_bytes: bytes,
    primary_colors_hex: list,
    k: int = 5,
    delta_e_tol: float = 10.0
) -> bool:
    """
    1. Resize image to 100×100, reshape → (10000, 3) RGB array.
    2. Run KMeans(n_clusters=k) to get k cluster_centers in RGB.
    3. Convert each center to CIELAB via OpenCV:
       - center_rgb → BGR (swap channels) → np.uint8 → cv2.cvtColor(..., BGR2LAB)
    4. Convert each brand hex to CIELAB (same procedure).
    5. If any cluster ΔE < delta_e_tol relative to any brand color, return True.
    6. Otherwise False.
    """
    try:
        pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        small = pil_img.resize((100, 100))
        arr = np.array(small).reshape(-1, 3) 

        kmeans = KMeans(n_clusters=k, random_state=42).fit(arr)
        centers_rgb = kmeans.cluster_centers_  

        def rgb_to_lab(rgb_triplet):
            r, g, b = int(rgb_triplet[0]), int(rgb_triplet[1]), int(rgb_triplet[2])
            bgr = np.uint8([[[b, g, r]]])
            lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)[0][0]
            return lab.astype(np.float32)

        centers_lab = [rgb_to_lab(center) for center in centers_rgb]

        brand_labs = []
        for hx in primary_colors_hex:
            r = int(hx[1:3], 16)
            g = int(hx[3:5], 16)
            b = int(hx[5:7], 16)
            brand_labs.append(rgb_to_lab((r, g, b)))

        for cl in centers_lab:
            for bl in brand_labs:
                dE = np.linalg.norm(cl - bl)
                if dE < delta_e_tol:
                    return True

        return False

    except Exception as e:
        logging.getLogger("neurons_api.image_helpers").error(
            f"check_palette_compliance error: {e}"
        )
        return False
    

