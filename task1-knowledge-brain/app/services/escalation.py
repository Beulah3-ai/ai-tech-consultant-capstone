import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from app.db import get_db_connection, init_db


class EscalationService:
    """Service managing unanswered query escalations and expert resolutions."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        init_db(self.db_path)

    def create(self, query: str, reason: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Create a new escalation record with status 'pending'."""
        escalation_id = f"esc_{uuid.uuid4().hex[:8]}"
        created_at = datetime.now(timezone.utc).isoformat()

        with get_db_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO escalations (
                    id, query, reason, context, status, created_at
                ) VALUES (?, ?, ?, ?, 'pending', ?)
                """,
                (escalation_id, query, reason, context, created_at),
            )
            conn.commit()

        return {
            "id": escalation_id,
            "query": query,
            "reason": reason,
            "context": context,
            "status": "pending",
            "expert_answer": None,
            "resolved_by": None,
            "created_at": created_at,
            "resolved_at": None,
        }

    def resolve(self, escalation_id: str, expert_answer: str, resolved_by: str) -> Optional[Dict[str, Any]]:
        """Resolve an existing escalation with expert answer and resolver identity."""
        resolved_at = datetime.now(timezone.utc).isoformat()

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM escalations WHERE id = ?", (escalation_id,))
            existing = cursor.fetchone()
            if not existing:
                return None

            cursor.execute(
                """
                UPDATE escalations SET
                    status = 'resolved',
                    expert_answer = ?,
                    resolved_by = ?,
                    resolved_at = ?
                WHERE id = ?
                """,
                (expert_answer, resolved_by, resolved_at, escalation_id),
            )
            conn.commit()

            cursor.execute("SELECT * FROM escalations WHERE id = ?", (escalation_id,))
            updated = cursor.fetchone()

            return {
                "id": updated["id"],
                "query": updated["query"],
                "reason": updated["reason"],
                "context": updated["context"],
                "status": updated["status"],
                "expert_answer": updated["expert_answer"],
                "resolved_by": updated["resolved_by"],
                "created_at": updated["created_at"],
                "resolved_at": updated["resolved_at"],
            }

    def get(self, escalation_id: str) -> Optional[Dict[str, Any]]:
        """Fetch escalation by ID."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM escalations WHERE id = ?", (escalation_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return dict(row)

    def list_all(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all escalations optionally filtered by status."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("SELECT * FROM escalations WHERE status = ? ORDER BY created_at DESC", (status,))
            else:
                cursor.execute("SELECT * FROM escalations ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]
