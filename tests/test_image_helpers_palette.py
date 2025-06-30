import os
import sys
import pytest
from PIL import Image
import numpy as np
import io


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.image_analyzer_helpers import check_palette_compliance

def create_solid_color_image(hex_color: str, size=(100, 100)):
    """
    Creates a solid‐fill image of size (100×100) in the given hex color.
    Returns raw PNG bytes.
    """
    img = Image.new("RGB", size, color=hex_color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def test_palette_compliance_exact_match():
    kit_hexes = ["#85A0FE", "#AA82FF", "#FE839C", "#FFD14C", "#380F57"]
    img_bytes = create_solid_color_image("#85A0FE")
    assert check_palette_compliance(img_bytes, kit_hexes, k=3, delta_e_tol=5) is True

def test_palette_compliance_no_brand_color():
    kit_hexes = ["#85A0FE", "#AA82FF", "#FE839C", "#FFD14C", "#380F57"]
    img_bytes = create_solid_color_image("#808080")
    assert check_palette_compliance(img_bytes, kit_hexes, k=3, delta_e_tol=5) is False

def test_palette_compliance_tolerance():
    kit_hexes = ["#85A0FE"]
    img_bytes = create_solid_color_image("#84A0FD")
    assert check_palette_compliance(img_bytes, kit_hexes, k=1, delta_e_tol=10) is True