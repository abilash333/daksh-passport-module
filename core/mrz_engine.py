import pytesseract
from passporteye import read_mrz

# Tell the backend exactly where Tesseract lives
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def calculate_check_digit(data: str) -> int:
    weights = [7, 3, 1]
    total = 0
    for i, char in enumerate(data):
        if char == '<':
            val = 0
        elif char.isdigit():
            val = int(char)
        elif char.isalpha():
            val = ord(char.upper()) - 55
        else:
            val = 0
        total += val * weights[i % 3]
    return total % 10

def parse_and_validate_mrz(image_path: str) -> dict:
    mrz_record = read_mrz(image_path)
    if not mrz_record:
        return {
            "mrz_detected": False,
            "mrz_checksum_valid": False,
            "parsed_fields": {},
            "evidence": [{
                "code": "MRZ_NOT_FOUND",
                "field": "mrz",
                "description": "No machine-readable zone could be detected or decoded.",
                "severity": "MEDIUM"
            }]
        }

    data = mrz_record.to_dict()
    evidence = []
    checksum_passed = True

    # Validate Passport Number Check Digit if raw string is available
    raw_pass = data.get("raw_number", "")
    pass_check = data.get("number_check", "")
    if raw_pass and pass_check:
        if str(calculate_check_digit(raw_pass)) != str(pass_check):
            checksum_passed = False
            evidence.append({
                "code": "MRZ_CHECKSUM_FAIL_DOC_NUMBER",
                "field": "passport_number",
                "description": "MRZ document number check digit mismatch.",
                "severity": "HIGH"
            })

    # Validate Date of Birth Check Digit (YYMMDD format)
    raw_dob = data.get("date_of_birth", "")
    dob_check = data.get("date_of_birth_check", "")
    if raw_dob and dob_check:
        if str(calculate_check_digit(raw_dob)) != str(dob_check):
            checksum_passed = False
            evidence.append({
                "code": "MRZ_CHECKSUM_FAIL_DOB",
                "field": "dob",
                "description": "MRZ date of birth check digit mismatch.",
                "severity": "HIGH"
            })

    return {
        "mrz_detected": True,
        "mrz_checksum_valid": checksum_passed,
        "parsed_fields": {
            "passport_number": data.get("number"),
            "surname": data.get("surname"),
            "names": data.get("names"),
            "nationality": data.get("nationality"),
            "dob": data.get("date_of_birth"),
            "expiry_date": data.get("expiration_date"),
            "gender": data.get("sex")
        },
        "evidence": evidence
    }