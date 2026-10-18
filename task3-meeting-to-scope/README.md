# Task 3: Meeting to Scope

Converts synthetic client-meeting transcripts into structured scope documents, effort estimates, and draft proposals using a deterministic multi-agent pipeline. Part of the AI Tech Consultant capstone.

> **All outputs are produced by a deterministic keyword-based pipeline — no LLM or Claude API is called. Every response is explicitly labelled `provider: deterministic_pipeline`, `is_mock: true`.**

---

## Features

- **3 synthetic meeting transcripts** (A: website search/filters/mobile, B: e-commerce/checkout/Stripe, C: follow-up to A)
- **5-stage modular pipeline**: Transcript Analyst → Feasibility Agent → Scope Agent → Estimation Agent → Proposal Agent
- **Knowledge Brain integration**: Feasibility Agent calls Task 1 `POST /query` with graceful timeout/error handling
- **Change analysis**: compare a follow-up transcript against an approved baseline
- **Human review workflow**: approve / reject / request-revision with full audit trail
- **JSON file persistence**: proposals, baselines, audit records (atomic writes)

---

## Requirements

- Python 3.11+
- pip packages: `fastapi uvicorn pydantic python-dotenv pytest httpx`

---

## Setup

```bash
cd task3-meeting-to-scope

# Install dependencies
pip install -r requirements.txt

# Copy and review environment config (no secrets committed)
copy .env.example .env
```

### Environment variables (`.env`)

| Variable | Default | Purpose |
|---|---|---|
| `KNOWLEDGE_BRAIN_URL` | `http://localhost:8000` | Task 1 API base URL |
| `DATA_DIR` | `./data` | JSON persistence directory |

---

## Run

```bash
# Start the server
python -m uvicorn app.main:app --reload --port 8003
```

API docs: [http://localhost:8003/docs](http://localhost:8003/docs)

---

## Key Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Service health check |
| GET | `/transcripts` | List available transcripts |
| POST | `/transcripts/{id}/process` | Run full pipeline, return DRAFT proposal |
| GET | `/proposals/{id}` | Retrieve a proposal |
| POST | `/proposals/{id}/approve` | Human approve → saves as baseline |
| POST | `/proposals/{id}/reject` | Human reject |
| POST | `/proposals/{id}/request-revision` | Request revision |
| POST | `/transcripts/{followup_id}/compare/{baseline_id}` | Change analysis (requires approved baseline) |
| GET | `/audit` | Full audit trail |

---

## Test

```bash
cd task3-meeting-to-scope
python -m pytest tests/ -v
```

### Test Coverage

| File | What is tested |
|---|---|
| `test_transcript_analyst.py` | Extraction, source refs, unique IDs, chunking |
| `test_feasibility_agent.py` | KB success, abstention, timeout, HTTP error |
| `test_scope_agent.py` | Deliverables, out-of-scope detection, risks, acceptance criteria |
| `test_estimation_agent.py` | Effort table matching, range validation, assumption labelling |
| `test_change_analyst.py` | Approved baseline requirement, change types, revised estimates |
| `test_approval.py` | Approve/reject/revise workflow, audit trail |
| `test_pipeline_integration.py` | End-to-end API: health, process, get, compare |

---

## Pipeline Architecture

```
Transcript (synthetic)
        │
        ▼
  TranscriptAnalyst          ← keyword extraction, source refs, chunking
        │
        ▼
  FeasibilityAgent           ← calls Task 1 POST /query (or graceful error)
        │
        ▼
    ScopeAgent               ← deliverables, in/out-of-scope, risks
        │
        ▼
  EstimationAgent            ← deterministic effort table (no AI)
        │
        ▼
  ProposalAgent              ← assembles ProposalDocument (always DRAFT)
        │
        ▼
  Human Review               ← approve / reject / request-revision
        │
        ▼
  ChangeAnalyst              ← baseline vs. follow-up diff (requires APPROVED)
```

---

## Synthetic Transcripts

| ID | Topic | Segments |
|---|---|---|
| `TRANSCRIPT-A` | LocalBiz Directory — website search, multi-select filters, mobile improvements | 12 |
| `TRANSCRIPT-B` | CraftMarket Pro — e-commerce checkout, Stripe payments, order notifications | 12 |
| `TRANSCRIPT-C` | LocalBiz follow-up — ADD voice search, MODIFY filter UX, REMOVE mobile redesign | 8 |

All transcripts are synthetic test artifacts. No real customer information is used.

---

## No Real API Keys Needed

The Feasibility Agent calls Task 1 at `KNOWLEDGE_BRAIN_URL`. If Task 1 is offline, it returns `answered: false` with an error message — it never fabricates answers.

Task 1 runs independently and has its own mock provider. You can test Task 3 without starting Task 1.
