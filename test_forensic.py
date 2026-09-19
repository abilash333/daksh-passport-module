import json
from core.forensic import analyze_forensics

def run_test():
    image_path = "test_passport.jpg" 
    
    print(f"\n🔍 Running Pixel Forensics & ELA on {image_path}...\n")
    
    try:
        result = analyze_forensics(image_path)
        print(json.dumps(result, indent=2))
        
        if result.get("ela_anomaly_detected"):
            print(f"\n🚨 ALERT: Found {len(result['suspicious_regions'])} suspicious edited region(s)!")
        else:
            print("\n✅ CLEAN: No significant pixel tampering detected.")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    run_test()