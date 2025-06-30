from pydantic import BaseModel
from typing import List, Dict

class ImageAnalysis(BaseModel):
    clip_score: float
    detected_fonts: List[str]
    font_style_ok: bool
    logo_safe_zone_ok: bool
    logo_colors_ok: bool
    palette_ok: bool

class BrandkitInfo(BaseModel):
    primary_font: str
    secondary_font: str
    safe_zone_px: int
    logo_colors: List[str]
    primary_colors: List[str]

class ComplianceResponse(BaseModel):
    score: int
    reasoning: Dict[str, str]