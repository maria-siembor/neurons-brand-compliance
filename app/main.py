import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from app.schemas import ImageAnalysis, BrandkitInfo, ComplianceResponse

from app import brandkit_parser, image_analyzer, compliance_checker

# --------- Logger configuration ------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("neurons_api")
# -------------------------------------------

app = FastAPI()

@app.get("/")
def read_root():
    logger.info("GET / → health check")
    return {"message": "Neurons Brand Compliance API is running!"}

@app.post("/upload_brandkit")
async def upload_brandkit(file: UploadFile = File(...)):
    """
    Accepts a multipart form with field “file” containing a brand-kit PDF.
    Returns the parsed BrandkitInfo JSON.
    """
    try:
        content = await file.read()
        result = brandkit_parser.extract_brandkit_info(content)
        return {"brandkit_info": result}
    except Exception as e:
        logger.error(f"Failed to parse brand kit PDF: {e}")
        raise HTTPException(status_code=400, detail="Invalid brand kit PDF")

@app.post("/get_score")
async def get_score(
    image: UploadFile = File(...),
    brandkit: UploadFile = File(...)
):
    """
    Accepts two multipart fields:
      - brandkit: PDF file
      - image: PNG/JPEG file

    Returns JSON matching ComplianceResponse:
      {
        "score": <int 0–4>,
        "reasoning": {
          "font": <str>,
          "safe_zone": <str>,
          "logo_colors": <str>,
          "palette": <str>
        }
      }
    """
    # 1. Parse brand kit
    try:
        brandkit_bytes = await brandkit.read()
        brandkit_data = brandkit_parser.extract_brandkit_info(brandkit_bytes)
    except Exception as e:
        logger.error(f"Failed to parse brand kit in /get_score: {e}")
        raise HTTPException(status_code=400, detail="Invalid brand kit PDF")

    # 2. Analyze image
    try:
        image_bytes = await image.read()
        image_data = image_analyzer.analyze_image(image_bytes, brandkit_data)
    except Exception as e:
        logger.error(f"Image analysis failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid image or analysis error")

    # 3. Check compliance
    try:
        score, reasoning = compliance_checker.check_compliance(image_data, brandkit_data)
        logger.info(f"Compliance score computed: {score}/4")
        return {"score": score, "reasoning": reasoning}
    except Exception as e:
        logger.error(f"Compliance checking failed: {e}")
        raise HTTPException(status_code=500, detail="Internal compliance check error")