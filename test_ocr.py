import json
from core.visual_ocr import extract_visual_fields

def run_test():
    image_path = "test_passport.jpg" 
    
    print(f"\n🔍 Running Visual OCR extraction on {image_path}...\n")
    
    try:
        result = extract_visual_fields(image_path)
        
        # Print just the structured fields to keep the terminal clean
        print("\n✅ Extracted Structured Fields:")
        print(json.dumps(result["fields"], indent=2))
        
        print(f"\n✅ Extracted {len(result['text_blocks'])} total text blocks from the image.")
            
    except Exception as e:
        print(f"❌ ERROR during execution: {e}")

if __name__ == "__main__":
    run_test()