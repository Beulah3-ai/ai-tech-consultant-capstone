"""JSON file store for proposals, baselines, and audit records.

Uses atomic write (write temp → rename) for reliability on Windows.
"""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.schemas import ApprovalRecord, ProposalDocument

# Default data directory relative to the project root
_DEFAULT_DATA_DIR = Path(__file__).parent.parent / "data"


def _atomic_write(path: Path, data: str) -> None:
    """Write data atomically using a temp file + rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(data)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


class ProposalStore:
    """Persists ProposalDocuments and ApprovalRecords as JSON files."""

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        self.data_dir = data_dir or _DEFAULT_DATA_DIR
        self.proposals_dir = self.data_dir / "proposals"
        self.baselines_dir = self.data_dir / "baselines"
        self.audit_dir = self.data_dir / "audit"

    # ------------------------------------------------------------------
    # Proposals
    # ------------------------------------------------------------------

    def save_proposal(self, proposal: ProposalDocument) -> None:
        filename = f"{proposal.proposal_id}_{proposal.version}.json"
        path = self.proposals_dir / filename
        _atomic_write(path, proposal.model_dump_json(indent=2))

    def load_proposal(self, proposal_id: str, version: str = "1.0") -> ProposalDocument:
        filename = f"{proposal_id}_{version}.json"
        path = self.proposals_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Proposal not found: {filename}")
        data = json.loads(path.read_text(encoding="utf-8"))
        return ProposalDocument.model_validate(data)

    def list_proposals(self) -> List[Dict[str, str]]:
        self.proposals_dir.mkdir(parents=True, exist_ok=True)
        result = []
        for p in self.proposals_dir.glob("*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                result.append(
                    {
                        "proposal_id": data.get("proposal_id", ""),
                        "version": data.get("version", ""),
                        "transcript_id": data.get("transcript_id", ""),
                        "status": data.get("status", ""),
                        "created_at": data.get("created_at", ""),
                    }
                )
            except Exception:
                continue
        return result

    # ------------------------------------------------------------------
    # Baselines (approved proposals marked as canonical)
    # ------------------------------------------------------------------

    def save_baseline(self, proposal: ProposalDocument) -> None:
        filename = f"{proposal.proposal_id}_{proposal.version}_baseline.json"
        path = self.baselines_dir / filename
        _atomic_write(path, proposal.model_dump_json(indent=2))

    def load_baseline(self, proposal_id: str, version: str = "1.0") -> ProposalDocument:
        filename = f"{proposal_id}_{version}_baseline.json"
        path = self.baselines_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Baseline not found: {filename}")
        data = json.loads(path.read_text(encoding="utf-8"))
        return ProposalDocument.model_validate(data)

    # ------------------------------------------------------------------
    # Audit trail
    # ------------------------------------------------------------------

    def save_approval(self, record: ApprovalRecord) -> None:
        entry_id = uuid.uuid4().hex[:8]
        filename = f"{record.document_id}_{record.version}_{entry_id}.json"
        path = self.audit_dir / filename
        _atomic_write(path, record.model_dump_json(indent=2))

    def get_audit_trail(
        self, proposal_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        records = []
        for p in sorted(self.audit_dir.glob("*.json")):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if proposal_id and data.get("document_id") != proposal_id:
                    continue
                records.append(data)
            except Exception:
                continue
        return records
