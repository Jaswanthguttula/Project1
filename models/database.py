"""
Database models for the Contract Clause Detection System
"""

import os

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    ForeignKey,
    Boolean,
    Enum as SQLEnum,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import enum

Base = declarative_base()


class ClauseType(enum.Enum):
    """Enumeration of clause types"""

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


class RiskLevel(enum.Enum):
    """Enumeration of risk levels"""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ReviewStatus(enum.Enum):
    """Review workflow status"""

    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"


class User(Base):
    """User for application authentication"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # flask-login integration
    def get_id(self):
        return str(self.id)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class Contract(Base):
    """Main contract document"""

    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    original_filename = Column(String(255))
    file_path = Column(String(500))
    version = Column(String(50))
    effective_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Is this an amendment or addendum?
    is_amendment = Column(Boolean, default=False)
    parent_contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=True)

    # Relationships
    parent_contract = relationship("Contract", remote_side=[id], backref="amendments")
    clauses = relationship(
        "Clause", back_populates="contract", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Contract(id={self.id}, name='{self.name}', version='{self.version}')>"


class Clause(Base):
    """Individual clause within a contract"""

    __tablename__ = "clauses"

    id = Column(Integer, primary_key=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)

    # Reference information
    section_number = Column(String(50))  # e.g., "5.2.1"
    clause_path = Column(String(500))  # Full hierarchical path
    title = Column(String(500))

    # Content
    text = Column(Text, nullable=False)
    normalized_text = Column(Text)  # Cleaned version for comparison

    # Classification
    clause_type = Column(SQLEnum(ClauseType), default=ClauseType.GENERAL)
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.LOW)

    # Metadata
    page_number = Column(Integer)
    position_in_document = Column(Integer)
    extracted_at = Column(DateTime, default=datetime.utcnow)

    # Embedding for semantic search
    embedding_vector = Column(Text)  # Stored as JSON string

    # Relationships
    contract = relationship("Contract", back_populates="clauses")
    conflicts = relationship(
        "Conflict", foreign_keys="Conflict.clause_id", back_populates="clause"
    )
    reviews = relationship(
        "ClauseReview", back_populates="clause", cascade="all, delete-orphan"
    )
    interpretations = relationship(
        "Interpretation", back_populates="clause", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Clause(id={self.id}, section='{self.section_number}', type={self.clause_type.value})>"


class Conflict(Base):
    """Detected conflicts between clauses"""

    __tablename__ = "conflicts"

    id = Column(Integer, primary_key=True)
    clause_id = Column(Integer, ForeignKey("clauses.id"), nullable=False)
    conflicting_clause_id = Column(Integer, ForeignKey("clauses.id"), nullable=False)

    # Conflict details
    conflict_type = Column(
        String(100)
    )  # e.g., "OVERRIDE", "CONTRADICTION", "AMBIGUITY"
    description = Column(Text)
    severity = Column(SQLEnum(RiskLevel), default=RiskLevel.MEDIUM)
    confidence_score = Column(Float)  # 0.0 to 1.0

    # Resolution
    is_resolved = Column(Boolean, default=False)
    resolution_notes = Column(Text)
    resolved_by = Column(String(255))
    resolved_at = Column(DateTime)

    detected_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    clause = relationship(
        "Clause", foreign_keys=[clause_id], back_populates="conflicts"
    )
    conflicting_clause = relationship("Clause", foreign_keys=[conflicting_clause_id])

    def __repr__(self):
        return f"<Conflict(id={self.id}, type='{self.conflict_type}', severity={self.severity.value})>"


class Interpretation(Base):
    """AI-generated or human interpretations of clauses"""

    __tablename__ = "interpretations"

    id = Column(Integer, primary_key=True)
    clause_id = Column(Integer, ForeignKey("clauses.id"), nullable=False)

    # Interpretation content
    interpretation_text = Column(Text, nullable=False)
    reasoning = Column(Text)  # Why this interpretation was made

    # Metadata
    is_ai_generated = Column(Boolean, default=True)
    created_by = Column(String(255))  # User ID or 'AI'
    created_at = Column(DateTime, default=datetime.utcnow)

    # Risk assessment
    has_ambiguity = Column(Boolean, default=False)
    ambiguity_details = Column(Text)
    requires_legal_review = Column(Boolean, default=False)

    # Relationships
    clause = relationship("Clause", back_populates="interpretations")

    def __repr__(self):
        return f"<Interpretation(id={self.id}, clause_id={self.clause_id}, ai={self.is_ai_generated})>"


class ClauseReview(Base):
    """Legal review workflow for clauses"""

    __tablename__ = "clause_reviews"

    id = Column(Integer, primary_key=True)
    clause_id = Column(Integer, ForeignKey("clauses.id"), nullable=False)

    # Review details
    status = Column(SQLEnum(ReviewStatus), default=ReviewStatus.PENDING)
    reviewer_name = Column(String(255))
    reviewer_email = Column(String(255))

    # Feedback
    comments = Column(Text)
    suggested_changes = Column(Text)
    approved_interpretation = Column(Text)

    # Timestamps
    assigned_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime)

    # Relationships
    clause = relationship("Clause", back_populates="reviews")
    decision_logs = relationship(
        "DecisionLog", back_populates="review", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ClauseReview(id={self.id}, status={self.status.value}, reviewer='{self.reviewer_name}')>"


class DecisionLog(Base):
    """Audit trail of decisions made during review"""

    __tablename__ = "decision_logs"

    id = Column(Integer, primary_key=True)
    review_id = Column(Integer, ForeignKey("clause_reviews.id"), nullable=False)

    # Decision details
    action = Column(String(100))  # e.g., "APPROVED", "FLAGGED", "CLARIFIED"
    decision_text = Column(Text, nullable=False)
    rationale = Column(Text)

    # Context
    previous_state = Column(String(50))
    new_state = Column(String(50))

    # Metadata
    made_by = Column(String(255), nullable=False)
    made_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    review = relationship("ClauseReview", back_populates="decision_logs")

    def __repr__(self):
        return (
            f"<DecisionLog(id={self.id}, action='{self.action}', by='{self.made_by}')>"
        )


class QuestionAnswer(Base):
    """Stored question-answer pairs with evidence"""

    __tablename__ = "question_answers"

    id = Column(Integer, primary_key=True)

    # Question
    question = Column(Text, nullable=False)
    question_embedding = Column(Text)  # For semantic search

    # Answer
    answer = Column(Text, nullable=False)
    confidence_score = Column(Float)

    # Evidence (stored as JSON with clause IDs and relevance scores)
    evidence_clauses = Column(Text)  # JSON: [{"clause_id": 1, "relevance": 0.95}, ...]

    # Metadata
    asked_by = Column(String(255))
    asked_at = Column(DateTime, default=datetime.utcnow)
    contract_id = Column(Integer, ForeignKey("contracts.id"))

    def __repr__(self):
        return f"<QuestionAnswer(id={self.id}, confidence={self.confidence_score})>"


# Database initialization
def init_db(database_url="sqlite:///./contracts.db"):
    """Initialize the database"""
    echo = os.getenv("SQLALCHEMY_ECHO", "False").lower() == "true"
    engine = create_engine(database_url, echo=echo)
    Base.metadata.create_all(engine)
    return engine


def get_session(engine):
    """Get a database session"""
    Session = sessionmaker(bind=engine)
    return Session()
