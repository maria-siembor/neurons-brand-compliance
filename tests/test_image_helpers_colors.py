import os
import sys
import pytest
from PIL import Image, ImageDraw
import io

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.image_analyzer_helpers import check_logo_colors

def create_three_triangle_image(
    hex_list: list,
    image_size=(200, 200),
    triangle_size=40
):
    """
    Creates a synthetic image with three upward-pointing triangles,
    each filled with a color from `hex_list[0:3]`, placed at distinct corners.
    All other pixels are white. Returns raw PNG bytes.
    """
    img = Image.new("RGB", image_size, color="white")
    draw = ImageDraw.Draw(img)


    coords = [
        (10, 10),  
        (image_size[0] - triangle_size - 10, 10),  
        ( (image_size[0] - triangle_size)//2, image_size[1] - triangle_size - 10 )  
    ]

    for idx, hx in enumerate(hex_list[:3]):
        x0, y0 = coords[idx]
        x1, y1 = x0 + triangle_size, y0 + triangle_size
        draw.polygon([(x0, y1), ((x0 + x1) // 2, y0), (x1, y1)], fill=hx)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def test_logo_colors_exact_match_three_triangles():
    kit_hexes = ["#85A0FE", "#AA82FF", "#FE839C", "#FFD14C", "#380F57"]
    img_bytes = create_three_triangle_image(kit_hexes)
    assert check_logo_colors(image_bytes=img_bytes, logo_colors_hex=kit_hexes) is True

def test_logo_colors_failure_non_logo_color():
    img = Image.new("RGB", (200, 200), color="white")
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 150, 150], fill="#FF0000")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    kit_hexes = ["#85A0FE", "#AA82FF", "#FE839C", "#FFD14C", "#380F57"]
    assert check_logo_colors(image_bytes=img_bytes, logo_colors_hex=kit_hexes) is False