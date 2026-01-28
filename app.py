"""
Main Flask API Application - Vercel Optimized
"""

import os
from flask import Flask, request, jsonify, send_file, render_template, redirect, url_for, flash
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from config import Config
from models.database import init_db, get_session, User, Contract
from models.schemas import (
    QuestionRequest,
    ReviewSubmissionRequest,
    AuditReportRequest,
)
from extractors import ClauseExtractor
from analyzers import ConflictDetector, AmbiguityDetector
from qa_system import QuestionAnsweringSystem
from workflows import ReviewWorkflow
from reports import AuditReportGenerator

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY # Ensure secret key is explicitly set
CORS(app)

# Initialize directories
Config.init_directories()

# Initialize database
try:
    engine = init_db(Config.DATABASE_URL)
except Exception as e:
    print(f"Database initialization failed: {e}")
    # In Vercel, we might not have write access to create a local SQLite file.
    # We create a dummy engine to allow the app to boot (e.g., for static pages).
    from sqlalchemy import create_engine
    engine = create_engine("sqlite:///:memory:")

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    session = get_session(engine)
    try:
        # Use session.get for SQLAlchemy 2.0+ compatibility
        return session.get(User, int(user_id))
    except Exception:
        return None
    finally:
        session.close()


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        session = get_session(engine)
        try:
            user = session.query(User).filter_by(username=username).first()
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                return redirect(url_for("home"))
            else:
                flash("Invalid username or password")
        finally:
            session.close()
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        session = get_session(engine)
        try:
            # Check if user exists
            if session.query(User).filter_by(username=username).first():
                flash("Username already exists")
            else:
                user = User(
                    username=username,
                    email=email,
                    password_hash=generate_password_hash(password),
                )
                session.add(user)
                session.commit()
                return redirect(url_for("login"))
        finally:
            session.close()
    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/", methods=["GET"])
@login_required
def home():
    """Serve the built-in frontend UI."""
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})


@app.route("/api/contracts/upload", methods=["POST"])
@login_required
def upload_contract():
    """
    Upload and process a contract document

    Accepts: multipart/form-data with file and metadata
    Returns: Contract details with extraction results
    """
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # Get metadata
    name = request.form.get("name", file.filename)
    version = request.form.get("version", "1.0")
    is_amendment = request.form.get("is_amendment", "false").lower() == "true"
    parent_contract_id = request.form.get("parent_contract_id", None)

    # Save file
    filename = secure_filename(file.filename)
    file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
    file.save(file_path)

    # Create contract in database
    session = get_session(engine)

    try:
        contract = Contract(
            name=name,
            original_filename=filename,
            file_path=file_path,
            version=version,
            is_amendment=is_amendment,
            parent_contract_id=int(parent_contract_id) if parent_contract_id else None,
        )
        session.add(contract)
        session.commit()

        # Extract clauses
        extractor = ClauseExtractor()
        start_time = datetime.utcnow()
        clauses = extractor.extract_from_contract(contract, file_path, session)
        extraction_time = (datetime.utcnow() - start_time).total_seconds()

        # Analyze for ambiguities
        ambiguity_detector = AmbiguityDetector(session)
        ambiguity_detector.analyze_all_clauses(contract.id)

        # Detect conflicts
        conflict_detector = ConflictDetector(session)
        conflicts = conflict_detector.detect_conflicts(contract.id)

        # Get clause statistics
        clauses_by_type = {}
        high_risk_count = 0

        for clause in clauses:
            clause_type = clause.clause_type.value
            clauses_by_type[clause_type] = clauses_by_type.get(clause_type, 0) + 1
            if clause.risk_level.value in ["HIGH", "CRITICAL"]:
                high_risk_count += 1

        result = {
            "contract_id": contract.id,
            "name": contract.name,
            "version": contract.version,
            "total_clauses": len(clauses),
            "clauses_by_type": clauses_by_type,
            "high_risk_count": high_risk_count,
            "conflicts_detected": len(conflicts),
            "extraction_time": extraction_time,
        }

        return jsonify(result), 201

    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@app.route("/api/contracts", methods=["GET"])
@login_required
def list_contracts():
    """List all contracts"""
    session = get_session(engine)

    try:
        contracts = session.query(Contract).all()

        result = []
        for contract in contracts:
            high_risk_count = sum(
                1
                for clause in contract.clauses
                if clause.risk_level.value in ["HIGH", "CRITICAL"]
            )

            result.append(
                {
                    "id": contract.id,
                    "name": contract.name,
                    "version": contract.version,
                    "is_amendment": contract.is_amendment,
                    "created_at": contract.created_at.isoformat()
                    if contract.created_at
                    else None,
                    "clause_count": len(contract.clauses),
                    "high_risk_clause_count": high_risk_count,
                }
            )

        return jsonify(result), 200

    finally:
        session.close()


@app.route("/api/contracts/<int:contract_id>", methods=["GET"])
@login_required
def get_contract(contract_id):
    """Get contract details"""
    session = get_session(engine)

    try:
        contract = session.query(Contract).filter_by(id=contract_id).first()

        if not contract:
            return jsonify({"error": "Contract not found"}), 404

        # Get clauses
        clauses = [
            {
                "id": clause.id,
                "section_number": clause.section_number,
                "clause_type": clause.clause_type.value,
                "risk_level": clause.risk_level.value,
                "text": clause.text[:200] + "..."
                if len(clause.text) > 200
                else clause.text,
            }
            for clause in contract.clauses
        ]

        result = {
            "id": contract.id,
            "name": contract.name,
            "version": contract.version,
            "is_amendment": contract.is_amendment,
            "created_at": contract.created_at.isoformat()
            if contract.created_at
            else None,
            "clauses": clauses,
        }

        return jsonify(result), 200

    finally:
        session.close()


@app.route("/api/questions/ask", methods=["POST"])
@login_required
def ask_question():
    """
    Ask a question about contracts

    Accepts: JSON with question and optional contract_id
    Returns: Answer with evidence clauses
    """
    data = request.get_json()

    try:
        question_req = QuestionRequest(**data)
    except Exception as e:
        return jsonify({"error": f"Invalid request: {str(e)}"}), 400

    session = get_session(engine)

    try:
        qa_system = QuestionAnsweringSystem(session)
        answer = qa_system.answer_question(
            question=question_req.question,
            contract_id=question_req.contract_id,
            asked_by=question_req.asked_by,
        )

        return jsonify(answer.dict()), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@app.route("/api/conflicts/<int:contract_id>", methods=["GET"])
@login_required
def get_conflicts(contract_id):
    """Get all conflicts for a contract"""
    session = get_session(engine)

    try:
        from models.database import Conflict, Clause

        conflicts = (
            session.query(Conflict)
            .join(Clause)
            .filter(Clause.contract_id == contract_id)
            .all()
        )

        result = [
            {
                "id": conflict.id,
                "clause_id": conflict.clause_id,
                "conflicting_clause_id": conflict.conflicting_clause_id,
                "conflict_type": conflict.conflict_type,
                "severity": conflict.severity.value,
                "description": conflict.description,
                "is_resolved": conflict.is_resolved,
            }
            for conflict in conflicts
        ]

        return jsonify(result), 200

    finally:
        session.close()


@app.route("/api/reviews/assign", methods=["POST"])
@login_required
def assign_review():
    """Assign a clause for review"""
    data = request.get_json()

    session = get_session(engine)

    try:
        workflow = ReviewWorkflow(session)
        review = workflow.assign_for_review(
            clause_id=data["clause_id"],
            reviewer_name=data["reviewer_name"],
            reviewer_email=data["reviewer_email"],
        )

        return jsonify(
            {
                "review_id": review.id,
                "clause_id": review.clause_id,
                "status": review.status.value,
                "reviewer": review.reviewer_name,
            }
        ), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@app.route("/api/reviews/submit", methods=["POST"])
@login_required
def submit_review():
    """Submit a review decision"""
    data = request.get_json()

    try:
        review_req = ReviewSubmissionRequest(**data)
    except Exception as e:
        return jsonify({"error": f"Invalid request: {str(e)}"}), 400

    session = get_session(engine)

    try:
        workflow = ReviewWorkflow(session)
        review = workflow.submit_review(
            review_id=review_req.clause_id,  # Using clause_id as review_id for simplicity
            status=review_req.status,
            comments=review_req.comments,
            suggested_changes=review_req.suggested_changes,
            approved_interpretation=review_req.approved_interpretation,
        )

        return jsonify(
            {
                "review_id": review.id,
                "status": review.status.value,
                "reviewed_at": review.reviewed_at.isoformat()
                if review.reviewed_at
                else None,
            }
        ), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@app.route("/api/reviews/pending", methods=["GET"])
@login_required
def get_pending_reviews():
    """Get all pending reviews"""
    reviewer_email = request.args.get("reviewer_email")

    session = get_session(engine)

    try:
        workflow = ReviewWorkflow(session)
        reviews = workflow.get_pending_reviews(reviewer_email)

        return jsonify(reviews), 200

    finally:
        session.close()


@app.route("/api/reports/generate", methods=["POST"])
@login_required
def generate_report():
    """Generate an audit report"""
    data = request.get_json()

    try:
        report_req = AuditReportRequest(**data)
    except Exception as e:
        return jsonify({"error": f"Invalid request: {str(e)}"}), 400

    session = get_session(engine)

    try:
        generator = AuditReportGenerator(session)

        # Generate report for first contract (can be extended for multiple)
        contract_id = report_req.contract_ids[0]
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        if report_req.format == "pdf":
            output_path = os.path.join(
                Config.REPORTS_FOLDER, f"contract_report_{contract_id}_{timestamp}.pdf"
            )
            generator.generate_contract_report(
                contract_id=contract_id,
                output_path=output_path,
                include_conflicts=report_req.include_conflicts,
                include_reviews=report_req.include_reviews,
                include_decisions=report_req.include_decisions,
            )
        else:  # JSON
            output_path = os.path.join(
                Config.REPORTS_FOLDER, f"contract_report_{contract_id}_{timestamp}.json"
            )
            generator.export_to_json(contract_id, output_path)

        return send_file(output_path, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@app.route("/api/workflow/status/<int:contract_id>", methods=["GET"])
@login_required
def get_workflow_status(contract_id):
    """Get workflow status for a contract"""
    session = get_session(engine)

    try:
        workflow = ReviewWorkflow(session)
        status = workflow.get_workflow_status(contract_id)

        return jsonify(status.dict()), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@app.route("/api/contracts/<int:contract_id>/history", methods=["GET"])
@login_required
def get_contract_history(contract_id):
    """Get the amendment history/lineage of a contract"""
    session = get_session(engine)
    try:
        current = session.query(Contract).filter_by(id=contract_id).first()
        if not current:
            return jsonify({"error": "Contract not found"}), 404

        # Find the root contract (the original)
        root = current
        while root.parent_contract_id:
            parent = session.query(Contract).filter_by(id=root.parent_contract_id).first()
            if not parent or parent.id == root.id: # Prevent infinite cycles
                break
            root = parent

        # Traverse down from root to find all amendments in order
        history = []
        def traverse(node):
            history.append({
                "id": node.id,
                "name": node.name,
                "version": node.version,
                "is_amendment": node.is_amendment,
                "created_at": node.created_at.isoformat() if node.created_at else None,
                "clause_count": len(node.clauses)
            })
            children = session.query(Contract).filter_by(parent_contract_id=node.id).order_by(Contract.id).all()
            for child in children:
                traverse(child)

        traverse(root)
        return jsonify(history), 200
    finally:
        session.close()

@app.route("/api/contracts/compare/<int:id1>/<int:id2>", methods=["GET"])
@login_required
def compare_contracts(id1, id2):
    """Compare two contracts and find clause changes"""
    session = get_session(engine)
    try:
        import difflib
        c1 = session.query(Contract).filter_by(id=id1).first()
        c2 = session.query(Contract).filter_by(id=id2).first()
        if not c1 or not c2:
            return jsonify({"error": "One or both contracts not found"}), 404

        # Map clauses by section/path for comparison
        clauses1 = {c.clause_path: c.text for c in c1.clauses if c.clause_path}
        clauses2 = {c.clause_path: c.text for c in c2.clauses if c.clause_path}

        diffs = []
        all_paths = sorted(set(clauses1.keys()) | set(clauses2.keys()))

        for path in all_paths:
            t1 = clauses1.get(path, "")
            t2 = clauses2.get(path, "")

            if t1 != t2:
                # Generate a simple diff
                d = difflib.ndiff(t1.split(), t2.split())
                diff_html = []
                for word in d:
                    if word.startswith("+ "): diff_html.append(f"<ins>{word[2:]}</ins>")
                    elif word.startswith("- "): diff_html.append(f"<del>{word[2:]}</del>")
                    elif word.startswith("  "): diff_html.append(word[2:])
                
                diffs.append({
                    "path": path,
                    "status": "added" if not t1 else ("removed" if not t2 else "modified"),
                    "old_text": t1,
                    "new_text": t2,
                    "diff_visual": " ".join(diff_html)
                })

        return jsonify({
            "contract1": {"id": c1.id, "name": c1.name},
            "contract2": {"id": c2.id, "name": c2.name},
            "changes": diffs
        }), 200
    finally:
        session.close()

@app.route("/api/clauses/<int:clause_id>/fix", methods=["POST"])
@login_required
def fix_clause(clause_id):
    """Suggest an improved version of a high-risk or ambiguous clause"""
    session = get_session(engine)
    try:
        from models.database import Clause, ClauseType
        clause = session.query(Clause).filter_by(id=clause_id).first()
        if not clause:
            return jsonify({"error": "Clause not found"}), 404

        original_text = clause.text
        suggestion = ""
        rationale = ""

        # Simple rule-based fixer for demonstration
        # In a real app, this would call an LLM with a specific prompt
        if clause.clause_type == ClauseType.LIABILITY:
            suggestion = original_text + " Notwithstanding the foregoing, the total liability of either party shall not exceed the total amount paid under this agreement in the twelve (12) months preceding the claim."
            rationale = "Added a liability cap to mitigate high-risk unlimited exposure."
        elif clause.clause_type == ClauseType.TERMINATION:
            suggestion = original_text + " Either party may terminate this agreement for convenience upon thirty (30) days prior written notice."
            rationale = "Added a termination for convenience right to provide exit flexibility."
        elif "reasonable" in original_text.lower():
            suggestion = original_text.replace("reasonable", "defined and objective")
            rationale = "Replaced subjective 'reasonable' with objective criteria to reduce ambiguity."
        else:
            suggestion = "REVISED: " + original_text.replace("shall", "will")
            rationale = "Simplified language for better clarity and modern legal standards."

        return jsonify({
            "original": original_text,
            "suggestion": suggestion,
            "rationale": rationale,
            "clause_type": clause.clause_type.value
        }), 200
    finally:
        session.close()

if __name__ == "__main__":
    # Internal server loop for local development
    print("Starting Contract Clause Detection System API...")
    host = Config.API_HOST
    port = Config.API_PORT

    try:
        from waitress import serve
        print("Serving with waitress...")
        serve(app, host=host, port=port)
    except ImportError:
        app.run(host=host, port=port, debug=Config.DEBUG)
