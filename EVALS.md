# Evaluation Report — AI Tech Consultant Capstone

## 1. Evaluation Approach

The project uses automated software tests to check implemented functionality, API behavior, review workflows, and failure handling. These results demonstrate test coverage for the current prototype; they do not establish production readiness or prove that one language model performs better than another.

The current implementation uses mock or deterministic providers. Live Claude API evaluations and quantitative comparisons between language models have **not been run**.

## 2. Automated Test Results

The following results were observed when running the task-specific test suites during development.

| Component | Test command | Result |
|---|---|---:|
| Knowledge Brain | `python -m pytest task1-knowledge-brain/tests -v` | 32 passed |
| Inbox Agent | `npm test` (inside `task2-inbox-agent`) | 35 passed |
| Meeting to Scope | `python -m pytest task3-meeting-to-scope/tests -v` | 76 passed |
| **Total** | Three task-specific suites | **143 passed** |

Task 1 and Task 3 each reported a Starlette deprecation warning related to the HTTP test-client dependency. Task 2's TypeScript build was also run successfully with `npm run build`.

These results reflect the recorded test runs. Re-run the suites before submission if any source code or dependencies change.

## 3. Task 1 — Knowledge Brain

The automated tests cover core API behavior, HTML extraction, ingestion behavior, retrieval, and escalation.

Evaluation focus:
- API response behavior and input validation.
- Extraction of useful text from HTML.
- Ingestion retries, checkpoints, and idempotent updates.
- Keyword retrieval and source-grounded responses.
- Abstention or escalation when evidence is insufficient.

**Known limitations:** The current retrieval system uses SQLite FTS5 keyword search. Dense vector embeddings, hybrid vector retrieval, and image-understanding evaluation have not been demonstrated. The recorded 32 passing tests are software tests, not an evaluation of live Claude responses.

## 4. Task 2 — Inbox Agent

The automated tests cover email review behavior, API workflows, draft processing, audit records, and autonomy safeguards.

Evaluation focus:
- Handling of synthetic emails across supported categories.
- Knowledge-service integration and fallback behavior.
- Review actions: approve, edit and approve, reject, or escalate.
- Recording of review decisions and audit information.
- Tracking the threshold of 20 consecutive unchanged approvals per category.
- TypeScript compilation.

**Known limitations:** The dataset contains 55 synthetic emails. No live mailbox connection, external email delivery, or autonomous sending is implemented. The autonomy threshold indicates eligibility only; it does not trigger email delivery.

## 5. Task 3 — Meeting to Scope

The automated tests cover transcript analysis, scope generation, estimation, feasibility handling, change analysis, pipeline integration, and approval behavior.

Evaluation focus:
- Structured requirement extraction from transcript content.
- Separation of transcript analysis, feasibility, estimation, and proposal stages.
- Handling of follow-up changes against an approved baseline.
- Preservation of approval requirements.
- Graceful handling of unavailable or insufficient feasibility evidence.

**Known limitations:** The current pipeline uses mock or deterministic processing. Live Claude-based multi-agent orchestration and a comparative long-context model evaluation have not been run.

## 6. Model Comparison and Measurement Plan

No model-comparison metrics are reported because live model evaluations have not been performed. A future evaluation should use the same fixed dataset and scoring rubric for each candidate model and configuration.

Recommended measurements:
- **Quality:** correctness, completeness, and adherence to structured output requirements.
- **Grounding:** citation correctness and unsupported-claim rate.
- **Classification:** precision, recall, and F1 score.
- **Reliability:** valid structured-output rate, failure rate, and successful retry rate.
- **Performance:** median and p95 latency.
- **Cost:** measured API cost per case and per successful result.

Use 20–30 evaluation cases for each model-choice decision and at least 20 task-specific cases for each major workflow. Report sample size, model and configuration, scoring method, failures, latency, and measured cost. Do not substitute assumed or fabricated numbers for measured results.

## 7. Summary

The current prototype