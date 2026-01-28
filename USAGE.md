# Usage Guide - Contract Clause Detection System

## Quick Start

### 1. Installation

```bash
# Run the setup script
python setup.py

# Or manually:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_lg
```

### 2. Start the API Server

```bash
python app.py
```

The API will be available at `http://localhost:5000`

## API Endpoints

### Health Check
```bash
GET /health
```

### Upload Contract
```bash
POST /api/contracts/upload
Content-Type: multipart/form-data

Parameters:
- file: Contract document (PDF, DOCX, or TXT)
- name: Contract name
- version: Version number (default: "1.0")
- is_amendment: Boolean (default: false)
- parent_contract_id: ID of parent contract (for amendments)
```

Example using curl:
```bash
curl -X POST http://localhost:5000/api/contracts/upload \
  -F "file=@sample_contracts/service_agreement.txt" \
  -F "name=Service Agreement" \
  -F "version=1.0"
```

### List Contracts
```bash
GET /api/contracts
```

### Get Contract Details
```bash
GET /api/contracts/{contract_id}
```

### Ask a Question
```bash
POST /api/questions/ask
Content-Type: application/json

{
  "question": "What are the payment terms?",
  "contract_id": 1,
  "asked_by": "user@example.com"
}
```

Example:
```bash
curl -X POST http://localhost:5000/api/questions/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the termination conditions?", "contract_id": 1}'
```

### Get Conflicts
```bash
GET /api/conflicts/{contract_id}
```

### Assign Review
```bash
POST /api/reviews/assign
Content-Type: application/json

{
  "clause_id": 1,
  "reviewer_name": "John Doe",
  "reviewer_email": "john@example.com"
}
```

### Submit Review
```bash
POST /api/reviews/submit
Content-Type: application/json

{
  "clause_id": 1,
  "status": "APPROVED",
  "reviewer_name": "John Doe",
  "reviewer_email": "john@example.com",
  "comments": "Looks good",
  "approved_interpretation": "This clause is clear"
}
```

### Get Pending Reviews
```bash
GET /api/reviews/pending?reviewer_email=john@example.com
```

### Generate Report
```bash
POST /api/reports/generate
Content-Type: application/json

{
  "contract_ids": [1],
  "include_conflicts": true,
  "include_reviews": true,
  "include_decisions": true,
  "format": "pdf"
}
```

### Get Workflow Status
```bash
GET /api/workflow/status/{contract_id}
```

## Workflow Example

### Step 1: Upload a Contract
```bash
curl -X POST http://localhost:5000/api/contracts/upload \
  -F "file=@sample_contracts/service_agreement.txt" \
  -F "name=Service Agreement"
```

Response:
```json
{
  "contract_id": 1,
  "name": "Service Agreement",
  "version": "1.0",
  "total_clauses": 25,
  "high_risk_count": 5,
  "conflicts_detected": 0,
  "extraction_time": 2.5
}
```

### Step 2: Ask Questions
```bash
curl -X POST http://localhost:5000/api/questions/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the liability limit?",
    "contract_id": 1
  }'
```

Response includes answer with evidence clauses and any conflicts/ambiguities.

### Step 3: Review High-Risk Clauses
```bash
# Get workflow status
curl http://localhost:5000/api/workflow/status/1

# Assign high-risk clauses for review
curl -X POST http://localhost:5000/api/reviews/assign \
  -H "Content-Type: application/json" \
  -d '{
    "clause_id": 15,
    "reviewer_name": "Legal Team",
    "reviewer_email": "legal@company.com"
  }'
```

### Step 4: Submit Review Decisions
```bash
curl -X POST http://localhost:5000/api/reviews/submit \
  -H "Content-Type: application/json" \
  -d '{
    "clause_id": 15,
    "status": "APPROVED",
    "reviewer_name": "Legal Team",
    "reviewer_email": "legal@company.com",
    "comments": "Liability terms are acceptable"
  }'
```

### Step 5: Generate Audit Report
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
  --output contract_report.pdf
```

## Python SDK Usage

```python
from models.database import init_db, get_session, Contract
from extractors import ClauseExtractor
from analyzers import ConflictDetector, AmbiguityDetector
from qa_system import QuestionAnsweringSystem
from workflows import ReviewWorkflow
from reports import AuditReportGenerator

# Initialize
engine = init_db()
session = get_session(engine)

# Extract clauses from contract
contract = session.query(Contract).filter_by(id=1).first()
extractor = ClauseExtractor()
clauses = extractor.extract_from_contract(contract, "path/to/contract.pdf", session)

# Detect conflicts
conflict_detector = ConflictDetector(session)
conflicts = conflict_detector.detect_conflicts(contract.id)

# Analyze ambiguities
ambiguity_detector = AmbiguityDetector(session)
interpretations = ambiguity_detector.analyze_all_clauses(contract.id)

# Answer questions
qa_system = QuestionAnsweringSystem(session)
answer = qa_system.answer_question("What are the payment terms?", contract_id=1)

# Manage reviews
workflow = ReviewWorkflow(session)
review = workflow.assign_for_review(clause_id=5, reviewer_name="John", reviewer_email="john@example.com")

# Generate report
report_gen = AuditReportGenerator(session)
report_gen.generate_contract_report(contract.id, "output/report.pdf")
```

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test
pytest tests/test_system.py::TestDatabase::test_create_contract -v
```

## Troubleshooting

### Issue: spaCy model not found
```bash
python -m spacy download en_core_web_lg
```

### Issue: Database errors
```bash
# Delete and recreate database
rm contracts.db
python -c "from models.database import init_db; init_db()"
```

### Issue: Import errors
Make sure you're in the virtual environment:
```bash
# Windows
venv\Scripts\activate

# Unix/Linux/Mac
source venv/bin/activate
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer (Flask)                      │
├─────────────────────────────────────────────────────────────┤
│  Extractors  │  Analyzers  │  QA System  │  Workflows       │
│  - Document  │  - Conflict │  - Question │  - Review        │
│    Parser    │    Detector │    Answering│    Management    │
│  - Clause    │  - Ambiguity│  - Evidence │  - Decision      │
│    Extractor │    Detector │    Retrieval│    Logging       │
├─────────────────────────────────────────────────────────────┤
│                    Database Layer (SQLAlchemy)                │
│  Contracts | Clauses | Conflicts | Reviews | Interpretations │
└─────────────────────────────────────────────────────────────┘
```

## Key Features Demonstrated

1. **Clause Extraction**: Automatically extracts and classifies clauses
2. **Conflict Detection**: Identifies contradictions across versions
3. **Ambiguity Analysis**: Flags unclear language
4. **Risk Assessment**: Categorizes clauses by risk level
5. **Q&A System**: Answers questions with evidence
6. **Review Workflow**: Manages legal review process
7. **Decision Logging**: Maintains audit trail
8. **Report Generation**: Creates PDF/JSON audit reports
