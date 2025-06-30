import streamlit as st
import requests
from PIL import Image
import io
import pandas as pd

BACKEND_URL = "http://localhost:8000" 

st.set_page_config(page_title="Neurons Compliance Checker", layout="centered")
st.title("Neurons Brand Compliance Checker")

st.markdown(
    "Upload a Neurons Brand-Kit PDF and an ad image (PNG/JPEG), then click 'Analyze' to get a compliance score."
)

brandkit_file = st.file_uploader("Brand-Kit PDF", type=["pdf"])
image_file = st.file_uploader("Ad Image (PNG/JPEG)", type=["png", "jpg", "jpeg"])

if st.button("Analyze") and brandkit_file and image_file:
    with st.spinner("Analyzing..."):
        brandkit_bytes = brandkit_file.read()
        image_bytes = image_file.read()

        files = {
            "brandkit": ("Neurons_brand_kit.pdf", brandkit_bytes, "application/pdf"),
            "image": ("ad_image.png", image_bytes, "image/png"),
        }
        try:
            response = requests.post(f"{BACKEND_URL}/get_score", files=files, timeout=30)
            response.raise_for_status()
            result = response.json()
        except Exception as e:
            st.error(f"Error calling backend: {e}")
            st.stop()

        score = result.get("score", None)
        reasoning = result.get("reasoning", {})

        if score is not None:
            st.metric(label="Compliance Score", value=f"{score} / 4")
        else:
            st.error("No score returned from server.")
            st.stop()

        df = pd.DataFrame.from_dict(reasoning, orient="index", columns=["Detail"])
        df.index.name = "Element"
        st.table(df)

        try:
            ad_image = Image.open(io.BytesIO(image_bytes))
            st.image(ad_image, caption="Uploaded Ad Preview", use_container_width=True)
        except Exception as e:
            st.warning(f"Could not display ad image: {e}")