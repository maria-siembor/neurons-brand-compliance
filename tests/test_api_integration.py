import os
import sys
import pytest
from fastapi.testclient import TestClient


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def brandkit_bytes():
    path = os.path.join(PROJECT_ROOT, "Neurons_brand_kit.pdf")
    with open(path, "rb") as f:
        return f.read()

@pytest.mark.parametrize("image_filename", [
    "neurons_test1.png",  
    "neurons_test2.png",
    "neurons_test3.png"
])
def test_get_score_valid(client, brandkit_bytes, image_filename):
    img_path = os.path.join(PROJECT_ROOT, image_filename)
    with open(img_path, "rb") as f:
        image_bytes = f.read()

    response = client.post(
        "/get_score",
        files={
            "brandkit": ("Neurons_brand_kit.pdf", brandkit_bytes, "application/pdf"),
            "image": (image_filename, image_bytes, "image/png")
        }
    )
    assert response.status_code == 200

    data = response.json()
    assert "score" in data
    assert "reasoning" in data

    score = data["score"]
    assert isinstance(score, int)
    assert 0 <= score <= 4

    reasoning = data["reasoning"]
    assert isinstance(reasoning, dict)
    expected_keys = {"font", "safe_zone", "logo_colors", "palette"}
    assert set(reasoning.keys()) == expected_keys

    for val in reasoning.values():
        assert isinstance(val, str)

def test_get_score_invalid_brandkit(client):
    response = client.post(
        "/upload_brandkit",
        files={"file": ("bad.jpg", b"not a pdf", "image/jpeg")}
    )
    assert response.status_code == 400

def test_healthcheck(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json() == {"message": "Neurons Brand Compliance API is running!"}