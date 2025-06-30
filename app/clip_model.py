from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import torch
import io

_processor = None
_model = None

def _load_clip():
    """
    Lazily load CLIPProcessor and CLIPModel into
    the module level variables on first use.
    """
    global _processor, _model

    if _processor is None or _model is None:
        _processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        _model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")

def assess_image_with_clip(image_bytes):
    """
    Return a dictionary with:
      - clip_score: probability that the image is “brand compliant”
      - non_compliant_score: probability that the image is “non compliant”
      - raw_probs: [p_compliant, p_non_compliant]

    Usage:
        result = assess_image_with_clip(image_bytes)
        # result["clip_score"] is a float in [0,1]
    """
   
    _load_clip()

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    prompts = ["a brand-compliant image", "a non-compliant image"]

    inputs = _processor(text=prompts, images=image, return_tensors="pt", padding=True)

    outputs = _model(**inputs)


    probs = outputs.logits_per_image.softmax(dim=1).tolist()[0]
    clip_score = probs[0]
    non_compliant_score = probs[1]

    return {
        "clip_score": clip_score,
        "non_compliant_score": non_compliant_score,
        "raw_probs": probs
    }