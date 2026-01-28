"""
Main clause extractor that orchestrates the extraction process
"""

import json
from typing import List, Dict
from datetime import datetime

from .document_parser import DocumentParser, StructureAnalyzer, ClauseIdentifier
from models.database import Contract, Clause, ClauseType
from config import Config


class ClauseExtractor:
    """Main extraction engine for contract clauses"""

    def __init__(self):
        """Initialize NLP models"""
        self.nlp = None
        self.embedding_model = None
        self._load_models()

    def _load_models(self):
        """Load NLP and embedding models"""
        # spaCy is optional (used for richer clause type refinement).
        try:
            import spacy  # type: ignore

            try:
                self.nlp = spacy.load(Config.SPACY_MODEL)
            except OSError:
                print(
                    f"Warning: spaCy model '{Config.SPACY_MODEL}' not found. Using en_core_web_sm"
                )
                try:
                    self.nlp = spacy.load("en_core_web_sm")
                except OSError:
                    self.nlp = None
                    print("Warning: No spaCy model available.")
        except Exception as e:
            self.nlp = None
            print(
                f"Warning: spaCy not available ({type(e).__name__}). Clause extraction will run in lightweight mode."
            )

        # sentence-transformers is optional (used for semantic embeddings).
        # Catch ANY exception (import errors, version mismatches, download issues, etc.)
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            self.embedding_model = SentenceTransformer(Config.TRANSFORMER_MODEL)
        except Exception as e:
            self.embedding_model = None
            print(
                f"Warning: Could not load embedding model ({type(e).__name__}: {e}). Embeddings will be disabled."
            )

    def extract_from_contract(
        self, contract: Contract, file_path: str, session
    ) -> List[Clause]:
        """
        Extract all clauses from a contract document

        Args:
            contract: Contract database object
            file_path: Path to the contract file
            session: Database session

        Returns:
            List of extracted Clause objects
        """
        # Step 1: Parse document
        print(f"Parsing document: {file_path}")
        pages = DocumentParser.parse(file_path)

        # Step 2: Analyze structure for each page
        all_clauses = []
        clause_position = 0

        for page_num, page_text in pages.items():
            print(f"Processing page {page_num}...")

            # Identify sections
            sections = StructureAnalyzer.identify_sections(page_text)

            if not sections:
                # No clear structure, treat entire page as sections
                sections = [("", "Document Text", 0)]

            # Extract clauses from each section
            for section_num, section_title, position in sections:
                # Get text for this section
                section_text = self._extract_section_text(page_text, position, sections)

                # Split into individual clauses
                clause_dicts = ClauseIdentifier.split_into_clauses(
                    section_text, {"number": section_num, "title": section_title}
                )

                # Create Clause objects
                for clause_dict in clause_dicts:
                    clause = self._create_clause(
                        contract=contract,
                        clause_dict=clause_dict,
                        section_num=section_num,
                        section_title=section_title,
                        page_number=page_num,
                        position=clause_position,
                    )
                    all_clauses.append(clause)
                    clause_position += 1

        # Step 3: Enhance clauses with NLP analysis
        print("Enhancing clauses with NLP analysis...")
        self._enhance_clauses(all_clauses)

        # Step 4: Save to database
        print(f"Saving {len(all_clauses)} clauses to database...")
        for clause in all_clauses:
            session.add(clause)

        session.commit()

        return all_clauses

    def _extract_section_text(
        self, full_text: str, start_pos: int, all_sections: List
    ) -> str:
        """Extract text belonging to a specific section"""
        lines = full_text.split("\n")

        # Find the next section position
        current_idx = None
        next_idx = None

        for i, (_, _, pos) in enumerate(all_sections):
            if pos == start_pos:
                current_idx = i
            elif current_idx is not None and pos > start_pos:
                next_idx = i
                break

        if current_idx is not None:
            start_line = all_sections[current_idx][2]
            end_line = all_sections[next_idx][2] if next_idx is not None else len(lines)
            return "\n".join(lines[start_line:end_line])

        return ""

    def _create_clause(
        self,
        contract: Contract,
        clause_dict: Dict,
        section_num: str,
        section_title: str,
        page_number: int,
        position: int,
    ) -> Clause:
        """Create a Clause object from extracted data"""
        text = clause_dict["text"]

        # Build clause path
        clause_path = (
            f"{section_num}.{clause_dict['clause_number']}"
            if section_num
            else str(clause_dict["clause_number"])
        )

        # Normalize text for comparison
        normalized_text = self._normalize_text(text)

        # Map estimated type to enum
        clause_type = self._map_clause_type(clause_dict["estimated_type"])

        clause = Clause(
            contract_id=contract.id,
            section_number=section_num,
            clause_path=clause_path,
            title=section_title,
            text=text,
            normalized_text=normalized_text,
            clause_type=clause_type,
            page_number=page_number,
            position_in_document=position,
            extracted_at=datetime.utcnow(),
        )

        return clause

    def _enhance_clauses(self, clauses: List[Clause]):
        """Enhance clauses with NLP features"""
        # Generate embeddings in batch for efficiency (if enabled)
        if self.embedding_model is not None:
            texts = [clause.text for clause in clauses]
            try:
                embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
            except Exception as e:
                print(
                    f"Warning: embedding encode failed ({type(e).__name__}: {e}). Continuing without embeddings."
                )
                embeddings = [None] * len(clauses)
        else:
            embeddings = [None] * len(clauses)

        for clause, embedding in zip(clauses, embeddings):
            # Store embedding as JSON (optional)
            if embedding is not None:
                # sentence-transformers returns numpy arrays; convert defensively.
                clause.embedding_vector = json.dumps(list(map(float, embedding)))
            else:
                clause.embedding_vector = None

            # Additional NLP analysis with spaCy (optional)
            refined_type = self._refine_clause_type(clause.text, clause.clause_type)
            clause.clause_type = refined_type

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        # Remove extra whitespace
        text = " ".join(text.split())
        # Lowercase
        text = text.lower()
        # Remove special characters
        text = "".join(c if c.isalnum() or c.isspace() else " " for c in text)
        return text

    def _map_clause_type(self, estimated_type: str) -> ClauseType:
        """Map string type to ClauseType enum"""
        type_map = {
            "OBLIGATION": ClauseType.OBLIGATION,
            "EXCLUSION": ClauseType.EXCLUSION,
            "LIABILITY": ClauseType.LIABILITY,
            "TERMINATION": ClauseType.TERMINATION,
            "GENERAL": ClauseType.GENERAL,
        }
        return type_map.get(estimated_type, ClauseType.GENERAL)

    def _refine_clause_type(self, text: str, current_type: ClauseType) -> ClauseType:
        """Refine clause type using lightweight keyword heuristics."""
        text_lower = (text or "").lower()

        # Check for specific clause types based on keywords and patterns
        if "confidential" in text_lower or "non-disclosure" in text_lower:
            return ClauseType.CONFIDENTIALITY

        if "payment" in text_lower or "fee" in text_lower or "invoice" in text_lower:
            return ClauseType.PAYMENT

        if (
            "intellectual property" in text_lower
            or "copyright" in text_lower
            or "patent" in text_lower
        ):
            return ClauseType.INTELLECTUAL_PROPERTY

        if (
            "warranty" in text_lower
            or "warrants" in text_lower
            or "guarantee" in text_lower
        ):
            return ClauseType.WARRANTY

        if "indemnif" in text_lower or "hold harmless" in text_lower:
            return ClauseType.INDEMNIFICATION

        if "force majeure" in text_lower or "act of god" in text_lower:
            return ClauseType.FORCE_MAJEURE

        if (
            "dispute" in text_lower
            or "arbitration" in text_lower
            or "litigation" in text_lower
        ):
            return ClauseType.DISPUTE_RESOLUTION

        if (
            "amend" in text_lower
            or "modification" in text_lower
            or "change" in text_lower
        ):
            return ClauseType.AMENDMENT

        # Keep current type if no better match
        return current_type
