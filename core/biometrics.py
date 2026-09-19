from PIL import Image, ImageOps
import cv2
import numpy as np
import os
import requests

def download_file(url, filename):
    print(f"Downloading {filename} from Git LFS...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

def ensure_models_exist():
    yunet_url = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
    sface_url = "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx"
    
    if not os.path.exists("yunet.onnx") or os.path.getsize("yunet.onnx") < 100000:
        download_file(yunet_url, "yunet.onnx")
        
    if not os.path.exists("sface.onnx") or os.path.getsize("sface.onnx") < 100000:
        download_file(sface_url, "sface.onnx")

def get_face_feature(image_path):
    try:
        # Auto-rotate smartphone photos based on EXIF orientation
        pil_img = Image.open(image_path)
        pil_img = ImageOps.exif_transpose(pil_img).convert('RGB')
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    except Exception:
        img = cv2.imread(image_path)

    if img is None:
        return None, None

    # Resize massive camera images to speed up and stabilize detection
    max_dim = 1280
    h, w = img.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / float(max(h, w))
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    height, width = img.shape[:2]

    # Initialize YuNet with score threshold = 0.6 for reliable detection
    detector = cv2.FaceDetectorYN.create(
        model="yunet.onnx",
        config="",
        input_size=(width, height),
        score_threshold=0.6,
        nms_threshold=0.3,
        top_k=5000
    )
    
    _, faces = detector.detect(img)
    if faces is None or len(faces) == 0:
        return None, None
        
    face = faces[0]
    recognizer = cv2.FaceRecognizerSF.create("sface.onnx", "")
    aligned_face = recognizer.alignCrop(img, face)
    feature = recognizer.feature(aligned_face)
    
    return feature, recognizer

def analyze_face(passport_path: str, selfie_path: str = None) -> dict:
    result = {
        "photo_extracted": False,
        "face_match_performed": False,
        "similarity_score": 0.0,
        "status": "NOT_CHECKED",
        "evidence": []
    }

    try:
        ensure_models_exist()
        
        pass_feature, recognizer = get_face_feature(passport_path)
        if pass_feature is None:
            result["evidence"].append({
                "code": "BIO_NO_FACE_DETECTED",
                "field": "photograph",
                "description": "Could not detect a valid human face in the passport.",
                "severity": "MEDIUM"
            })
            return result

        result["photo_extracted"] = True

        if selfie_path:
            result["face_match_performed"] = True
            selfie_feature, _ = get_face_feature(selfie_path)
            
            if selfie_feature is None:
                result["status"] = "DETECTION_FAILED"
                result["evidence"].append({
                    "code": "BIO_NO_SELFIE_FACE",
                    "field": "reference_photo",
                    "description": "Could not detect a clear face in the reference selfie.",
                    "severity": "MEDIUM"
                })
                return result

            score = recognizer.match(pass_feature, selfie_feature, cv2.FaceRecognizerSF_FR_COSINE)
            similarity = float(round(max(0.0, score), 3))
            result["similarity_score"] = similarity

            if score >= 0.363:
                result["status"] = "MATCH"
            else:
                result["status"] = "MISMATCH"
                result["evidence"].append({
                    "code": "BIO_FACE_MISMATCH",
                    "field": "photograph",
                    "description": f"Passport photo and live selfie do not match (Similarity: {similarity}).",
                    "severity": "HIGH"
                })
        else:
            result["status"] = "FACE_DETECTED_NO_REFERENCE"

    except Exception as e:
        print(f"Biometric Error: {e}")
        result["status"] = "ERROR"

    return result