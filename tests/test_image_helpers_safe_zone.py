import os
import sys
import pytest
from PIL import Image, ImageDraw
import io


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.image_analyzer_helpers import check_logo_safe_zone

def create_test_image(hex_color: str, position: tuple, image_size=(500, 500), square_size=100):
    """
    Creates a synthetic image:
      - White background
      - A solid square of size `square_size`×`square_size` filled with `hex_color`
        placed with its top-left corner at `position` (x, y).
    Returns raw PNG bytes.
    """
    img = Image.new("RGB", image_size, color="white")
    draw = ImageDraw.Draw(img)
    x0, y0 = position
    x1, y1 = x0 + square_size, y0 + square_size
    draw.rectangle([x0, y0, x1, y1], fill=hex_color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

@pytest.mark.parametrize("pos, safe_zone, expected", [
    ((200, 200), 50, True),  
    ((0, 0),     10, False),  
    ((50, 50),   60, False),  
    ((30, 30),   30, True),   
    ((30, 30),   31, False),  
])
def test_check_logo_safe_zone(pos, safe_zone, expected):
    hex_color = "#85A0FE"
    img_bytes = create_test_image(hex_color, pos)
    result = check_logo_safe_zone(
        image_bytes=img_bytes,
        safe_zone_px=safe_zone,
        logo_colors_hex=[hex_color]
    )
    assert result is expected