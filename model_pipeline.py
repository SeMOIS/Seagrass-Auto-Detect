import cv2
import numpy as np
import json
import os
from PIL import Image
from io import BytesIO
import base64

# Load config
def _load_config():
    path = "config.json"
    default = {"quadrat_area_m2": 0.25, "carbon_density_g_per_m2": 100.0}
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r") as f:
            cfg = json.load(f)
        return {**default, **cfg}
    except Exception:
        return default

def _resize_max(img, max_side=1280):
    h, w = img.shape[:2]
    scale = min(1.0, max_side / max(h, w))
    if scale < 1.0:
        img = cv2.resize(img, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_AREA)
    return img

def _morph_cleanup(mask, open_k=5, close_k=7):
    open_k = max(1, int(open_k))
    close_k = max(1, int(close_k))
    k1 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (open_k, open_k))
    k2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_k, close_k))
    m = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k1)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k2)
    return m

def _suppress_glints(img_bgr):
    # Reduce specular highlights using simple min filter in HSV V channel
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    v_blur = cv2.medianBlur(v, 5)
    v = cv2.min(v, v_blur)
    hsv2 = cv2.merge([h, s, v])
    return cv2.cvtColor(hsv2, cv2.COLOR_HSV2BGR)

def _overlay(image_bgr, mask, color=(0,255,0), alpha=0.45):
    overlay = image_bgr.copy()
    colored = np.zeros_like(image_bgr)
    colored[:] = color
    overlay = np.where(mask[...,None]>0, (alpha*colored + (1-alpha)*overlay).astype(np.uint8), overlay)
    return overlay

def _to_b64(image_bgr):
    # Convert BGR to RGB for PIL
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(image_rgb)
    buf = BytesIO()
    pil.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return b64

def analyze_image(image_path, out_dir="outputs"):
    cfg = _load_config()
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("Cannot read image")
    img = _resize_max(img, 1280)

    # Optional highlight suppression
    img = _suppress_glints(img)

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Seagrass mask (greenish, enough saturation and brightness)
    lower_green = np.array([35, 50, 35], dtype=np.uint8)
    upper_green = np.array([95, 255, 255], dtype=np.uint8)
    mask_seagrass = cv2.inRange(hsv, lower_green, upper_green)

    # White sand mask (low saturation, high value)
    lower_white = np.array([0, 0, 185], dtype=np.uint8)
    upper_white = np.array([180, 60, 255], dtype=np.uint8)
    mask_white = cv2.inRange(hsv, lower_white, upper_white)

    # Morphological cleanup
    mask_seagrass = _morph_cleanup(mask_seagrass, open_k=5, close_k=7)
    mask_white = _morph_cleanup(mask_white, open_k=3, close_k=5)

    # Remove overlaps (if any): prefer seagrass label
    overlap = cv2.bitwise_and(mask_seagrass, mask_white)
    mask_white = cv2.bitwise_and(mask_white, cv2.bitwise_not(overlap))

    total_pixels = img.shape[0]*img.shape[1]
    seagrass_area = int(np.count_nonzero(mask_seagrass))
    white_area = int(np.count_nonzero(mask_white))

    seagrass_pct = 100.0 * seagrass_area / total_pixels
    white_pct = 100.0 * white_area / total_pixels

    # Blue carbon estimate (placeholder model):
    # grams C = (seagrass_cover_fraction) * quadrat_area_m2 * carbon_density_g_per_m2
    seagrass_cover_fraction = seagrass_pct / 100.0
    blue_carbon_g = seagrass_cover_fraction * cfg["quadrat_area_m2"] * cfg["carbon_density_g_per_m2"]

    # Overlays
    overlay_sea = _overlay(img, mask_seagrass, color=(0,255,120), alpha=0.45)
    overlay_wh = _overlay(img, mask_white, color=(255,255,255), alpha=0.35)

    # Export to base64 (for UI)
    overlay_sea_b64 = _to_b64(overlay_sea)
    overlay_wh_b64 = _to_b64(overlay_wh)

    return {
        "seagrass_pct": round(seagrass_pct, 2),
        "white_pct": round(white_pct, 2),
        "blue_carbon_g": float(blue_carbon_g),
        "overlay_seagrass_b64": overlay_sea_b64,
        "overlay_white_b64": overlay_wh_b64
    }