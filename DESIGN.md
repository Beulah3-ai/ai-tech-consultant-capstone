# System Design — AI Tech Consultant Capstone

## 1. Overview

The AI Tech Consultant Capstone consists of three connected services designed to support technical consulting workflows:

1. **Knowledge Brain:** ingests and searches technical knowledge and returns grounded answers.
2. **Inbox Agent:** classifies customer emails and generates draft responses for human review.
3. **Meeting to Scope:** extracts requirements from meeting transcripts, assesses feasibility, estimates work, and prepares proposals.

The architecture separates knowledge retrieval, email review, and requirements analysis into independent modules. This makes each task testable and allows the services to evolve independently.

The current implementation uses mock or deterministic providers. Live Claude API integration and comparative model benchmarking have not been performed.

## 2. High-Level Architecture

### Components and data flow

**Knowledge Brain**

Website sitemap → bounded page ingestion → HTML extraction → normalized article text → SQLite FTS5 index → retrieval → cited answer or abstention.

**Inbox Agent**

Synthetic customer emails → classification → Knowledge Brain query → grounded draft generation → human review → audit trail and feedback → autonomy eligibility tracking.

**Meeting to Scope**

Meeting transcript → requirement extraction → feasibility assessment using available knowledge → estimation → scope and proposal generation → follow-up change analysis → human approval.

### Service boundaries

The Knowledge Brain exposes a FastAPI interface. The Inbox Agent uses a TypeScript/Node.js service and calls the Knowledge Brain over HTTP. The Meeting-to-Scope pipeline is implemented in Python and organized into separate analysis and proposal modules.

This design avoids tightly coupling email processing or meeting analysis to the internal storage implementation of the Knowledge Brain.

## 3. Task 1 — Knowledge Brain

### Ingestion

The ingestion module discovers pages through a sitemap and processes a bounded number of pages per run. It uses retry handling, checkpoints, canonical URLs, content hashes, and idempotent upserts to make ingestion resumable and reduce duplicate records.

HTML extraction separates article text from surrounding page markup. The service stores searchable content in SQLite and uses SQLite FTS5 for keyword retrieval.

A production ingestion system should additionally verify comprehensive deletion detection, scheduling, rate limits, and incremental synchronization against the source sitemap.

### Retrieval and grounded answers

The retrieval service searches the indexed content and uses retrieved passages to support responses. Answers should include source citations when evidence is available. When the indexed material does not adequately support an answer, the system should abstain or escalate instead of inventing technical information.

The current retrieval implementation uses FTS5 keyword search. Dense embeddings, vector similarity, and a combined keyword-plus-vector retrieval pipeline are not implemented in the current version.

Image understanding and image-derived knowledge have not been validated as implemented capabilities.

### API and persistence

FastAPI exposes endpoints for querying the knowledge service and supporting related workflows. SQLite provides local persistence and searchable indexing, making the prototype easy to run without a separate database server.

## 4. Task 2 — Inbox Agent

### Classification and drafting

The Inbox Agent processes a dataset of 55 synthetic emails spanning technical support, billing, onboarding, feature requests, account configuration, and out-of-scope requests.

The draft-generation workflow consults the Knowledge Brain through an HTTP client. If the knowledge service is unavailable, the client handles the failure and uses the configured fallback behavior rather than assuming that a successful knowledge lookup occurred.

Drafts are intended for review, not automatic delivery. The application supports approving an unchanged draft, editing and approving a draft, rejecting a draft, and escalating an email.

### Human review and auditability

Review decisions are recorded with relevant reviewer information, timestamps, and change information. Feedback and audit records support later analysis of draft quality and review outcomes.

An autonomy safeguard tracks consecutive unchanged approvals by category. A category becomes eligible for consideration after 20 consecutive unchanged approvals. Eligibility does not itself authorize or execute automatic email sending.

The current prototype uses synthetic email data. Live mailbox ingestion and external email delivery are not implemented.

## 5. Task 3 — Meeting to Scope

### Modular pipeline

The Meeting-to-Scope service separates the workflow into dedicated modules:

- **Transcript analyst:** identifies requirements from meeting content.
- **Scope agent:** organizes requirements into a structured scope.
- **Feasibility agent:** checks requirements against available knowledge and records limitations.
- **Estimation agent:** produces estimates using the implemented estimation rules.
- **Proposal agent:** assembles scope and estimation outputs into a proposal.
- **Change analyst:** compares follow-up requirements with the approved baseline and identifies changes.

This modular approach makes individual stages independently testable and provides a clear place to improve each stage.

### Follow-up and approval

The workflow must preserve the approved baseline when a follow-up transcript arrives. Changes are analyzed relative to that baseline and categorized according to the implemented change-analysis rules.

A revised scope should not silently replace an approved scope. The approval workflow preserves human oversight over consequential scope changes.

The current pipeline uses mock or deterministic processing rather than a live Claude-powered multi-agent system. Production-grade model orchestration and independently benchmarked long-context handling remain future work.

## 6. Reliability, Safety, and Failure Handling

The implementation emphasizes:

- Bounded ingestion and resumable processing.
- Retry and error handling in ingestion and service calls.
- Idempotent content updates.
- Grounded answers with citations and abstention behavior.
- Explicit human review for customer-facing drafts.
- Audit records for review decisions.
- A threshold-based autonomy eligibility safeguard.
- Approval before accepting consequential scope changes.
- Automated tests for core modules and API workflows.

Failures should be visible and handled conservatively. For example, an unavailable knowledge service must not be represented as a successful evidence lookup, and an unsupported technical question should not receive a fabricated answer.

## 7. Evaluation and Model Strategy

Automated tests validate implemented behavior and expected failure paths. Task 1 and Task 3 use Python tests; Task 2 uses TypeScript tests and a build check.

The current project does not claim measured superiority of one language model over another. Claude API integration and live model-comparison evaluations remain unperformed. Any future comparison should measure answer quality, citation correctness, classification performance, latency, reliability, and cost on the same evaluation cases.

## 8. Known Limitations and Next Steps

The current project is a locally testable prototype, not a fully deployed production service. Key improvements include:

1. Add embedding-based retrieval and evaluate hybrid search.
2. Implement and test image understanding and image-derived evidence.
3. Verify incremental deletion detection and scheduled ingestion.
4. Add live model integration with secure secret management.
5. Implement and evaluate the required MCP/tool-calling workflows where applicable.
6. Run reproducible model comparisons using fixed evaluation datasets.
7. Add deployment configuration, operational monitoring, and production security controls.

These limitations are documented explicitly so that implemented functionality can be distinguished from proposed future capabilities.