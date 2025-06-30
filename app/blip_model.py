from transformers import BlipProcessor, BlipForQuestionAnswering
from PIL import Image
import torch
import io

_processor = None
_model = None

def _load_blip():
    global _processor, _model
    if _processor is None or _model is None:
        _processor = BlipProcessor.from_pretrained("Salesforce/blip-vqa-base")
        _model = BlipForQuestionAnswering.from_pretrained("Salesforce/blip-vqa-base")

def ask_blip_question(image_bytes, question: str):
    _load_blip()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    inputs = _processor(image, question, return_tensors="pt")
    output = _model.generate(**inputs)
    answer = _processor.decode(output[0], skip_special_tokens=True)
    return answer