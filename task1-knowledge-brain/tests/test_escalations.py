import tempfile
from pathlib import Path
import pytest
from app.services.escalation import EscalationService


@pytest.fixture
def escalation_service():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    service = EscalationService(db_path=path)
    yield service
    import gc
    gc.collect()
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        pass



def test_create_escalation(escalation_service):
    record = escalation_service.create(
        query="Can Brilliant Directories integrate directly with QuickBooks Online for ledger sync?",
        reason="No documentation found in Solution Center",
        context="Attempted keyword searches for 'QuickBooks' and 'accounting sync'",
    )

    assert record["id"].startswith("esc_")
    assert record["status"] == "pending"
    assert record["query"] == "Can Brilliant Directories integrate directly with QuickBooks Online for ledger sync?"
    assert record["expert_answer"] is None
    assert record["resolved_at"] is None


def test_resolve_escalation(escalation_service):
    record = escalation_service.create(
        query="Does Brilliant Directories support SAML SSO for enterprise members?",
        reason="Client enterprise security requirement",
    )
    esc_id = record["id"]

    resolved = escalation_service.resolve(
        escalation_id=esc_id,
        expert_answer="SAML SSO is available on Enterprise plans via custom OAuth/SAML bridge add-on.",
        resolved_by="Senior Solutions Architect",
    )

    assert resolved is not None
    assert resolved["id"] == esc_id
    assert resolved["status"] == "resolved"
    assert resolved["expert_answer"] == "SAML SSO is available on Enterprise plans via custom OAuth/SAML bridge add-on."
    assert resolved["resolved_by"] == "Senior Solutions Architect"
    assert resolved["resolved_at"] is not None


def test_resolve_nonexistent_escalation_returns_none(escalation_service):
    res = escalation_service.resolve(
        escalation_id="esc_nonexistent_12345",
        expert_answer="Answer",
        resolved_by="Architect",
    )
    assert res is None


def test_get_and_list_escalations(escalation_service):
    esc1 = escalation_service.create(query="Question 1", reason="Reason 1")
    esc2 = escalation_service.create(query="Question 2", reason="Reason 2")

    escalation_service.resolve(esc1["id"], expert_answer="Ans 1", resolved_by="Admin")

    pending_list = escalation_service.list_all(status="pending")
    assert len(pending_list) == 1
    assert pending_list[0]["id"] == esc2["id"]

    resolved_list = escalation_service.list_all(status="resolved")
    assert len(resolved_list) == 1
    assert resolved_list[0]["id"] == esc1["id"]
