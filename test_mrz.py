import json
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
from core.mrz_engine import parse_and_validate_mrz

def run_test():
    image_path = "test_passport.jpg" 
    
    print(f"🔍 Running MRZ extraction on {image_path}...\n")
    
    try:
        # Run the engine we just built
        result = parse_and_validate_mrz(image_path)
        
        # Print the output formatted nicely
        print(json.dumps(result, indent=2))
        
        if result.get("mrz_checksum_valid"):
            print("\n✅ SUCCESS: The MRZ was parsed and the ICAO math checksums passed!")
        else:
            print("\n⚠️ WARNING: MRZ was parsed, but check digits failed. (This is normal if the sample image is a bad fake).")
            
    except FileNotFoundError:
        print(f"❌ ERROR: Could not find '{image_path}'. Did you save the sample image in the right folder?")
    except Exception as e:
        print(f"❌ ERROR during execution: {e}")

if __name__ == "__main__":
    run_test()