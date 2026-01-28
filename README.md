# Contract Clause Detection & Analysis System

A comprehensive tool for extracting, analyzing, and managing contract clauses with support for version conflict detection, question answering, and legal review workflows.

## Features

- **Clause Extraction**: Automatically extracts structured clauses from contracts (TXT first; PDF/DOCX optional)
- **Question Answering**: Ask questions and get answers with clause-level evidence
- **Conflict Detection**: Identifies conflicts across contract versions and amendments
- **Ambiguity Detection**: Flags unclear or potentially problematic clauses
- **Risk Assessment**: Marks high-risk interpretations for legal review
- **Reviewer Workflow**: Structured approval process with decision logging
- **Audit Reports**: Export comprehensive audit-friendly reports

## Project Structure

```
clauses_detection/
├── models/             # Data models for contracts, clauses, etc.
├── extractors/         # Clause extraction logic
├── analyzers/          # Conflict detection, ambiguity analysis
├── qa_system/          # Question answering engine
├── workflows/          # Reviewer workflow management
├── reports/            # Report generation
├── api/                # REST API endpoints
├── database/           # Database setup and migrations
├── utils/              # Helper functions
└── tests/              # Unit and integration tests
```

## Installation

This project is designed to **gracefully degrade**: if optional NLP / PDF / DOCX libraries are missing or have version mismatches, the API still starts and Q&A falls back to lexical matching.

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Optional: Download spaCy model (improves clause typing)
python -m spacy download en_core_web_lg
```

## Usage

```bash
# Run the API server
python app.py

# Run an end-to-end smoke test with the included TXT contract
python scripts/smoke_test_txt.py

# Run tests
pytest tests/
```

### Quick start tip (TXT-first)

If you haven't installed PDF/DOCX/NLP dependencies yet, start with a `.txt` contract:

- Sample file: `sample_contracts/service_agreement.txt`
- The built-in UI is served at: `http://127.0.0.1:5000/`

## Architecture

1. **Extraction Layer**: Processes documents and extracts structured clauses
2. **Analysis Layer**: Detects conflicts, ambiguities, and assesses risk
3. **QA Layer**: Answers questions using extracted clauses as evidence
4. **Workflow Layer**: Manages review process and decision logging
5. **Reporting Layer**: Generates audit reports

## License

MIT
