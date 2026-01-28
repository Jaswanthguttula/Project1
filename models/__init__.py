"""
Models package initialization
"""

from .database import (
    Base,
    Contract,
    Clause,
    Conflict,
    Interpretation,
    ClauseReview,
    DecisionLog,
    QuestionAnswer,
    ClauseType,
    RiskLevel,
    ReviewStatus,
    init_db,
    get_session,
)

from .schemas import (
    ClauseTypeEnum,
    RiskLevelEnum,
    ReviewStatusEnum,
    ContractUploadRequest,
    QuestionRequest,
    ReviewSubmissionRequest,
    DecisionLogRequest,
    ClauseResponse,
    ConflictResponse,
    EvidenceClause,
    AnswerResponse,
    ContractResponse,
    ExtractionResult,
    ConflictAnalysisResult,
    ReviewWorkflowStatus,
    AuditReportRequest,
)

__all__ = [
    # Database models
    "Base",
    "Contract",
    "Clause",
    "Conflict",
    "Interpretation",
    "ClauseReview",
    "DecisionLog",
    "QuestionAnswer",
    "ClauseType",
    "RiskLevel",
    "ReviewStatus",
    "init_db",
    "get_session",
    # Pydantic schemas
    "ClauseTypeEnum",
    "RiskLevelEnum",
    "ReviewStatusEnum",
    "ContractUploadRequest",
    "QuestionRequest",
    "ReviewSubmissionRequest",
    "DecisionLogRequest",
    "ClauseResponse",
    "ConflictResponse",
    "EvidenceClause",
    "AnswerResponse",
    "ContractResponse",
    "ExtractionResult",
    "ConflictAnalysisResult",
    "ReviewWorkflowStatus",
    "AuditReportRequest",
]
