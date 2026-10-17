# Task 2: Inbox Agent & Human Review Portal

The **Inbox Agent** is the triage and response generation engine for the **AI Tech Consultant Capstone**. Built with **TypeScript** and **Node.js**, it ingests customer inquiries, classifies intent and urgency, retrieves verified technical evidence from the Task 1 Knowledge Brain, generates grounded draft responses with citations, and provides an interactive **Human Review Portal** with strict **Autonomy Safeguards**.

---

## 📌 Implementation Status

### Currently Implemented & Tested
- [x] **TypeScript & Node.js Backend**: Express server with strict Zod runtime schema validation.
- [x] **Task 1 Knowledge Brain Connection**:
  - Connects to Task 1 Knowledge Brain at `http://localhost:8000/query` (configurable via `KNOWLEDGE_BRAIN_URL`).
  - Configurable timeouts (`KNOWLEDGE_BRAIN_TIMEOUT_MS`, default 4000ms) with `AbortSignal`.
  - Resilient error handling: network timeouts and API errors safely fallback to escalation without pretending failed calls succeeded.
  - Offline mock provider available for standalone testing (`MOCK_KNOWLEDGE_BRAIN=true`).
- [x] **Synthetic Customer Email Dataset**:
  - 55 realistic synthetic customer emails stored in [`data/synthetic_emails.json`](file:///c:/Users/gurra/ai-tech-consultant-capstone/task2-inbox-agent/data/synthetic_emails.json).
  - Explicitly marked as synthetic (`"synthetic": true`, test domain addresses, zero real customer PII).
  - Balanced across 6 categories: `technical_support`, `billing`, `onboarding`, `feature_requests`, `account_configuration`, and `out_of_scope`.
- [x] **Classification & Draft Generation**:
  - Assigns `category`, `priority` (`urgent`, `high`, `medium`, `low`), and `confidence` (0.0 – 1.0).
  - Generates replies grounded in Task 1 Knowledge Brain evidence with article citations.
  - Explicit abstention for out-of-scope inquiries and questions with insufficient knowledge base evidence.
- [x] **Human Review Web Interface**:
  - Interactive portal served at `http://localhost:3000`.
  - Displays customer email, classification breakdown, grounded Task 1 citations, and editable draft reply.
  - Review actions: **Approve (Unchanged)**, **Edit & Approve**, **Reject**, and **Escalate**.
  - Review decisions, reviewer IDs, timestamps, and notes saved to an audit trail.
- [x] **Autonomy Safeguard Engine**:
  - Tracks consecutive approved, unchanged drafts per category.
  - Marks category as **Eligible for Autonomy** strictly after **20 consecutive qualifying drafts**.
  - Editing, rejecting, or escalating immediately resets the consecutive count to 0 and revokes eligibility.
  - **Safety Policy**: Autonomy eligibility is an audit readiness metric only; no emails are dispatched automatically.
- [x] **Evaluation Test Suite**: 32 deterministic tests running via Vitest covering classification, citations, abstention, error handling, review actions, and the 20-draft safeguard.

### Deferred / Not Yet Implemented
- [ ] Direct IMAP/SMTP/SendGrid inbox sync (operates on the synthetic dataset for safe development)
- [ ] Automatic email dispatch (autonomy eligibility is purely a readiness status)
- [ ] Live Anthropic Claude API generation (mock and local retrieval are currently active)

---

## 🚀 Getting Started

### 1. Prerequisites
- Node.js 20 or higher (v22 recommended)
- npm 10 or higher
- *(Optional)* Running Task 1 Knowledge Brain on `http://localhost:8000`

### 2. Installation
Navigate into the `task2-inbox-agent/` directory:

```bash
cd task2-inbox-agent
npm install
```

### 3. Environment Configuration
Copy the `.env.example` file:

```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# Linux / macOS
cp .env.example .env
```

Available environment variables:
```env
PORT=3000
KNOWLEDGE_BRAIN_URL=http://localhost:8000
KNOWLEDGE_BRAIN_TIMEOUT_MS=4000
AI_PROVIDER=local_retrieval
MOCK_KNOWLEDGE_BRAIN=false
```

---

## 🏃 Running the Application

### Start the Development Server
```bash
npm start
```

Open your browser to:
- **Human Review Portal**: [http://localhost:3000](http://localhost:3000)
- **Health Check**: [http://localhost:3000/health](http://localhost:3000/health)
- **Autonomy Status API**: [http://localhost:3000/api/autonomy](http://localhost:3000/api/autonomy)

---

## 🧪 Running the Test Suite

Run all evaluation tests with Vitest:

```bash
npm test
```

Build the TypeScript project:

```bash
npm run build
```

---

## 🛡️ Autonomy Safeguard Rules

| Review Action | Text Diff Detected? | Consecutive Streak Impact | Autonomy Status |
| :--- | :--- | :--- | :--- |
| **Approve** | No | `+1` | Becomes `Eligible` at `20` |
| **Approve** | Yes (edited) | **Reset to 0** | Revoked / Guarded |
| **Edit & Approve** | Yes | **Reset to 0** | Revoked / Guarded |
| **Reject** | Any | **Reset to 0** | Revoked / Guarded |
| **Escalate** | Any | **Reset to 0** | Revoked / Guarded |

> [!IMPORTANT]
> **Safety Notice**: Autonomy eligibility is strictly a readiness metric. Emails are never dispatched automatically without explicit human confirmation.

---

## 📡 API Reference

### 1. `GET /health`
Returns service status, total drafts, and active autonomy statuses across categories.

### 2. `GET /api/emails`
Returns all 55 synthetic customer emails.

### 3. `GET /api/drafts`
Lists suggested drafts. Supports query filters: `?status=pending_review&category=technical_support`.

### 4. `POST /api/drafts/:id/review`
Submits a reviewer action and records audit log.

**Payload:**
```json
{
  "action": "approve",
  "reviewer_id": "Lead Consultant 01",
  "final_reply": "Verified response...",
  "notes": "Verified against DNS documentation."
}
```

### 5. `GET /api/audit`
Returns persistent audit trail with timestamps, diff detection, and streak impacts.

### 6. `GET /api/autonomy`
Returns real-time consecutive approved count and eligibility flag for all 6 categories.
