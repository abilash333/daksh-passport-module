import easyocr
import re

# Initialize the EasyOCR reader (this runs once when the app starts)
# It uses deep learning to find text anywhere on the image.
print("Loading OCR Engine... (This may take a minute on the first run)")
reader = easyocr.Reader(['en'], gpu=False) 

def extract_visual_fields(image_path: str) -> dict:
    # Extract text, bounding boxes, and confidence scores
    results = reader.readtext(image_path)
    
    # Store all raw text to search through
    full_text = " ".join([res[1] for res in results])
    
    # Extract dates using Regex (looking for DD/MM/YYYY or DD-MM-YYYY)
    date_pattern = r'\b\d{2}[/-]\d{2}[/-]\d{4}\b'
    found_dates = re.findall(date_pattern, full_text)
    
    # Extract potential Passport Numbers (typically 1 letter followed by 7 digits in India, but varies)
    passport_pattern = r'\b[A-Z]{1,2}[0-9]{7}\b'
    found_passports = re.findall(passport_pattern, full_text)

    # Format the output to match our P6 data contract
    extracted_data = {
        "raw_text": full_text,
        "fields": {},
        "text_blocks": []
    }
    
    # Assign found data to our standardized fields
    if found_passports:
        extracted_data["fields"]["passport_number"] = {
            "value": found_passports[0],
            "confidence": 0.85 # Estimated confidence for regex match
        }
        
    if len(found_dates) >= 2:
        # Passports usually have DOB and Expiry. 
        # We sort them: the older date is DOB, newer is Expiry.
        found_dates.sort(key=lambda x: int(x[-4:])) 
        extracted_data["fields"]["dob"] = {
            "value": found_dates[0],
            "confidence": 0.90
        }
        extracted_data["fields"]["expiry_date"] = {
            "value": found_dates[-1],
            "confidence": 0.90
        }

    # Save bounding boxes for the frontend visualization
    for (bbox, text, prob) in results:
        extracted_data["text_blocks"].append({
            "text": text,
            "confidence": float(prob),
            # Convert float coordinates to integers for JSON serialization
            "bbox": [[int(coord) for coord in pt] for pt in bbox] 
        })
        
    return extracted_data