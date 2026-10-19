# AI Tech Consultant Capstone

An AI-powered tech consultant platform combining three connected workflows: knowledge retrieval, customer email triage, and meeting-to-scope automation.

## Projects

1. **Knowledge Brain** — Python/FastAPI service for website ingestion, searchable knowledge, grounded answers, citations, and escalation.
2. **Inbox Agent** — TypeScript/Node.js workflow for email classification, knowledge-grounded reply drafts, human review, audit trails, and autonomy safeguards.
3. **Meeting to Scope** — Python/FastAPI pipeline for extracting requirements from meeting transcripts, checking feasibility, estimating scope, generating proposals, and reviewing follow-up changes.

## Technology

Python, FastAPI, TypeScript, Node.js, SQLite FTS5, Pydantic, REST APIs, automated tests, and mock/deterministic model providers.

## Current Implementation Status

The current implementation uses mock/deterministic providers. Live Claude API integration and model-comparison benchmarks have not been run. See `DESIGN.md`, `EVALS.md`, and `AI_LOG.md` for architecture, evaluation results, and AI-development notes.

## Repository Structure

- `task1-knowledge-brain/` — Knowledge Brain API and tests
- `task2-inbox-agent/` — Inbox Agent and review workflow
- `task3-meeting-to-scope/` — Meeting-to-Scope pipeline and tests
- `docs/conversation_history/` — Available development conversation records

## Running Tests

Run each task's tests using the instructions in its directory README. Task 1 and Task 3 use `pytest`; Task 2 uses `npm test` and `npm run build`.

## Safety

Human review is required for consequential email decisions and scope changes. The current implementation does not send customer emails autonomously.


Deployed Links: 

Task 1: https://ai-tech-consultant-capstone-mdk0.onrender.com 
Task 2: https://ai-tech-consultant-capstone-1-n2xr.onrender.com 
Task 3: https://ai-tech-consultant-task3-b2pq.onrender.com/docs
