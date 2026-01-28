"""
Workflow management for legal review process
"""

from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from models.database import (
    Clause,
    ClauseReview,
    DecisionLog,
    Interpretation,
    ReviewStatus,
    RiskLevel,
    Contract,
)
from models.schemas import ReviewWorkflowStatus


class ReviewWorkflow:
    """Manage the legal review workflow for clauses"""

    def __init__(self, session: Session):
        self.session = session

    def assign_for_review(
        self, clause_id: int, reviewer_name: str, reviewer_email: str
    ) -> ClauseReview:
        """
        Assign a clause for legal review

        Returns:
            ClauseReview object
        """
        clause = self.session.query(Clause).filter_by(id=clause_id).first()
        if not clause:
            raise ValueError(f"Clause {clause_id} not found")

        # Check if already in review
        existing_review = (
            self.session.query(ClauseReview)
            .filter_by(clause_id=clause_id, status=ReviewStatus.IN_REVIEW)
            .first()
        )

        if existing_review:
            return existing_review

        review = ClauseReview(
            clause_id=clause_id,
            status=ReviewStatus.IN_REVIEW,
            reviewer_name=reviewer_name,
            reviewer_email=reviewer_email,
            assigned_at=datetime.utcnow(),
        )

        self.session.add(review)

        # Log the assignment
        self._create_decision_log(
            review=review,
            action="ASSIGNED",
            decision_text=f"Clause assigned to {reviewer_name} for review",
            made_by="SYSTEM",
        )

        self.session.commit()

        return review

    def batch_assign_high_risk(
        self, contract_id: int, reviewer_name: str, reviewer_email: str
    ) -> List[ClauseReview]:
        """
        Automatically assign all high-risk clauses for review

        Returns:
            List of ClauseReview objects
        """
        contract = self.session.query(Contract).filter_by(id=contract_id).first()
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")

        high_risk_clauses = (
            self.session.query(Clause)
            .filter(
                Clause.contract_id == contract_id,
                Clause.risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL]),
            )
            .all()
        )

        reviews = []
        for clause in high_risk_clauses:
            try:
                review = self.assign_for_review(
                    clause.id, reviewer_name, reviewer_email
                )
                reviews.append(review)
            except Exception as e:
                print(f"Error assigning clause {clause.id}: {e}")

        return reviews

    def submit_review(
        self,
        review_id: int,
        status: ReviewStatus,
        comments: Optional[str] = None,
        suggested_changes: Optional[str] = None,
        approved_interpretation: Optional[str] = None,
    ) -> ClauseReview:
        """
        Submit a review decision

        Returns:
            Updated ClauseReview object
        """
        review = self.session.query(ClauseReview).filter_by(id=review_id).first()
        if not review:
            raise ValueError(f"Review {review_id} not found")

        previous_status = review.status
        review.status = status
        review.comments = comments
        review.suggested_changes = suggested_changes
        review.approved_interpretation = approved_interpretation
        review.reviewed_at = datetime.utcnow()

        # Log the decision
        decision_text = self._format_review_decision(status, comments)
        self._create_decision_log(
            review=review,
            action=status.value,
            decision_text=decision_text,
            made_by=review.reviewer_name,
            previous_state=previous_status.value,
            new_state=status.value,
        )

        self.session.commit()

        return review

    def request_clarification(
        self, review_id: int, clarification_needed: str, made_by: str
    ) -> ClauseReview:
        """
        Request clarification on a clause interpretation

        Returns:
            Updated ClauseReview object
        """
        review = self.session.query(ClauseReview).filter_by(id=review_id).first()
        if not review:
            raise ValueError(f"Review {review_id} not found")

        review.status = ReviewStatus.NEEDS_CLARIFICATION
        review.comments = (
            review.comments or ""
        ) + f"\n\nClarification needed: {clarification_needed}"

        self._create_decision_log(
            review=review,
            action="REQUEST_CLARIFICATION",
            decision_text=clarification_needed,
            made_by=made_by,
        )

        self.session.commit()

        return review

    def _create_decision_log(
        self,
        review: ClauseReview,
        action: str,
        decision_text: str,
        made_by: str,
        previous_state: Optional[str] = None,
        new_state: Optional[str] = None,
        rationale: Optional[str] = None,
    ):
        """Create a decision log entry"""
        # Handle case where review doesn't have an ID yet
        if review.id is None:
            self.session.flush()  # Get the ID

        log = DecisionLog(
            review_id=review.id,
            action=action,
            decision_text=decision_text,
            rationale=rationale,
            previous_state=previous_state,
            new_state=new_state,
            made_by=made_by,
            made_at=datetime.utcnow(),
        )

        self.session.add(log)

    def _format_review_decision(
        self, status: ReviewStatus, comments: Optional[str]
    ) -> str:
        """Format review decision for logging"""
        decision = f"Review decision: {status.value}"
        if comments:
            decision += f"\nComments: {comments}"
        return decision

    def get_pending_reviews(self, reviewer_email: Optional[str] = None) -> List[Dict]:
        """
        Get all pending reviews

        Args:
            reviewer_email: Optional filter by reviewer

        Returns:
            List of review dictionaries with clause details
        """
        query = self.session.query(ClauseReview).filter(
            ClauseReview.status.in_(
                [
                    ReviewStatus.PENDING,
                    ReviewStatus.IN_REVIEW,
                    ReviewStatus.NEEDS_CLARIFICATION,
                ]
            )
        )

        if reviewer_email:
            query = query.filter(ClauseReview.reviewer_email == reviewer_email)

        reviews = query.all()

        result = []
        for review in reviews:
            clause = self.session.query(Clause).filter_by(id=review.clause_id).first()
            contract = (
                self.session.query(Contract).filter_by(id=clause.contract_id).first()
            )

            # Get interpretations for this clause
            interpretations = (
                self.session.query(Interpretation).filter_by(clause_id=clause.id).all()
            )

            result.append(
                {
                    "review_id": review.id,
                    "clause_id": clause.id,
                    "contract_name": contract.name if contract else "Unknown",
                    "section_number": clause.section_number,
                    "clause_type": clause.clause_type.value,
                    "risk_level": clause.risk_level.value,
                    "text": clause.text,
                    "status": review.status.value,
                    "reviewer": review.reviewer_name,
                    "assigned_at": review.assigned_at.isoformat()
                    if review.assigned_at
                    else None,
                    "has_ambiguity": any(i.has_ambiguity for i in interpretations),
                    "requires_review": any(
                        i.requires_legal_review for i in interpretations
                    ),
                }
            )

        return result

    def get_workflow_status(self, contract_id: int) -> ReviewWorkflowStatus:
        """
        Get overview of review workflow status for a contract

        Returns:
            ReviewWorkflowStatus object with counts
        """
        contract = self.session.query(Contract).filter_by(id=contract_id).first()
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")

        total_clauses = len(contract.clauses)

        # Count reviews by status
        status_counts = {}
        for status in ReviewStatus:
            count = (
                self.session.query(ClauseReview)
                .join(Clause)
                .filter(
                    Clause.contract_id == contract_id, ClauseReview.status == status
                )
                .count()
            )
            status_counts[status.value.lower()] = count

        return ReviewWorkflowStatus(
            total_clauses=total_clauses,
            pending_review=status_counts.get("pending", 0),
            in_review=status_counts.get("in_review", 0),
            approved=status_counts.get("approved", 0),
            rejected=status_counts.get("rejected", 0),
            needs_clarification=status_counts.get("needs_clarification", 0),
        )

    def get_decision_history(self, review_id: int) -> List[Dict]:
        """
        Get complete decision history for a review

        Returns:
            List of decision log dictionaries
        """
        logs = (
            self.session.query(DecisionLog)
            .filter_by(review_id=review_id)
            .order_by(DecisionLog.made_at)
            .all()
        )

        return [
            {
                "id": log.id,
                "action": log.action,
                "decision_text": log.decision_text,
                "rationale": log.rationale,
                "previous_state": log.previous_state,
                "new_state": log.new_state,
                "made_by": log.made_by,
                "made_at": log.made_at.isoformat() if log.made_at else None,
            }
            for log in logs
        ]
