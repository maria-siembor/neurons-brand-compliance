import os
import sys
import pytest
from PIL import Image, ImageDraw, ImageFont
import io

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.image_analyzer import crop_largest_text_region, analyze_image

LEXEND_TTF = os.path.join(PROJECT_ROOT, "fonts", "Lexend-Regular.ttf")
ARIAL_TTF = "C:/Windows/Fonts/arial.ttf"

def create_text_image(text, font_path, size=(400, 200), fontsize=64):
    """
    Creates a white background image with centered `text` using `font_path`.
    Returns raw PNG bytes.
    """
    img = Image.new("RGB", size, color="white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_path, fontsize)

    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]

    x = (size[0] - w) // 2
    y = (size[1] - h) // 2
    draw.text((x, y), text, font=font, fill="black")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

@pytest.mark.skipif(
    not os.path.isfile(LEXEND_TTF),
    reason="Lexend TTF not found at {}".format(LEXEND_TTF)
)
def test_crop_and_blip_recognizes_lexend():
    img_bytes = create_text_image("HELLO", LEXEND_TTF)
    cropped = crop_largest_text_region(img_bytes)
    assert cropped is not None, "EAST failed to detect text region"

    buf = io.BytesIO()
    cropped.save(buf, format="PNG")
    cropped_bytes = buf.getvalue()

    from app.blip_model import ask_blip_question
    resp = ask_blip_question(cropped_bytes, "What font is used in this image?")
    assert "lexend" in resp.lower()

def test_analyze_image_font_field_is_boolean():
    img_bytes = create_text_image("TEST", ARIAL_TTF)
    fake_brandkit = {
        "primary_font": "Lexend",
        "secondary_font": "Inter",
        "safe_zone_px": 30,
        "logo_colors": ["#85A0FE", "#AA82FF", "#FE839C", "#FFD14C", "#380F57"],
        "primary_colors": ["#85A0FE", "#AA82FF", "#FE839C", "#FFD14C", "#380F57"]
    }

    result = analyze_image(img_bytes, fake_brandkit)
    assert isinstance(result, dict)

    assert "font_style_ok" in result
    assert isinstance(result["font_style_ok"], bool)

    assert "detected_fonts" in result
    assert isinstance(result["detected_fonts"], list)
    for f in result["detected_fonts"]:
        assert isinstance(f, str)