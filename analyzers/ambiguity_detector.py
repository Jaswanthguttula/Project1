"""
Ambiguity detection and risk assessment for clauses
"""

import re
from typing import List, Tuple
from sqlalchemy.orm import Session

from models.database import Clause, Interpretation, RiskLevel
from config import Config


class AmbiguityDetector:
    """Detect ambiguous language and assess risk in clauses"""

    # Ambiguous terms that can lead to interpretation issues
    AMBIGUOUS_TERMS = [
        "reasonable",
        "appropriate",
        "substantial",
        "material",
        "promptly",
        "timely",
        "as soon as possible",
        "best efforts",
        "good faith",
        "commercially reasonable",
        "may",
        "might",
        "approximately",
        "about",
        "around",
        "generally",
        "typically",
        "adequate",
        "sufficient",
        "necessary",
        "proper",
    ]

    # Vague quantifiers
    VAGUE_QUANTIFIERS = [
        "some",
        "several",
        "few",
        "many",
        "most",
        "numerous",
        "various",
        "certain",
        "multiple",
    ]

    # Conditional language that adds complexity
    COMPLEX_CONDITIONALS = [
        "unless",
        "except",
        "provided that",
        "subject to",
        "notwithstanding",
        "whereas",
        "whereby",
    ]

    def __init__(self, session: Session):
        self.session = session

    def analyze_clause(self, clause: Clause) -> Tuple[bool, List[str], float]:
        """
        Analyze a clause for ambiguity

        Returns:
            (has_ambiguity, list of issues, ambiguity_score)
        """
        text = clause.text.lower()
        issues = []
        score = 0.0

        # Check for ambiguous terms
        found_ambiguous = [term for term in self.AMBIGUOUS_TERMS if term in text]
        if found_ambiguous:
            issues.append(f"Ambiguous terms: {', '.join(found_ambiguous)}")
            score += len(found_ambiguous) * 0.15

        # Check for vague quantifiers
        found_vague = [term for term in self.VAGUE_QUANTIFIERS if term in text]
        if found_vague:
            issues.append(f"Vague quantifiers: {', '.join(found_vague)}")
            score += len(found_vague) * 0.1

        # Check for complex conditionals
        found_complex = [term for term in self.COMPLEX_CONDITIONALS if term in text]
        if found_complex:
            issues.append(f"Complex conditionals: {', '.join(found_complex)}")
            score += len(found_complex) * 0.12

        # Check for missing specifics (no numbers, dates, or concrete terms)
        has_numbers = bool(re.search(r"\d+", text))
        has_dates = bool(re.search(r"\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2}", text))

        if not has_numbers and not has_dates and len(text) > 100:
            if clause.clause_type.value in ["PAYMENT", "TERMINATION", "LIABILITY"]:
                issues.append(
                    "Lacks specific numbers or dates for critical clause type"
                )
                score += 0.25

        # Check for double negatives (confusing)
        negations = ["not", "no", "never", "neither", "nor"]
        negation_count = sum(1 for neg in negations if f" {neg} " in f" {text} ")
        if negation_count >= 2:
            issues.append("Contains multiple negations (potentially confusing)")
            score += 0.2

        # Check sentence length and complexity
        sentences = re.split(r"[.;]", clause.text)
        avg_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)

        if avg_length > 40:
            issues.append(f"Long average sentence length ({avg_length:.0f} words)")
            score += 0.15

        # Normalize score to 0-1 range
        score = min(score, 1.0)

        has_ambiguity = len(issues) > 0

        return has_ambiguity, issues, score

    def assess_risk_level(self, clause: Clause, ambiguity_score: float) -> RiskLevel:
        """
        Assess risk level based on clause type and ambiguity

        Returns:
            RiskLevel enum value
        """
        # Critical clause types that need clarity
        critical_types = [
            "LIABILITY",
            "INDEMNIFICATION",
            "TERMINATION",
            "PAYMENT",
            "INTELLECTUAL_PROPERTY",
        ]

        high_risk_types = [
            "OBLIGATION",
            "EXCLUSION",
            "WARRANTY",
            "CONFIDENTIALITY",
            "DISPUTE_RESOLUTION",
        ]

        clause_type = clause.clause_type.value

        # Base risk on ambiguity score
        if clause_type in critical_types:
            if ambiguity_score > 0.6:
                return RiskLevel.CRITICAL
            elif ambiguity_score > 0.3:
                return RiskLevel.HIGH
            elif ambiguity_score > 0.15:
                return RiskLevel.MEDIUM
            else:
                return RiskLevel.LOW

        elif clause_type in high_risk_types:
            if ambiguity_score > 0.7:
                return RiskLevel.HIGH
            elif ambiguity_score > 0.4:
                return RiskLevel.MEDIUM
            else:
                return RiskLevel.LOW

        else:
            # General clauses
            if ambiguity_score > 0.8:
                return RiskLevel.HIGH
            elif ambiguity_score > 0.5:
                return RiskLevel.MEDIUM
            else:
                return RiskLevel.LOW

    def create_interpretation(
        self, clause: Clause, issues: List[str], ambiguity_score: float
    ) -> Interpretation:
        """
        Create an interpretation record for an ambiguous clause

        Returns:
            Interpretation object
        """
        # Generate interpretation text
        interpretation_text = self._generate_interpretation(clause, issues)

        # Generate reasoning
        reasoning = f"Ambiguity score: {ambiguity_score:.2%}. "
        reasoning += "Issues identified: " + "; ".join(issues)

        # Determine if legal review is needed
        risk_level = self.assess_risk_level(clause, ambiguity_score)
        requires_review = risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]

        interpretation = Interpretation(
            clause_id=clause.id,
            interpretation_text=interpretation_text,
            reasoning=reasoning,
            is_ai_generated=True,
            created_by="AI",
            has_ambiguity=True,
            ambiguity_details="\n".join(issues),
            requires_legal_review=requires_review,
        )

        return interpretation

    def _generate_interpretation(self, clause: Clause, issues: List[str]) -> str:
        """Generate interpretation text for an ambiguous clause"""
        interp = f"This {clause.clause_type.value.lower()} clause "

        if len(issues) == 1:
            interp += "contains ambiguous language that "
        else:
            interp += "contains multiple ambiguities that "

        interp += "may lead to different interpretations. "

        # Add specific guidance based on clause type
        if clause.clause_type.value == "PAYMENT":
            interp += (
                "Payment terms should specify exact amounts, dates, and conditions. "
            )
        elif clause.clause_type.value == "TERMINATION":
            interp += (
                "Termination conditions should specify clear timelines and procedures. "
            )
        elif clause.clause_type.value == "LIABILITY":
            interp += "Liability limits should be explicitly stated with specific dollar amounts. "
        elif clause.clause_type.value in ["OBLIGATION", "EXCLUSION"]:
            interp += (
                "Obligations and exclusions should use clear, unambiguous language. "
            )

        interp += "Legal review is recommended to clarify interpretation."

        return interp

    def analyze_all_clauses(self, contract_id: int) -> List[Interpretation]:
        """
        Analyze all clauses in a contract for ambiguity

        Returns:
            List of Interpretation objects for ambiguous clauses
        """
        from models.database import Contract

        contract = self.session.query(Contract).filter_by(id=contract_id).first()
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")

        interpretations = []

        for clause in contract.clauses:
            has_ambiguity, issues, score = self.analyze_clause(clause)

            if has_ambiguity:
                # Update clause risk level
                risk_level = self.assess_risk_level(clause, score)
                clause.risk_level = risk_level

                # Create interpretation
                interpretation = self.create_interpretation(clause, issues, score)
                interpretations.append(interpretation)
                self.session.add(interpretation)

        self.session.commit()

        return interpretations
