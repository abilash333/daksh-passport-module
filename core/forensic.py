import cv2
import numpy as np
from PIL import Image, ImageChops, ImageEnhance
import piexif

def analyze_metadata(image_path: str) -> list:
    flags = []
    try:
        exif_dict = piexif.load(image_path)
        # Check the 'Software' tag (0x0131 in the 0th IFD)
        if "0th" in exif_dict and piexif.ImageIFD.Software in exif_dict["0th"]:
            software = exif_dict["0th"][piexif.ImageIFD.Software].decode('utf-8', 'ignore')
            if any(sus in software.lower() for sus in ['photoshop', 'gimp', 'canva', 'paint']):
                flags.append(f"Suspicious Software Metadata: {software}")
    except Exception:
        pass # Many images have no EXIF data, which is fine
    return flags

def run_ela_and_localize(image_path: str, quality: int = 90, threshold: int = 50):
    try:
        # 1. Resave the image at a known quality level
        original = Image.open(image_path).convert('RGB')
        resaved_path = "temp_resaved.jpg"
        original.save(resaved_path, 'JPEG', quality=quality)
        resaved = Image.open(resaved_path)
        
        # 2. Find the pixel differences (edited pixels compress differently)
        ela_diff = ImageChops.difference(original, resaved)
        extrema = ela_diff.getextrema()
        max_diff = max([ex[1] for ex in extrema])
        
        # Amplify the hidden differences so OpenCV can see them
        scale = 255.0 / max_diff if max_diff != 0 else 1.0
        ela_enhanced = ImageEnhance.Brightness(ela_diff).enhance(scale)
        
        # 3. Convert to OpenCV format to draw bounding boxes
        ela_cv = np.array(ela_enhanced)
        gray = cv2.cvtColor(ela_cv, cv2.COLOR_RGB2GRAY)
        
        # Filter out background noise
        _, thresh = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
        
        # Group edited pixels into blocks
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        suspicious_boxes = []
        h_img, w_img = gray.shape
        
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            # Ignore tiny specks and the outer border of the image
            if 30 < w < w_img * 0.9 and 30 < h < h_img * 0.9:
                area = int(w * h)
                suspicious_boxes.append({
                    "bbox": [int(y), int(x), int(y + h), int(x + w)], # ymin, xmin, ymax, xmax
                    "area": area,
                    "severity": "HIGH" if area > 4000 else "MEDIUM"
                })
                
        return True, suspicious_boxes
    except Exception as e:
        print(f"ELA Error: {e}")
        return False, []

def analyze_forensics(image_path: str) -> dict:
    metadata_flags = analyze_metadata(image_path)
    ela_success, regions = run_ela_and_localize(image_path)
    
    return {
        "metadata_flags": metadata_flags,
        "ela_anomaly_detected": len(regions) > 0,
        "suspicious_regions": regions
    }