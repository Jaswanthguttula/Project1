"""
Pydantic models for API request/response validation
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ClauseTypeEnum(str, Enum):
    OBLIGATION = "OBLIGATION"
    EXCLUSION = "EXCLUSION"
    TERMINATION = "TERMINATION"
    LIABILITY = "LIABILITY"
    PAYMENT = "PAYMENT"
    CONFIDENTIALITY = "CONFIDENTIALITY"
    INTELLECTUAL_PROPERTY = "INTELLECTUAL_PROPERTY"
    WARRANTY = "WARRANTY"
    INDEMNIFICATION = "INDEMNIFICATION"
    FORCE_MAJEURE = "FORCE_MAJEURE"
    DISPUTE_RESOLUTION = "DISPUTE_RESOLUTION"
    AMENDMENT = "AMENDMENT"
    GENERAL = "GENERAL"


class RiskLevelEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ReviewStatusEnum(str, Enum):
    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"


# Request Models
class ContractUploadRequest(BaseModel):
    name: str
    version: Optional[str] = "1.0"
    effective_date: Optional[datetime] = None
    is_amendment: bool = False
    parent_contract_id: Optional[int] = None


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=1000)
    contract_id: Optional[int] = None
    asked_by: Optional[str] = "anonymous"


class ReviewSubmissionRequest(BaseModel):
    clause_id: int
    status: ReviewStatusEnum
    reviewer_name: str
    reviewer_email: str
    comments: Optional[str] = None
    suggested_changes: Optional[str] = None
    approved_interpretation: Optional[str] = None


class DecisionLogRequest(BaseModel):
    review_id: int
    action: str
    decision_text: str
    rationale: Optional[str] = None
    made_by: str


# Response Models
class ClauseResponse(BaseModel):
    id: int
    section_number: Optional[str]
    clause_path: Optional[str]
    title: Optional[str]
    text: str
    clause_type: ClauseTypeEnum
    risk_level: RiskLevelEnum
    page_number: Optional[int]

    class Config:
        from_attributes = True


class ConflictResponse(BaseModel):
    id: int
    clause_id: int
    conflicting_clause_id: int
    conflict_type: str
    description: str
    severity: RiskLevelEnum
    confidence_score: float
    is_resolved: bool

    class Config:
        from_attributes = True


class EvidenceClause(BaseModel):
    clause_id: int
    section_number: Optional[str]
    text: str
    relevance_score: float
    clause_type: ClauseTypeEnum
    document_name: str
    page_number: Optional[int]


class AnswerResponse(BaseModel):
    answer: str
    confidence: float
    evidence_clauses: List[EvidenceClause]
    ambiguities: List[str] = []
    conflicts: List[ConflictResponse] = []
    requires_review: bool = False


class ContractResponse(BaseModel):
    id: int
    name: str
    version: Optional[str]
    effective_date: Optional[datetime]
    is_amendment: bool
    created_at: datetime
    clause_count: int
    high_risk_clause_count: int

    class Config:
        from_attributes = True


class ExtractionResult(BaseModel):
    contract_id: int
    total_clauses: int
    clauses_by_type: Dict[str, int]
    high_risk_count: int
    extraction_time: float


class ConflictAnalysisResult(BaseModel):
    total_conflicts: int
    by_severity: Dict[str, int]
    unresolved_conflicts: List[ConflictResponse]


class ReviewWorkflowStatus(BaseModel):
    total_clauses: int
    pending_review: int
    in_review: int
    approved: int
    rejected: int
    needs_clarification: int


class AuditReportRequest(BaseModel):
    contract_ids: List[int]
    include_conflicts: bool = True
    include_decisions: bool = True
    include_reviews: bool = True
    format: str = "pdf"  # pdf, json, excel
