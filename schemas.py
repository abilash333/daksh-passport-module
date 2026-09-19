from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class FieldValue(BaseModel):
    value: str
    confidence: float

class ValidationDetail(BaseModel):
    field: str
    viz_value: Optional[str] = None
    mrz_value: Optional[str] = None
    status: str  # MATCH, CONTRADICTION, INVALID_CHECKSUM

class ValidationResult(BaseModel):
    mrz_detected: bool
    mrz_checksum_valid: bool
    viz_mrz_consistent: bool
    details: List[ValidationDetail] = []

class TamperRegion(BaseModel):
    bbox: List[int]  # [ymin, xmin, ymax, xmax]
    area: int
    severity: str    # HIGH, MEDIUM

class ForensicsResult(BaseModel):
    metadata_flags: List[str] = []
    ela_anomaly_detected: bool
    suspicious_regions: List[TamperRegion] = []

class EvidenceItem(BaseModel):
    code: str
    field: Optional[str] = None
    description: str
    severity: str    # LOW, MEDIUM, HIGH

class BiometricResult(BaseModel):
    photo_extracted: bool
    face_match_performed: bool
    similarity_score: float
    status: str

class PassportScreeningResponse(BaseModel):
    case_id: str
    document_type: str = "passport"
    module_status: str  # COMPLETE, INCONCLUSIVE, FAILED
    fields: Dict[str, FieldValue]
    validation: ValidationResult
    forensics: ForensicsResult
    evidence: List[EvidenceItem]
    biometric: BiometricResult