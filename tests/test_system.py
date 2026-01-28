"""
Test suite for the Contract Clause Detection System
"""

import pytest
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.database import (
    init_db,
    get_session,
    Contract,
    Clause,
    ClauseType,
    RiskLevel,
)
from sqlalchemy import create_engine


@pytest.fixture
def test_db():
    """Create a test database"""
    engine = create_engine("sqlite:///:memory:")
    from models.database import Base

    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def test_session(test_db):
    """Create a test database session"""
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=test_db)
    session = Session()
    yield session
    session.close()


class TestDatabase:
    """Test database models"""

    def test_create_contract(self, test_session):
        """Test creating a contract"""
        contract = Contract(name="Test Contract", version="1.0", is_amendment=False)
        test_session.add(contract)
        test_session.commit()

        assert contract.id is not None
        assert contract.name == "Test Contract"

    def test_create_clause(self, test_session):
        """Test creating a clause"""
        contract = Contract(name="Test Contract", version="1.0")
        test_session.add(contract)
        test_session.commit()

        clause = Clause(
            contract_id=contract.id,
            text="This is a test clause.",
            clause_type=ClauseType.GENERAL,
            risk_level=RiskLevel.LOW,
            section_number="1.1",
        )
        test_session.add(clause)
        test_session.commit()

        assert clause.id is not None
        assert clause.text == "This is a test clause."
        assert clause.contract_id == contract.id


class TestClauseExtractor:
    """Test clause extraction functionality"""

    def test_text_normalization(self):
        """Test text normalization"""
        from extractors.clause_extractor import ClauseExtractor

        extractor = ClauseExtractor()
        text = "  This   is  a   TEST!  "
        normalized = extractor._normalize_text(text)

        assert normalized == "this is a test"

    def test_clause_type_mapping(self):
        """Test clause type mapping"""
        from extractors.clause_extractor import ClauseExtractor

        extractor = ClauseExtractor()

        assert extractor._map_clause_type("OBLIGATION") == ClauseType.OBLIGATION
        assert extractor._map_clause_type("GENERAL") == ClauseType.GENERAL
        assert extractor._map_clause_type("INVALID") == ClauseType.GENERAL


class TestDocumentParser:
    """Test document parsing"""

    def test_section_identification(self):
        """Test section identification"""
        from extractors.document_parser import StructureAnalyzer

        text = """
        1. First Section
        This is content.
        
        2. Second Section
        More content here.
        
        2.1 Subsection
        Subsection content.
        """

        sections = StructureAnalyzer.identify_sections(text)
        assert len(sections) > 0


class TestConflictDetector:
    """Test conflict detection"""

    def test_contradiction_check(self, test_session):
        """Test contradiction detection"""
        from analyzers.conflict_detector import ConflictDetector

        detector = ConflictDetector(test_session)

        text1 = "The party shall provide services."
        text2 = "The party shall not provide services."

        score = detector._check_contradiction(text1, text2)
        assert score > 0.5  # Should detect contradiction


class TestAmbiguityDetector:
    """Test ambiguity detection"""

    def test_ambiguous_terms_detection(self, test_session):
        """Test detection of ambiguous terms"""
        from analyzers.ambiguity_detector import AmbiguityDetector

        contract = Contract(name="Test", version="1.0")
        test_session.add(contract)
        test_session.commit()

        clause = Clause(
            contract_id=contract.id,
            text="The party shall use reasonable efforts to complete the task.",
            clause_type=ClauseType.OBLIGATION,
            risk_level=RiskLevel.LOW,
        )
        test_session.add(clause)
        test_session.commit()

        detector = AmbiguityDetector(test_session)
        has_ambiguity, issues, score = detector.analyze_clause(clause)

        assert has_ambiguity == True
        assert score > 0


class TestReviewWorkflow:
    """Test review workflow"""

    def test_assign_review(self, test_session):
        """Test assigning a review"""
        from workflows.review_workflow import ReviewWorkflow

        # Create test data
        contract = Contract(name="Test", version="1.0")
        test_session.add(contract)
        test_session.commit()

        clause = Clause(
            contract_id=contract.id,
            text="Test clause",
            clause_type=ClauseType.GENERAL,
            risk_level=RiskLevel.MEDIUM,
        )
        test_session.add(clause)
        test_session.commit()

        # Assign review
        workflow = ReviewWorkflow(test_session)
        review = workflow.assign_for_review(
            clause_id=clause.id,
            reviewer_name="Test Reviewer",
            reviewer_email="test@example.com",
        )

        assert review.id is not None
        assert review.reviewer_name == "Test Reviewer"


def test_health_check():
    """Test API health check"""
    from app import app

    client = app.test_client()
    response = client.get("/health")

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
