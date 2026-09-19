import streamlit as st
import requests
from PIL import Image, ImageDraw

st.set_page_config(page_title="DAKSH - Passport Module", layout="wide")
st.title("🛂 DAKSH: Passport Screening Module")
st.markdown("Upload a passport image to run OCR, MRZ Validation, Image Forensics, and Biometrics.")

# Dual file uploader side-by-side
col_up1, col_up2 = st.columns(2)
with col_up1:
    uploaded_file = st.file_uploader("Upload Passport Image (JPG/PNG)", type=["jpg", "jpeg", "png"])
with col_up2:
    selfie_file = st.file_uploader("Upload Reference Selfie (Optional)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Original Document")
        image = Image.open(uploaded_file)
        st.image(image, use_container_width=True)
        
        if selfie_file is not None:
            st.subheader("Reference Selfie")
            selfie_img = Image.open(selfie_file)
            st.image(selfie_img, width=220)

    with st.spinner("Running AI Analysis, Forensics & Biometrics..."):
        uploaded_file.seek(0)
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "image/jpeg")}
        
        if selfie_file is not None:
            selfie_file.seek(0)
            files["selfie"] = (selfie_file.name, selfie_file.getvalue(), "image/jpeg")
        
        try:
            response = requests.post("http://127.0.0.1:8000/api/modules/passport", files=files)
            
            if response.status_code == 200:
                result = response.json()
                
                with col2:
                    st.subheader("Screening Results")
                    
                    # Review Priority Badge
                    if any(ev.get("severity") == "HIGH" for ev in result.get("evidence", [])):
                        st.error("🚨 HIGH REVIEW PRIORITY")
                    else:
                        st.success("✅ LOW CONCERN")
                        
                    # Extracted OCR Fields
                    st.markdown("### 📄 Extracted Fields (OCR)")
                    for key, val in result.get("fields", {}).items():
                        st.write(f"**{key.upper()}:** {val['value']} *(Confidence: {val['confidence']:.2f})*")

                    # MRZ Validation
                    st.markdown("### 🔢 MRZ Validation")
                    val_data = result.get("validation", {})
                    st.write(f"- **MRZ Detected:** {'✅' if val_data.get('mrz_detected') else '❌'}")
                    st.write(f"- **Checksum Valid:** {'✅' if val_data.get('mrz_checksum_valid') else '❌'}")
                    st.write(f"- **VIZ vs MRZ Consistent:** {'✅' if val_data.get('viz_mrz_consistent') else '❌'}")
                    
                    # Biometrics
                    st.markdown("### 👤 Biometric Verification")
                    bio_data = result.get("biometric", {})
                    st.write(f"- **Document Face Detected:** {'✅' if bio_data.get('photo_extracted') else '❌'}")
                    if bio_data.get("face_match_performed"):
                        status = bio_data.get("status")
                        score = bio_data.get("similarity_score", 0.0)
                        if status == "MATCH":
                            st.success(f"Face Match: MATCH (Similarity: {score})")
                        elif status == "MISMATCH":
                            st.error(f"Face Match: MISMATCH (Similarity: {score})")
                        else:
                            st.warning("Face Verification: Unable to detect face in selfie image.")
                    else:
                        st.info("No selfie provided for 1:1 face verification.")

                    # Evidence & Contradictions
                    st.markdown("### 🔍 Evidence & Contradictions")
                    evidence_items = result.get("evidence", [])
                    if not evidence_items:
                        st.info("No contradictions or anomalies found.")
                    for ev in evidence_items:
                        if ev.get("severity") == "HIGH":
                            st.error(f"**{ev.get('code')}**: {ev.get('description')}")
                        else:
                            st.warning(f"**{ev.get('code')}**: {ev.get('description')}")

                # Forensic Bounding Boxes
                st.markdown("---")
                st.subheader("Forensic Pixel Analysis (ELA)")
                forensics = result.get("forensics", {})
                if forensics.get("ela_anomaly_detected"):
                    st.warning(f"Detected {len(forensics.get('suspicious_regions', []))} suspicious regions.")
                    annotated_image = image.copy()
                    draw = ImageDraw.Draw(annotated_image)
                    
                    for region in forensics.get("suspicious_regions", []):
                        ymin, xmin, ymax, xmax = region["bbox"]
                        color = "red" if region.get("severity") == "HIGH" else "orange"
                        draw.rectangle([xmin, ymin, xmax, ymax], outline=color, width=3)
                        
                    st.image(annotated_image, caption="Tampered Regions Highlighted", use_container_width=True)
                else:
                    st.success("No localized pixel tampering detected.")
            else:
                st.error(f"Server returned error code: {response.status_code}")
                st.write(response.text)
                    
        except requests.exceptions.ConnectionError:
            st.error("❌ Could not connect to the backend API. Is FastAPI running on port 8000?")