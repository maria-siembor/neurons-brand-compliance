Neurons Brand Compliance is a microservice that lets you upload a brand‐kit PDF and an image; it checks fonts, safe‐zone, logo colors, and palette compliance using CLIP, OpenCV, BLIP, and (optionally) Tesseract, then returns a compliance score (0–4) and reasoning.

Running locally (without Docker)
# 1 Create & activate a virtualenv (optional but recommended)
python3 -m venv venv
source venv/bin/activate

# 2 Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3 Download EAST model if missing:
wget -O frozen_east_text_detection.pb \
  https://github.com/opencv/opencv_extra/raw/master/testdata/dnn/download_models/frozen_east_text_detection.pb

# 4 Run the backend
uvicorn app.main:app --reload

# 5 In a second terminal, run the Streamlit frontend
streamlit run streamlit_app.py