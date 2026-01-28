"""
Conflict detection across contract versions and amendments
"""

import json
import math
from typing import List, Tuple, Dict
from sqlalchemy.orm import Session

from models.database import Contract, Clause, Conflict, RiskLevel
from config import Config


class ConflictDetector:
    """Detect conflicts between clauses across versions and amendments"""

    def __init__(self, session: Session):
        self.session = session
        self.similarity_threshold = Config.SIMILARITY_THRESHOLD
        self.conflict_threshold = Config.CONFLICT_THRESHOLD

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Cosine similarity for same-length numeric vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        dot = 0.0
        n1 = 0.0
        n2 = 0.0
        for a, b in zip(vec1, vec2):
            dot += a * b
            n1 += a * a
            n2 += b * b
        if n1 <= 0.0 or n2 <= 0.0:
            return 0.0
        return dot / math.sqrt(n1 * n2)

    def detect_conflicts(self, contract_id: int) -> List[Conflict]:
        """
        Detect all conflicts for a given contract, including:
        - Internal contradictions
        - Conflicts with parent contract (if amendment)
        - Conflicts across versions

        Returns:
            List of detected Conflict objects
        """
        contract = self.session.query(Contract).filter_by(id=contract_id).first()
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")

        conflicts = []

        # 1. Detect internal contradictions
        print("Detecting internal contradictions...")
        internal_conflicts = self._detect_internal_conflicts(contract)
        conflicts.extend(internal_conflicts)

        # 2. If this is an amendment, check against parent contract
        if contract.is_amendment and contract.parent_contract_id:
            print("Detecting conflicts with parent contract...")
            parent_conflicts = self._detect_parent_conflicts(contract)
            conflicts.extend(parent_conflicts)

        # 3. Check against other versions of the same contract
        print("Detecting version conflicts...")
        version_conflicts = self._detect_version_conflicts(contract)
        conflicts.extend(version_conflicts)

        # Save all conflicts
        for conflict in conflicts:
            self.session.add(conflict)

        self.session.commit()

        return conflicts

    def _detect_internal_conflicts(self, contract: Contract) -> List[Conflict]:
        """Detect contradictions within the same contract"""
        conflicts = []
        clauses = contract.clauses

        # Group clauses by type for more efficient comparison
        clauses_by_type = {}
        for clause in clauses:
            if clause.clause_type not in clauses_by_type:
                clauses_by_type[clause.clause_type] = []
            clauses_by_type[clause.clause_type].append(clause)

        # Compare clauses within each type
        for clause_type, type_clauses in clauses_by_type.items():
            for i, clause1 in enumerate(type_clauses):
                for clause2 in type_clauses[i + 1 :]:
                    conflict = self._check_clause_conflict(clause1, clause2)
                    if conflict:
                        conflicts.append(conflict)

        return conflicts

    def _detect_parent_conflicts(self, amendment: Contract) -> List[Conflict]:
        """Detect conflicts between amendment and parent contract"""
        conflicts = []

        parent = amendment.parent_contract
        if not parent:
            return conflicts

        amendment_clauses = amendment.clauses
        parent_clauses = parent.clauses

        # Compare amendment clauses with parent clauses
        for amend_clause in amendment_clauses:
            for parent_clause in parent_clauses:
                # Only compare clauses of similar types or related sections
                if (
                    amend_clause.clause_type == parent_clause.clause_type
                    or self._sections_related(
                        amend_clause.section_number, parent_clause.section_number
                    )
                ):
                    conflict = self._check_clause_conflict(
                        amend_clause, parent_clause, conflict_type="OVERRIDE"
                    )
                    if conflict:
                        conflicts.append(conflict)

        return conflicts

    def _detect_version_conflicts(self, contract: Contract) -> List[Conflict]:
        """Detect conflicts across different versions"""
        conflicts = []

        # Find other versions of the same contract (by name similarity)
        other_contracts = (
            self.session.query(Contract)
            .filter(
                Contract.id != contract.id,
                Contract.name.contains(
                    contract.name.split()[0]
                ),  # Simple name matching
            )
            .all()
        )

        for other_contract in other_contracts:
            for clause1 in contract.clauses:
                for clause2 in other_contract.clauses:
                    if clause1.clause_type == clause2.clause_type:
                        conflict = self._check_clause_conflict(
                            clause1, clause2, conflict_type="VERSION_CONFLICT"
                        )
                        if conflict:
                            conflicts.append(conflict)

        return conflicts

    def _check_clause_conflict(
        self, clause1: Clause, clause2: Clause, conflict_type: str = "CONTRADICTION"
    ) -> Conflict:
        """
        Check if two clauses conflict

        Returns:
            Conflict object if conflict detected, None otherwise
        """
        # Get embeddings
        emb1 = (
            json.loads(clause1.embedding_vector) if clause1.embedding_vector else None
        )
        emb2 = (
            json.loads(clause2.embedding_vector) if clause2.embedding_vector else None
        )

        if not emb1 or not emb2:
            return None

        # Calculate semantic similarity
        try:
            similarity = self._cosine_similarity(
                list(map(float, emb1)),
                list(map(float, emb2)),
            )
        except (TypeError, ValueError):
            similarity = 0.0

        # High similarity + different implications = potential conflict
        # This is a simplified heuristic
        if similarity > self.similarity_threshold:
            # Check for contradictory terms
            contradiction_score = self._check_contradiction(clause1.text, clause2.text)

            if contradiction_score > self.conflict_threshold:
                # Determine severity based on clause types
                severity = self._assess_conflict_severity(
                    clause1.clause_type, contradiction_score
                )

                description = self._generate_conflict_description(
                    clause1, clause2, conflict_type, contradiction_score
                )

                conflict = Conflict(
                    clause_id=clause1.id,
                    conflicting_clause_id=clause2.id,
                    conflict_type=conflict_type,
                    description=description,
                    severity=severity,
                    confidence_score=contradiction_score,
                )

                return conflict

        return None

    def _check_contradiction(self, text1: str, text2: str) -> float:
        """
        Check for contradictory terms between two texts

        Returns:
            Score from 0.0 to 1.0 indicating contradiction level
        """
        # Negation indicators
        negations = ["not", "no", "never", "without", "except", "excluding"]
        obligations = ["shall", "must", "will", "required"]
        prohibitions = ["shall not", "must not", "prohibited", "forbidden"]

        text1_lower = text1.lower()
        text2_lower = text2.lower()

        score = 0.0

        # Check for opposing obligations
        has_obligation_1 = any(obl in text1_lower for obl in obligations)
        has_prohibition_1 = any(proh in text1_lower for proh in prohibitions)
        has_obligation_2 = any(obl in text2_lower for obl in obligations)
        has_prohibition_2 = any(proh in text2_lower for proh in prohibitions)

        # Obligation vs Prohibition
        if (has_obligation_1 and has_prohibition_2) or (
            has_prohibition_1 and has_obligation_2
        ):
            score += 0.7

        # Check for negation differences
        negation_count_1 = sum(1 for neg in negations if neg in text1_lower)
        negation_count_2 = sum(1 for neg in negations if neg in text2_lower)

        if abs(negation_count_1 - negation_count_2) >= 2:
            score += 0.3

        return min(score, 1.0)

    def _sections_related(self, section1: str, section2: str) -> bool:
        """Check if two section numbers are related"""
        if not section1 or not section2:
            return False

        # Simple check: same top-level section
        parts1 = section1.split(".")
        parts2 = section2.split(".")

        return parts1[0] == parts2[0] if parts1 and parts2 else False

    def _assess_conflict_severity(
        self, clause_type, contradiction_score: float
    ) -> RiskLevel:
        """Assess the severity of a conflict"""
        # Critical clause types
        critical_types = ["LIABILITY", "TERMINATION", "INDEMNIFICATION", "PAYMENT"]

        if clause_type.value in critical_types:
            if contradiction_score > 0.7:
                return RiskLevel.CRITICAL
            else:
                return RiskLevel.HIGH
        else:
            if contradiction_score > 0.7:
                return RiskLevel.HIGH
            elif contradiction_score > 0.5:
                return RiskLevel.MEDIUM
            else:
                return RiskLevel.LOW

    def _generate_conflict_description(
        self, clause1: Clause, clause2: Clause, conflict_type: str, score: float
    ) -> str:
        """Generate human-readable conflict description"""
        desc = f"{conflict_type}: "

        if conflict_type == "OVERRIDE":
            desc += f"Amendment clause (Section {clause1.section_number}) may override "
            desc += f"original clause (Section {clause2.section_number}). "
        elif conflict_type == "VERSION_CONFLICT":
            desc += "Different versions contain conflicting clauses in sections "
            desc += f"{clause1.section_number} and {clause2.section_number}. "
        else:
            desc += "Contradictory clauses found in sections "
            desc += f"{clause1.section_number} and {clause2.section_number}. "

        desc += f"Conflict confidence: {score:.2%}"

        return desc
