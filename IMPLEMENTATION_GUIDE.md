# Project Implementation Guide

## Overview

You now have a complete **Contract Clause Detection and Analysis System** with all the features requested:

✅ **Structured Clause Extraction** with document, section, and clause path references  
✅ **Question Answering** with evidence and ambiguity/conflict highlighting  
✅ **Conflict Detection** across versions and amendments  
✅ **Ambiguity Detection** and risk assessment  
✅ **Reviewer Workflow** with decision logging  
✅ **Audit-Friendly Reports** in PDF and JSON formats

## Project Structure

```
CLAUSES DETECTION/
├── models/                 # Data models
│   ├── database.py        # SQLAlchemy ORM models
│   ├── schemas.py         # Pydantic validation schemas
│   └── __init__.py
├── extractors/            # Clause extraction
│   ├── document_parser.py # Parse PDF/DOCX/TXT
│   ├── clause_extractor.py# Main extraction engine
│   └── __init__.py
├── analyzers/             # Analysis engines
│   ├── conflict_detector.py   # Detect conflicts
│   ├── ambiguity_detector.py  # Detect ambiguities
│   └── __init__.py
├── qa_system/             # Question answering
│   ├── question_answering.py  # QA with evidence
│   └── __init__.py
├── workflows/             # Review management
│   ├── review_workflow.py # Review & decision logging
│   └── __init__.py
├── reports/               # Report generation
│   ├── report_generator.py # PDF/JSON exports
│   └── __init__.py
├── utils/                 # Helper functions
│   ├── helpers.py
│   └── __init__.py
├── tests/                 # Test suite
│   └── test_system.py
├── sample_contracts/      # Example contracts
│   └── service_agreement.txt
├── app.py                 # Main Flask API
├── config.py              # Configuration
├── setup.py               # Setup script
├── requirements.txt       # Dependencies
├── README.md              # Documentation
├── USAGE.md               # Usage guide
└── .env.example           # Environment template
```

## Key Components

### 1. Clause Extraction (`extractors/`)
- **DocumentParser**: Extracts text from PDF, DOCX, TXT files
- **StructureAnalyzer**: Identifies sections and hierarchy
- **ClauseIdentifier**: Splits sections into individual clauses
- **ClauseExtractor**: Orchestrates extraction with NLP enhancement

### 2. Conflict Detection (`analyzers/conflict_detector.py`)
- Detects internal contradictions within a contract
- Identifies conflicts between amendments and parent contracts
- Compares across contract versions
- Calculates confidence scores using semantic similarity

### 3. Ambiguity Detection (`analyzers/ambiguity_detector.py`)
- Identifies ambiguous terms (reasonable, appropriate, etc.)
- Detects vague quantifiers (some, several, etc.)
- Flags complex conditionals
- Assesses risk based on clause type and ambiguity level

### 4. Question Answering (`qa_system/`)
- Semantic search for relevant clauses
- Evidence-based answers with relevance scores
- Automatic conflict and ambiguity detection in evidence
- Similar question retrieval

### 5. Review Workflow (`workflows/`)
- Assign clauses for legal review
- Submit review decisions (APPROVED, REJECTED, NEEDS_CLARIFICATION)
- Track decision history with audit trail
- Batch assign high-risk clauses

### 6. Report Generation (`reports/`)
- Comprehensive PDF reports with:
  - Contract metadata
  - Executive summary
  - Clause breakdown by type/risk
  - Conflict report
  - Review workflow status
  - Decision audit trail
- JSON export for programmatic access

## Getting Started

### Step 1: Setup

```bash
# Run automated setup
python setup.py

# Or manual setup:
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python -m spacy download en_core_web_lg
```

### Step 2: Start the API

```bash
python app.py
```

Server runs at: `http://localhost:5000`

### Step 3: Upload Your First Contract

```bash
# Using the sample contract
curl -X POST http://localhost:5000/api/contracts/upload \
  -F "file=@sample_contracts/service_agreement.txt" \
  -F "name=Service Agreement"
```

Response shows:
- Total clauses extracted
- Clauses by type (OBLIGATION, PAYMENT, etc.)
- High-risk clause count
- Conflicts detected

### Step 4: Ask Questions

```bash
curl -X POST http://localhost:5000/api/questions/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the payment terms?",
    "contract_id": 1
  }'
```

Returns:
- Answer with evidence
- Relevant clause excerpts
- Ambiguities detected
- Conflicts (if any)
- Whether legal review is needed

### Step 5: Review High-Risk Clauses

```bash
# Check workflow status
curl http://localhost:5000/api/workflow/status/1

# Assign for review
curl -X POST http://localhost:5000/api/reviews/assign \
  -H "Content-Type: application/json" \
  -d '{
    "clause_id": 5,
    "reviewer_name": "Legal Team",
    "reviewer_email": "legal@company.com"
  }'

# Submit review
curl -X POST http://localhost:5000/api/reviews/submit \
  -H "Content-Type: application/json" \
  -d '{
    "clause_id": 5,
    "status": "APPROVED",
    "reviewer_name": "Legal Team",
    "reviewer_email": "legal@company.com",
    "comments": "Acceptable terms"
  }'
```

### Step 6: Generate Audit Report

```bash
curl -X POST http://localhost:5000/api/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "contract_ids": [1],
    "include_conflicts": true,
    "include_reviews": true,
    "include_decisions": true,
    "format": "pdf"
  }' \
  --output report.pdf
```

## Advanced Usage

### Python SDK

```python
from models.database import init_db, get_session
from extractors import ClauseExtractor
from analyzers import ConflictDetector, AmbiguityDetector
from qa_system import QuestionAnsweringSystem

# Initialize
engine = init_db()
session = get_session(engine)

# Extract clauses
extractor = ClauseExtractor()
clauses = extractor.extract_from_contract(contract, file_path, session)

# Analyze
conflict_detector = ConflictDetector(session)
conflicts = conflict_detector.detect_conflicts(contract_id)

ambiguity_detector = AmbiguityDetector(session)
interpretations = ambiguity_detector.analyze_all_clauses(contract_id)

# Ask questions
qa_system = QuestionAnsweringSystem(session)
answer = qa_system.answer_question("What is the liability limit?", contract_id=1)
```

### Amendment Processing

```bash
# Upload parent contract first
curl -X POST http://localhost:5000/api/contracts/upload \
  -F "file=@original_contract.pdf" \
  -F "name=Master Agreement"

# Upload amendment
curl -X POST http://localhost:5000/api/contracts/upload \
  -F "file=@amendment_1.pdf" \
  -F "name=Amendment 1" \
  -F "is_amendment=true" \
  -F "parent_contract_id=1"
```

The system automatically detects conflicts between amendment and parent contract.

## Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=. --cov-report=html

# Specific test class
pytest tests/test_system.py::TestConflictDetector -v
```

## Key Features Explained

### 1. Structured Clause References
Every clause has:
- **section_number**: "1.2.1"
- **clause_path**: Full hierarchical path
- **document**: Source contract name
- **page_number**: Location in document

### 2. Evidence-Based Answers
Questions return:
- **answer**: Extracted from most relevant clause
- **evidence_clauses**: List with relevance scores
- **ambiguities**: Detected in evidence
- **conflicts**: Between evidence clauses
- **requires_review**: Auto-flagged if high-risk

### 3. Conflict Types
- **CONTRADICTION**: Opposing terms in same contract
- **OVERRIDE**: Amendment overrides parent clause
- **VERSION_CONFLICT**: Different versions conflict

### 4. Risk Assessment
Automatically categorized:
- **CRITICAL**: High-impact types + high ambiguity
- **HIGH**: Critical types or significant ambiguity
- **MEDIUM**: Moderate ambiguity
- **LOW**: Clear, low-risk clauses

### 5. Decision Logging
Every review action creates audit log:
- Action taken
- Who made decision
- When it happened
- Rationale provided
- State transitions

## Customization

### Add New Clause Types

Edit `config.py`:
```python
CLAUSE_TYPES = [
    'OBLIGATION',
    'YOUR_NEW_TYPE',  # Add here
    # ...
]
```

### Adjust Risk Thresholds

Edit `.env`:
```
HIGH_RISK_THRESHOLD=0.8
MEDIUM_RISK_THRESHOLD=0.5
SIMILARITY_THRESHOLD=0.85
```

### Custom Ambiguous Terms

Edit `analyzers/ambiguity_detector.py`:
```python
AMBIGUOUS_TERMS = [
    'reasonable',
    'your_custom_term',
    # ...
]
```

## Production Considerations

### 1. Database
Replace SQLite with PostgreSQL:
```python
DATABASE_URL=postgresql://user:pass@localhost/contracts
```

### 2. Authentication
Add API authentication:
```python
from flask_jwt_extended import jwt_required

@app.route('/api/contracts/upload')
@jwt_required()
def upload_contract():
    # ...
```

### 3. Scalability
- Add task queue (Celery) for extraction
- Use Redis for caching
- Deploy with Gunicorn + Nginx

### 4. ML Models
- Fine-tune transformers on legal text
- Train custom clause classifier
- Add named entity recognition for parties, dates, amounts

## Troubleshooting

### Memory Issues
Large contracts may need:
```python
# Process in chunks
extractor.extract_from_contract(contract, file_path, session, chunk_size=50)
```

### Slow Extraction
Enable GPU for transformers:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Import Errors
Ensure virtual environment is activated:
```bash
venv\Scripts\activate  # Windows
source venv/bin/activate  # Unix/Linux/Mac
```

## Next Steps

1. **Add More Contracts**: Test with your actual contracts
2. **Customize Clause Types**: Add domain-specific types
3. **Train Models**: Fine-tune on your contract corpus
4. **Build Frontend**: Create React/Vue interface
5. **Integrate**: Connect to document management system
6. **Scale**: Deploy to production infrastructure

## Support

- Check [README.md](README.md) for project overview
- See [USAGE.md](USAGE.md) for detailed API documentation
- Run tests to verify installation
- Review sample contract for expected format

## Success Criteria ✅

All requested features implemented:

✅ Structured clause extraction with full references  
✅ Question answering with evidence and conflict highlighting  
✅ Conflict detection across versions and amendments  
✅ Ambiguity and risk assessment  
✅ Reviewer workflow with assignment and approval  
✅ Decision logging with complete audit trail  
✅ Export to PDF and JSON formats  
✅ Separation of extraction and interpretation  
✅ High-risk flagging for legal review  

**The system is ready to use!**
