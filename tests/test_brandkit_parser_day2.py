import os
import sys


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
from app.brandkit_parser import extract_brandkit_info

@pytest.fixture
def brandkit_pdf_bytes():
    pdf_path = os.path.join(PROJECT_ROOT, "Neurons_brand_kit.pdf")
    with open(pdf_path, "rb") as f:
        return f.read()

def test_extract_safe_zone_and_colors(brandkit_pdf_bytes):
    info = extract_brandkit_info(brandkit_pdf_bytes)

    assert info["primary_font"] == "Lexend"
    assert info["secondary_font"] == "Inter"

    assert info["safe_zone_px"] == 30

    expected = ["#85A0FE", "#AA82FF", "#FE839C", "#FFD14C", "#380F57"]
    assert isinstance(info["logo_colors"], list)
    assert info["logo_colors"] == expected
    assert info["primary_colors"] == expected