"""
Question Answering System with Evidence Retrieval
"""

import json
import math
import re
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session

from models.database import Clause, Contract, Conflict, QuestionAnswer
from models.schemas import EvidenceClause, AnswerResponse, ConflictResponse
from config import Config


class QuestionAnsweringSystem:
    """Answer questions about contracts with clause-level evidence"""

    def __init__(self, session: Session):
        self.session = session
        # sentence-transformers is optional; we can fall back to lexical matching.
        # Catch ANY exception during model loading (import errors, version mismatches, etc.)
        self.embedding_model = None
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            self.embedding_model = SentenceTransformer(Config.TRANSFORMER_MODEL)
        except Exception as e:
            print(
                f"Warning: Could not load embedding model ({type(e).__name__}: {e}). "
                "QA will use lexical matching instead."
            )

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        text = (text or "").lower()
        # Keep it dependency-free and predictable.
        return re.findall(r"[a-z0-9]+", text)

    @classmethod
    def _lexical_similarity(cls, a: str, b: str) -> float:
        """Cosine similarity over binary token presence (0..1)."""
        ta = set(cls._tokenize(a))
        tb = set(cls._tokenize(b))
        if not ta or not tb:
            return 0.0
        inter = len(ta & tb)
        return inter / math.sqrt(len(ta) * len(tb))

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Cosine similarity for same-length numeric vectors (0..1-ish)."""
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

    def answer_question(
        self,
        question: str,
        contract_id: Optional[int] = None,
        top_k: int = 5,
        asked_by: str = "anonymous",
    ) -> AnswerResponse:
        """
        Answer a question using relevant clauses as evidence

        Args:
            question: The user's question
            contract_id: Optional contract ID to limit search scope
            top_k: Number of evidence clauses to retrieve
            asked_by: User identifier

        Returns:
            AnswerResponse with answer, evidence, and metadata
        """
        print(f"Processing question: {question}")

        # Step 1: Retrieve relevant clauses
        evidence_clauses = self._retrieve_evidence(question, contract_id, top_k)

        if not evidence_clauses:
            return AnswerResponse(
                answer="I couldn't find relevant clauses to answer this question.",
                confidence=0.0,
                evidence_clauses=[],
                ambiguities=[],
                conflicts=[],
                requires_review=False,
            )

        # Step 2: Generate answer from evidence
        answer, confidence = self._generate_answer(question, evidence_clauses)

        # Step 3: Check for ambiguities in evidence clauses
        ambiguities = self._detect_ambiguities(evidence_clauses)

        # Step 4: Check for conflicts between evidence clauses
        conflicts = self._check_evidence_conflicts(evidence_clauses)

        # Step 5: Determine if legal review is needed
        requires_review = self._needs_review(evidence_clauses, conflicts, ambiguities)

        # Step 6: Save Q&A to database
        self._save_qa(
            question, answer, confidence, evidence_clauses, asked_by, contract_id
        )

        # Step 7: Format response
        response = AnswerResponse(
            answer=answer,
            confidence=confidence,
            evidence_clauses=evidence_clauses,
            ambiguities=ambiguities,
            conflicts=conflicts,
            requires_review=requires_review,
        )

        return response

    def _retrieve_evidence(
        self, question: str, contract_id: Optional[int], top_k: int
    ) -> List[EvidenceClause]:
        """Retrieve most relevant clauses for the question"""
        question_embedding = None
        if self.embedding_model is not None:
            try:
                question_embedding = self.embedding_model.encode([question])[0]
            except Exception as e:
                # Any runtime issues (e.g., transformers/hf hub mismatches) should not break QA.
                print(
                    f"Warning: embedding encode failed ({type(e).__name__}: {e}). Falling back to lexical matching."
                )
                question_embedding = None

        # Get all clauses (filtered by contract if specified)
        query = self.session.query(Clause)
        if contract_id:
            query = query.filter(Clause.contract_id == contract_id)

        clauses = query.all()

        if not clauses:
            return []

        # Calculate similarities (embedding-based if available, else lexical)
        clause_scores = []
        for clause in clauses:
            similarity = 0.0
            if question_embedding is not None and clause.embedding_vector:
                try:
                    clause_vec = json.loads(clause.embedding_vector)
                    similarity = self._cosine_similarity(
                        list(map(float, question_embedding)),
                        list(map(float, clause_vec)),
                    )
                except (ValueError, TypeError, json.JSONDecodeError):
                    similarity = 0.0
            else:
                similarity = self._lexical_similarity(question, clause.text)

            clause_scores.append((clause, similarity))

        # Sort by similarity and take top k
        clause_scores.sort(key=lambda x: x[1], reverse=True)
        top_clauses = clause_scores[:top_k]

        # Format as EvidenceClause objects
        evidence = []
        for clause, score in top_clauses:
            # Get contract name
            contract = (
                self.session.query(Contract).filter_by(id=clause.contract_id).first()
            )

            evidence.append(
                EvidenceClause(
                    clause_id=clause.id,
                    section_number=clause.section_number,
                    text=clause.text,
                    relevance_score=float(score),
                    clause_type=clause.clause_type.value,
                    document_name=contract.name if contract else "Unknown",
                    page_number=clause.page_number,
                )
            )

        return evidence

    def _generate_answer(
        self, question: str, evidence_clauses: List[EvidenceClause]
    ) -> Tuple[str, float]:
        """
        Generate an answer based on evidence clauses

        Returns:
            (answer_text, confidence_score)
        """
        # Simple extractive approach: use most relevant clause
        # In production, you might use a generative model here

        if not evidence_clauses:
            return "No relevant information found.", 0.0

        most_relevant = evidence_clauses[0]

        # Build answer
        answer = f"Based on {most_relevant.document_name}"
        if most_relevant.section_number:
            answer += f", Section {most_relevant.section_number}"
        answer += ":\n\n"

        # Include the clause text
        answer += f'"{most_relevant.text}"'

        # Add supporting evidence if available
        if len(evidence_clauses) > 1:
            answer += f"\n\nThis is further supported by {len(evidence_clauses) - 1} related clause(s)"
            answer += " in "
            unique_docs = set(e.document_name for e in evidence_clauses[1:])
            answer += ", ".join(unique_docs)
            answer += "."

        # Confidence is based on relevance score of top clause
        confidence = most_relevant.relevance_score

        return answer, confidence

    def _detect_ambiguities(self, evidence_clauses: List[EvidenceClause]) -> List[str]:
        """Detect ambiguities in evidence clauses"""
        ambiguities = []

        ambiguous_terms = [
            "reasonable",
            "appropriate",
            "substantial",
            "material",
            "promptly",
            "timely",
            "best efforts",
            "good faith",
        ]

        for evidence in evidence_clauses:
            text_lower = evidence.text.lower()
            found_terms = [term for term in ambiguous_terms if term in text_lower]

            if found_terms:
                ambig_msg = f"Section {evidence.section_number or 'Unknown'} contains ambiguous terms: {', '.join(found_terms)}"
                ambiguities.append(ambig_msg)

        return ambiguities

    def _check_evidence_conflicts(
        self, evidence_clauses: List[EvidenceClause]
    ) -> List[ConflictResponse]:
        """Check for conflicts between evidence clauses"""
        conflicts = []

        clause_ids = [e.clause_id for e in evidence_clauses]

        # Query conflicts involving these clauses
        db_conflicts = (
            self.session.query(Conflict)
            .filter(Conflict.clause_id.in_(clause_ids))
            .filter(Conflict.conflicting_clause_id.in_(clause_ids))
            .all()
        )

        for conflict in db_conflicts:
            conflicts.append(
                ConflictResponse(
                    id=conflict.id,
                    clause_id=conflict.clause_id,
                    conflicting_clause_id=conflict.conflicting_clause_id,
                    conflict_type=conflict.conflict_type,
                    description=conflict.description,
                    severity=conflict.severity.value,
                    confidence_score=conflict.confidence_score,
                    is_resolved=conflict.is_resolved,
                )
            )

        return conflicts

    def _needs_review(
        self,
        evidence_clauses: List[EvidenceClause],
        conflicts: List[ConflictResponse],
        ambiguities: List[str],
    ) -> bool:
        """Determine if this answer requires legal review"""
        # Review needed if:
        # 1. Multiple high-risk clause types involved
        high_risk_types = ["LIABILITY", "TERMINATION", "INDEMNIFICATION", "PAYMENT"]
        high_risk_count = sum(
            1 for e in evidence_clauses if e.clause_type in high_risk_types
        )

        if high_risk_count >= 2:
            return True

        # 2. Conflicts detected
        if len(conflicts) > 0:
            return True

        # 3. Multiple ambiguities
        if len(ambiguities) >= 2:
            return True

        # 4. Low confidence in top evidence
        if evidence_clauses and evidence_clauses[0].relevance_score < 0.6:
            return True

        return False

    def _save_qa(
        self,
        question: str,
        answer: str,
        confidence: float,
        evidence_clauses: List[EvidenceClause],
        asked_by: str,
        contract_id: Optional[int],
    ):
        """Save question-answer pair to database"""
        # Generate embedding for question (optional)
        question_embedding = None
        if self.embedding_model is not None:
            try:
                question_embedding = self.embedding_model.encode([question])[0]
            except Exception as e:
                print(
                    f"Warning: embedding encode failed ({type(e).__name__}: {e}). Skipping question embedding storage."
                )
                question_embedding = None

        # Format evidence for storage
        evidence_json = json.dumps(
            [
                {"clause_id": e.clause_id, "relevance": e.relevance_score}
                for e in evidence_clauses
            ]
        )

        qa = QuestionAnswer(
            question=question,
            question_embedding=(
                json.dumps(list(map(float, question_embedding)))
                if question_embedding is not None
                else None
            ),
            answer=answer,
            confidence_score=confidence,
            evidence_clauses=evidence_json,
            asked_by=asked_by,
            contract_id=contract_id,
        )

        self.session.add(qa)
        self.session.commit()

    def get_similar_questions(self, question: str, top_k: int = 3) -> List[Dict]:
        """Find similar previously asked questions"""
        question_embedding = None
        if self.embedding_model is not None:
            try:
                question_embedding = self.embedding_model.encode([question])[0]
            except Exception as e:
                print(
                    f"Warning: embedding encode failed ({type(e).__name__}: {e}). Falling back to lexical matching."
                )
                question_embedding = None

        # Get all previous Q&As
        previous_qas = self.session.query(QuestionAnswer).all()

        if not previous_qas:
            return []

        # Calculate similarities (embedding-based if possible, else lexical)
        similarities = []
        for qa in previous_qas:
            similarity = 0.0
            if question_embedding is not None and qa.question_embedding:
                try:
                    qa_vec = json.loads(qa.question_embedding)
                    similarity = self._cosine_similarity(
                        list(map(float, question_embedding)),
                        list(map(float, qa_vec)),
                    )
                except (ValueError, TypeError, json.JSONDecodeError):
                    similarity = 0.0
            else:
                similarity = self._lexical_similarity(question, qa.question)

            similarities.append((qa, similarity))

        # Sort and take top k
        similarities.sort(key=lambda x: x[1], reverse=True)

        return [
            {
                "question": qa.question,
                "answer": qa.answer,
                "similarity": float(score),
                "asked_at": qa.asked_at.isoformat() if qa.asked_at else None,
            }
            for qa, score in similarities[:top_k]
        ]
