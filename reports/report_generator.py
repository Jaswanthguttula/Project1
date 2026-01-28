"""
Report generation for audit-friendly exports (JSON-only fallback)
"""

import json
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from models.database import (
    Contract,
    Clause,
    Conflict,
    ClauseReview,
    DecisionLog,
    Interpretation,
    RiskLevel,
)


class AuditReportGenerator:
    """Generate comprehensive audit reports (JSON format)"""

    def __init__(self, session: Session):
        self.session = session

    def generate_pdf_report(self, contract_id: int, output_path: str) -> str:
        """
        Generate a PDF audit report.
        Note: PDF generation requires reportlab. For now, JSON export is available.
        """
        print("Note: PDF export is not available. Generating JSON report instead.")
        json_path = output_path.replace(".pdf", ".json")
        return self.generate_json_report(contract_id, json_path)

    def generate_json_report(self, contract_id: int, output_path: str) -> str:
        """Generate a JSON audit report"""
        contract = self.session.query(Contract).filter_by(id=contract_id).first()
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")

        # Gather all data
        clauses = self.session.query(Clause).filter_by(contract_id=contract_id).all()
        conflicts = (
            self.session.query(Conflict)
            .join(Clause, Clause.id == Conflict.clause_id)
            .filter(Clause.contract_id == contract_id)
            .all()
        )
        reviews = (
            self.session.query(ClauseReview)
            .join(Clause, Clause.id == ClauseReview.clause_id)
            .filter(Clause.contract_id == contract_id)
            .all()
        )

        # Build report structure
        report = {
            "report_date": datetime.utcnow().isoformat(),
            "contract": {
                "id": contract.id,
                "name": contract.name,
                "version": contract.version,
                "file_path": contract.file_path,
                "is_amendment": contract.is_amendment,
                "created_at": contract.created_at.isoformat()
                if contract.created_at
                else None,
                "updated_at": contract.updated_at.isoformat()
                if contract.updated_at
                else None,
            },
            "summary": {
                "total_clauses": len(clauses),
                "clauses_by_type": self._count_by_type(clauses),
                "high_risk_count": sum(
                    1
                    for c in clauses
                    if c.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
                ),
                "conflicts_detected": len(conflicts),
                "reviews_pending": sum(
                    1 for r in reviews if r.status.value == "PENDING"
                ),
            },
            "clauses": [
                {
                    "id": c.id,
                    "section": c.section_number,
                    "title": c.title,
                    "text": c.text[:200] + "..." if len(c.text) > 200 else c.text,
                    "type": c.clause_type.value if c.clause_type else None,
                    "risk_level": c.risk_level.value if c.risk_level else None,
                    "page": c.page_number,
                }
                for c in clauses
            ],
            "conflicts": [
                {
                    "id": cf.id,
                    "clause_id": cf.clause_id,
                    "conflicting_clause_id": cf.conflicting_clause_id,
                    "type": cf.conflict_type,
                    "severity": cf.severity.value if cf.severity else None,
                    "confidence": cf.confidence_score,
                    "is_resolved": cf.is_resolved,
                }
                for cf in conflicts
            ],
            "reviews": [
                {
                    "id": r.id,
                    "clause_id": r.clause_id,
                    "status": r.status.value if r.status else None,
                    "reviewer": r.reviewer_name,
                    "assigned_at": r.assigned_at.isoformat() if r.assigned_at else None,
                    "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
                }
                for r in reviews
            ],
        }

        # Write JSON
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        return output_path

    def _count_by_type(self, clauses: List[Clause]) -> Dict[str, int]:
        """Count clauses by type"""
        counts = {}
        for clause in clauses:
            clause_type = clause.clause_type.value if clause.clause_type else "UNKNOWN"
            counts[clause_type] = counts.get(clause_type, 0) + 1
        return counts
