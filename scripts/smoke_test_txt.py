"""In-process smoke test for the contract pipeline using a .txt file.

Why this exists:
- Lets us validate upload -> extraction -> list -> ask flows without running a long-lived server.
- Works in "lightweight mode" (no PDF/DOCX/NLP dependencies required).

Run:
  python scripts/smoke_test_txt.py
"""

from __future__ import annotations

import json
import os
import sys


def _repo_root() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, ".."))


def main() -> int:
    sys.path.insert(0, _repo_root())

    # Importing app initializes Config dirs and DB engine.
    from app import app  # noqa: WPS433

    sample_path = os.path.join(
        _repo_root(), "sample_contracts", "service_agreement.txt"
    )
    if not os.path.exists(sample_path):
        raise FileNotFoundError(sample_path)

    client = app.test_client()

    # 1) Health
    r = client.get("/health")
    assert r.status_code == 200, (r.status_code, r.data)

    # 2) Upload TXT
    with open(sample_path, "rb") as f:
        data = {
            "name": "Service Agreement (TXT Sample)",
            "version": "1.0",
            "is_amendment": "false",
            "file": (f, "service_agreement.txt"),
        }
        r = client.post(
            "/api/contracts/upload",
            data=data,
            content_type="multipart/form-data",
        )

    if r.status_code != 201:
        raise RuntimeError(
            f"Upload failed: HTTP {r.status_code}: {r.data.decode('utf-8', errors='replace')}"
        )

    upload = r.get_json() or {}
    contract_id = upload.get("contract_id")
    if not contract_id:
        raise RuntimeError(
            f"Upload response missing contract_id: {json.dumps(upload, indent=2)}"
        )

    # 3) List contracts
    r = client.get("/api/contracts")
    assert r.status_code == 200, (r.status_code, r.data)
    contracts = r.get_json() or []
    assert isinstance(contracts, list)

    # 4) Ask a question (lexical fallback is OK)
    question = "What does the agreement say about termination?"
    r = client.post(
        "/api/questions/ask",
        json={
            "question": question,
            "contract_id": int(contract_id),
            "asked_by": "smoke_test",
        },
    )

    if r.status_code != 200:
        raise RuntimeError(
            f"Ask failed: HTTP {r.status_code}: {r.data.decode('utf-8', errors='replace')}"
        )

    answer = r.get_json() or {}

    # Emit a compact summary for humans.
    print("OK: /health")
    print(
        f"OK: upload contract_id={contract_id} total_clauses={upload.get('total_clauses')}"
    )
    print(f"OK: /api/contracts count={len(contracts)}")
    print(
        f"OK: ask confidence={answer.get('confidence')} evidence={len(answer.get('evidence_clauses') or [])}"
    )

    # Basic invariants.
    assert (
        "answer" in answer
        and isinstance(answer["answer"], str)
        and answer["answer"].strip()
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
