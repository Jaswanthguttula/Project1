"""Document parser for extracting text from various file formats.

This module is intentionally resilient to optional dependencies:
- PDF parsing requires pdfplumber
- DOCX parsing requires python-docx

If those packages are not installed, the API can still start and TXT parsing will work.
"""

import re
from typing import Dict, List, Tuple


class DocumentParser:
    """Parse documents and extract structured text"""

    @staticmethod
    def parse_pdf(file_path: str) -> Dict[int, str]:
        """
        Extract text from PDF, page by page using pdfplumber

        Returns:
            Dict mapping page numbers to text content
        """
        pages = {}

        try:
            import pdfplumber  # type: ignore
        except ModuleNotFoundError as e:
            raise ModuleNotFoundError(
                "pdfplumber is required to parse PDF files. Install it with: pip install pdfplumber"
            ) from e

        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    pages[i + 1] = text

        return pages

    @staticmethod
    def parse_docx(file_path: str) -> Dict[int, str]:
        """
        Extract text from DOCX, paragraph by paragraph

        Returns:
            Dict with single key containing all text
        """
        try:
            from docx import Document  # type: ignore
        except ModuleNotFoundError as e:
            raise ModuleNotFoundError(
                "python-docx is required to parse DOCX files. Install it with: pip install python-docx"
            ) from e

        doc = Document(file_path)
        full_text = []

        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text)

        # For DOCX, we'll treat it as one "page" but track paragraph positions
        return {1: "\n".join(full_text)}

    @staticmethod
    def parse_txt(file_path: str) -> Dict[int, str]:
        """Extract text from plain text file"""
        with open(file_path, "r", encoding="utf-8") as file:
            text = file.read()
        return {1: text}

    @classmethod
    def parse(cls, file_path: str) -> Dict[int, str]:
        """
        Auto-detect format and parse document

        Returns:
            Dict mapping page/section numbers to text
        """
        if file_path.lower().endswith(".pdf"):
            return cls.parse_pdf(file_path)
        elif file_path.lower().endswith(".docx"):
            return cls.parse_docx(file_path)
        elif file_path.lower().endswith(".txt"):
            return cls.parse_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path}")


class StructureAnalyzer:
    """Analyze document structure and identify sections"""

    # Common patterns for section headers
    SECTION_PATTERNS = [
        r"^(\d+\.)+\s+[A-Z]",  # 1.2.3 TITLE or 1. TITLE
        r"^[A-Z][A-Z\s]+:",  # TITLE:
        r"^Article\s+\d+",  # Article 1
        r"^Section\s+\d+",  # Section 1
        r"^\([a-z]\)",  # (a), (b), (c)
        r"^\([ivxIVX]+\)",  # (i), (ii), (iii)
    ]

    @classmethod
    def identify_sections(cls, text: str) -> List[Tuple[str, str, int]]:
        """
        Identify sections and subsections in text

        Returns:
            List of tuples: (section_number, section_title, position)
        """
        sections = []
        lines = text.split("\n")

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Check if line matches any section pattern
            for pattern in cls.SECTION_PATTERNS:
                if re.match(pattern, line):
                    # Extract section number and title
                    match = re.match(r"^([\d\.\(\)a-z ivxIVX]+)\s*(.*)", line)
                    if match:
                        section_num = match.group(1).strip()
                        title = match.group(2).strip()
                        sections.append((section_num, title, i))
                    break

        return sections

    @classmethod
    def build_hierarchy(cls, sections: List[Tuple[str, str, int]]) -> Dict:
        """
        Build hierarchical structure from flat section list

        Returns:
            Nested dictionary representing document structure
        """
        hierarchy = {}

        for section_num, title, position in sections:
            # Simple hierarchy based on numbering depth
            parts = section_num.replace("(", "").replace(")", "").split(".")
            parts = [p.strip() for p in parts if p.strip()]

            current = hierarchy
            for i, part in enumerate(parts):
                if part not in current:
                    current[part] = {
                        "title": title if i == len(parts) - 1 else "",
                        "position": position,
                        "full_number": section_num,
                        "children": {},
                    }
                current = current[part]["children"]

        return hierarchy


class ClauseIdentifier:
    """Identify individual clauses within sections"""

    # Keywords that typically indicate important clause types
    OBLIGATION_KEYWORDS = [
        "shall",
        "must",
        "will",
        "agrees to",
        "obligated",
        "required to",
    ]
    EXCLUSION_KEYWORDS = [
        "shall not",
        "except",
        "excluding",
        "does not include",
        "not applicable",
    ]
    LIABILITY_KEYWORDS = [
        "liable",
        "liability",
        "damages",
        "indemnify",
        "responsible for",
    ]
    TERMINATION_KEYWORDS = [
        "terminate",
        "termination",
        "cancel",
        "cancellation",
        "end this agreement",
    ]

    @classmethod
    def split_into_clauses(cls, text: str, section_info: Dict) -> List[Dict]:
        """
        Split section text into individual clauses

        Returns:
            List of clause dictionaries with metadata
        """
        clauses = []

        # Split by sentence-like boundaries
        sentences = re.split(r"(?<=[.;])\s+(?=[A-Z(])", text)

        current_clause = []
        clause_number = 1

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Check if this starts a new clause (numbered or lettered)
            if re.match(r"^[\(\[]*[a-z0-9ivx]+[\)\]]\s*", sentence):
                # Save previous clause if exists
                if current_clause:
                    clause_text = " ".join(current_clause)
                    clauses.append(
                        {
                            "text": clause_text,
                            "clause_number": clause_number,
                            "section_number": section_info.get("number", ""),
                            "estimated_type": cls._estimate_clause_type(clause_text),
                        }
                    )
                    clause_number += 1

                # Start new clause
                current_clause = [sentence]
            else:
                current_clause.append(sentence)

        # Don't forget the last clause
        if current_clause:
            clause_text = " ".join(current_clause)
            clauses.append(
                {
                    "text": clause_text,
                    "clause_number": clause_number,
                    "section_number": section_info.get("number", ""),
                    "estimated_type": cls._estimate_clause_type(clause_text),
                }
            )

        return clauses

    @classmethod
    def _estimate_clause_type(cls, text: str) -> str:
        """Estimate clause type based on keywords"""
        text_lower = text.lower()

        # Check for exclusions first (more specific)
        if any(keyword in text_lower for keyword in cls.EXCLUSION_KEYWORDS):
            return "EXCLUSION"

        # Then obligations
        if any(keyword in text_lower for keyword in cls.OBLIGATION_KEYWORDS):
            return "OBLIGATION"

        # Liability
        if any(keyword in text_lower for keyword in cls.LIABILITY_KEYWORDS):
            return "LIABILITY"

        # Termination
        if any(keyword in text_lower for keyword in cls.TERMINATION_KEYWORDS):
            return "TERMINATION"

        return "GENERAL"
