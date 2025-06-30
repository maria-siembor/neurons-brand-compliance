FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    libgl1-mesa-glx \
    libglib2.0-0 \
    poppler-utils \
 && rm -rf /var/lib/apt/lists/*


WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

RUN wget -O /app/frozen_east_text_detection.pb https://github.com/opencv/opencv_extra/raw/master/testdata/dnn/download_models/frozen_east_text_detection.pb

# 8000 for FastAPI, 8501 for Streamlit
EXPOSE 8000
EXPOSE 8501

COPY run.sh /app/run.sh
RUN chmod +x /app/run.sh

CMD ["/app/run.sh"]