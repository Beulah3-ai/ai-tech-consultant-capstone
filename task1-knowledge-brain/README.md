# Task 1: Knowledge Brain (Ingestion & Grounded Retrieval)

The **Knowledge Brain** is the foundational knowledge and retrieval engine for the AI Tech Consultant capstone. It ingests technical documentation from the Brilliant Directories Solution Center, indexes articles into a local SQLite store with FTS5 BM25 search, generates grounded answers with source citations, explicitly abstains when documentation is lacking, and provides an escalation workflow for human expert review.

---

## 📌 Implementation Status

### Currently Implemented & Tested
- [x] **Website Ingestion Pipeline**:
  - Resumable sitemap crawler for Brilliant Directories Solution Center (`https://support.brilliantdirectories.com/support/sitemap.xml`).
  - Configurable page bounds (e.g. `max_pages=10`), polite delays, timeouts, and exponential backoff retries.
  - Checkpoint tracking in database so interrupted runs record progress and can resume.
  - Robust HTML extraction of titles, canonical URLs, publication timestamps, and clean text (removing navigation, headers, scripts, and boilerplate).
- [x] **Local Knowledge Store (SQLite + FTS5)**:
  - SQLite database storing canonical URLs, titles, clean text, and SHA-256 content hashes.
  - Automatic change detection categorizing pages into `new`, `changed`, and `unchanged`.
  - Idempotent repeated ingestion runs without duplicate records.
  - Ingestion run metrics and error reporting.
- [x] **Grounded Retrieval & Answers**:
  - Local retrieval service utilizing SQLite FTS5 full-text search with BM25 ranking.
  - Grounded answers synthesized directly from retrieved documentation excerpts with transparent source citations (article titles and canonical URLs).
  - **Explicit Abstention**: If query keywords have no matching documentation or insufficient evidence, the system abstains rather than hallucinating facts.
  - **Configurable Provider**: Switch between `local_retrieval` (grounded answers) and `mock` (clearly labeled offline mock fallback) via configuration or query parameters.
- [x] **Escalation Workflow**:
  - `POST /escalations`: Captures unanswered questions and context for human consultant review.
  - `POST /escalations/{id}/resolve`: Records expert verified answers and marks items as resolved.
- [x] **Automated Test Suite**: 32 unit and integration tests passing offline with mocked network requests.

### Deferred / Not Yet Implemented
- [ ] Dense vector embeddings & vector database integration (e.g., Chroma / pgvector)
- [ ] Hybrid dense + sparse search fusion
- [ ] Multimodal / screenshot / image understanding
- [ ] Live Anthropic Claude API generation (mock and local retrieval are currently active)

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.11 or higher
- pip

### 2. Environment Setup
From the repository root, navigate to `task1-knowledge-brain/`:

```bash
cd task1-knowledge-brain
```

Create and activate a virtual environment:

```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy the example environment file:

```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# Linux / macOS
cp .env.example .env
```

Key environment variables:
- `AI_PROVIDER`: Choose `local_retrieval` to query the SQLite knowledge base, or `mock` for deterministic mock responses.
- `DATABASE_PATH`: Path to SQLite database (defaults to `data/knowledge_brain.db`).
- `ANTHROPIC_API_KEY`: Reserved for future Claude integration (not required currently).

---

## 🏃 Running the Application

Start the FastAPI application using Uvicorn:

```bash
uvicorn app.main:app --reload --port 8000
```

- **Interactive Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Specification**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Running Tests

Run the full pytest suite from inside `task1-knowledge-brain/`:

```bash
pytest -v
```

All 32 tests execute offline and deterministically with mocked HTTP fixtures.

---

## 📡 API Reference & Examples

### 1. Health Check
`GET /health`

**Response (200 OK):**
```json
{
  "status": "ok",
  "service": "knowledge-brain",
  "timestamp": "2026-10-17T16:00:00.000000Z",
  "provider": "local_retrieval",
  "total_articles": 10
}
```

---

### 2. Run Bounded Ingestion
`POST /ingestion/run`

**Request Body:**
```json
{
  "sitemap_url": "https://support.brilliantdirectories.com/support/sitemap.xml",
  "max_pages": 10,
  "rate_limit_delay_seconds": 0.5,
  "force_resync": false
}
```

**Response (200 OK):**
```json
{
  "run_id": "run_20261017_153000_a1b2c3",
  "status": "completed",
  "pages_discovered": 450,
  "pages_processed": 10,
  "pages_new": 10,
  "pages_changed": 0,
  "pages_unchanged": 0,
  "pages_removed": 0,
  "errors": [],
  "started_at": "2026-10-17T15:30:00.000000Z",
  "completed_at": "2026-10-17T15:30:05.000000Z"
}
```

---

### 3. Check Ingestion Status
`GET /ingestion/status`

**Response (200 OK):**
```json
{
  "status": "completed",
  "last_run_id": "run_20261017_153000_a1b2c3",
  "last_started_at": "2026-10-17T15:30:00.000000Z",
  "last_completed_at": "2026-10-17T15:30:05.000000Z",
  "total_articles_stored": 10,
  "pages_new": 10,
  "pages_changed": 0,
  "pages_unchanged": 0,
  "pages_removed": 0,
  "errors_count": 0,
  "recent_errors": []
}
```

---

### 4. Query Knowledge Brain (Grounded Retrieval)
`POST /query`

**Request Body:**
```json
{
  "query": "How do I configure Stripe payment gateway in Brilliant Directories?",
  "provider": "local_retrieval"
}
```

**Response (200 OK):**
```json
{
  "query": "How do I configure Stripe payment gateway in Brilliant Directories?",
  "answer": "According to the Brilliant Directories documentation for 'Setting Up Stripe Payment Gateway':\n\nConfigure Stripe in the Admin Dashboard under Finance > Payment Gateways.\nEnter your Publishable Key and Secret Key from the Stripe Dashboard.\n\nSource reference: https://support.brilliantdirectories.com/articles/stripe-gateway",
  "answered": true,
  "confidence": 0.85,
  "provider": "local_retrieval",
  "is_mock": false,
  "sources": [
    "Setting Up Stripe Payment Gateway (https://support.brilliantdirectories.com/articles/stripe-gateway)"
  ],
  "disclaimer": "Grounding Notice: Retrieved from local Brilliant Directories knowledge base via keyword and SQLite FTS5 search."
}
```

---

### 5. Query Knowledge Brain (Explicit Abstention)
`POST /query`

**Request Body:**
```json
{
  "query": "How do I bake artisan sourdough bread?",
  "provider": "local_retrieval"
}
```

**Response (200 OK):**
```json
{
  "query": "How do I bake artisan sourdough bread?",
  "answer": "I cannot answer this question based on the currently indexed Brilliant Directories knowledge base. Insufficient evidence was found. You may escalate this question to an expert for review.",
  "answered": false,
  "confidence": 0.0,
  "provider": "local_retrieval",
  "is_mock": false,
  "sources": [],
  "disclaimer": "Grounding Notice: Retrieved from local Brilliant Directories knowledge base via keyword and SQLite FTS5 search."
}
```

---

### 6. Create Escalation
`POST /escalations`

**Request Body:**
```json
{
  "query": "Does Brilliant Directories support SAML SSO for enterprise members?",
  "reason": "Missing documentation in public Solution Center",
  "context": "Client security requirement for enterprise rollout"
}
```

**Response (201 Created):**
```json
{
  "id": "esc_9f8e7d6c",
  "query": "Does Brilliant Directories support SAML SSO for enterprise members?",
  "reason": "Missing documentation in public Solution Center",
  "context": "Client security requirement for enterprise rollout",
  "status": "pending",
  "expert_answer": null,
  "resolved_by": null,
  "created_at": "2026-10-17T16:05:00.000000Z",
  "resolved_at": null
}
```

---

### 7. Resolve Escalation
`POST /escalations/{id}/resolve`

**Request Body:**
```json
{
  "expert_answer": "SAML SSO is supported via the Enterprise Single Sign-On bridge add-on configured with Azure AD or Okta metadata XML.",
  "resolved_by": "Lead Solutions Architect"
}
```

**Response (200 OK):**
```json
{
  "id": "esc_9f8e7d6c",
  "query": "Does Brilliant Directories support SAML SSO for enterprise members?",
  "reason": "Missing documentation in public Solution Center",
  "context": "Client security requirement for enterprise rollout",
  "status": "resolved",
  "expert_answer": "SAML SSO is supported via the Enterprise Single Sign-On bridge add-on configured with Azure AD or Okta metadata XML.",
  "resolved_by": "Lead Solutions Architect",
  "created_at": "2026-10-17T16:05:00.000000Z",
  "resolved_at": "2026-10-17T16:10:00.000000Z"
}
```
