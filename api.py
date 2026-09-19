from fastapi import FastAPI, File, UploadFile
import shutil
import os
import uuid
from typing import Optional

from core.mrz_engine import parse_and_validate_mrz
from core.visual_ocr import extract_visual_fields
from core.forensic import analyze_forensics
from core.biometrics import analyze_face
from schemas import (
    PassportScreeningResponse, 
    FieldValue, 
    ValidationResult, 
    ValidationDetail, 
    ForensicsResult, 
    BiometricResult,
    EvidenceItem
)

app = FastAPI(title="DAKSH - P1 Passport Module")

@app.post("/api/modules/passport", response_model=PassportScreeningResponse)
async def screen_passport(
    file: UploadFile = File(...), 
    selfie: Optional[UploadFile] = File(None)
):
    case_id = f"CASE_PASS_{uuid.uuid4().hex[:8].upper()}"
    temp_path = f"temp_{file.filename}"
    selfie_path = None
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if selfie is not None:
        selfie_path = f"temp_selfie_{selfie.filename}"
        with open(selfie_path, "wb") as buffer:
            shutil.copyfileobj(selfie.file, buffer)

    try:
        # Run all four engines
        mrz_data = parse_and_validate_mrz(temp_path)
        ocr_data = extract_visual_fields(temp_path)
        forensics_data = analyze_forensics(temp_path)
        bio_data = analyze_face(temp_path, selfie_path)

        evidence_list = []
        validation_details = []
        
        # 1. Contradiction Engine (VIZ vs MRZ)
        viz_dob = ocr_data["fields"].get("dob", {}).get("value")
        mrz_dob = mrz_data["parsed_fields"].get("dob")
        viz_mrz_consistent = True 
        
        if viz_dob and mrz_dob:
            viz_year_short = viz_dob[-2:] 
            mrz_year_short = mrz_dob[:2]
            
            if viz_year_short != mrz_year_short:
                viz_mrz_consistent = False
                validation_details.append(
                    ValidationDetail(
                        field="dob",
                        viz_value=viz_dob,
                        mrz_value=mrz_dob,
                        status="CONTRADICTION"
                    )
                )
                evidence_list.append(
                    EvidenceItem(
                        code="EV_VIZ_MRZ_MISMATCH",
                        field="dob",
                        description=f"Printed DOB ({viz_dob}) conflicts with MRZ DOB ({mrz_dob})",
                        severity="HIGH"
                    )
                )

        # 2. Collect MRZ Evidence
        for ev in mrz_data.get("evidence", []):
            evidence_list.append(EvidenceItem(**ev))

        # 3. Collect Forensics Evidence
        if forensics_data["ela_anomaly_detected"]:
            evidence_list.append(
                EvidenceItem(
                    code="EV_FORGERY_LOCALIZED",
                    field="image_pixels",
                    description=f"Detected {len(forensics_data['suspicious_regions'])} suspicious edited regions via ELA.",
                    severity="HIGH"
                )
            )

        # 4. Collect Biometric Evidence
        for ev in bio_data.get("evidence", []):
            evidence_list.append(EvidenceItem(**ev))

        # 5. Build standardized response
        response = PassportScreeningResponse(
            case_id=case_id,
            module_status="COMPLETE",
            fields={k: FieldValue(**v) for k, v in ocr_data["fields"].items()},
            validation=ValidationResult(
                mrz_detected=mrz_data["mrz_detected"],
                mrz_checksum_valid=mrz_data["mrz_checksum_valid"],
                viz_mrz_consistent=viz_mrz_consistent,
                details=validation_details
            ),
            forensics=ForensicsResult(**forensics_data),
            biometric=BiometricResult(
                photo_extracted=bio_data["photo_extracted"],
                face_match_performed=bio_data["face_match_performed"],
                similarity_score=bio_data["similarity_score"],
                status=bio_data["status"]
            ),
            evidence=evidence_list
        )

        return response

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if selfie_path and os.path.exists(selfie_path):
            os.remove(selfie_path)

@app.get("/api/health")
def health_check():
    return {"status": "online", "module": "P1-Passport"}