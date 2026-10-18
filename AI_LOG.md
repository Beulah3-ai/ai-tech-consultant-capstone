# AI Development Log — AI Tech Consultant Capstone

## AI Tools and Development Approach

AI coding assistance was used during implementation, debugging, test development, and documentation. The application itself currently uses mock or deterministic providers; live Claude API integration has not been completed. The prompts below summarize the development tasks and should be checked against the retained coding-agent conversation history.

## Five Useful Coding Prompts

1. **Knowledge Brain ingestion**
   - Design a Python/FastAPI knowledge ingestion service that reads a sitemap, extracts article text, handles retries and checkpoints, and supports idempotent updates.
   - Intended result: a modular ingestion pipeline with automated tests.

2. **Grounded retrieval**
   - Implement searchable knowledge retrieval that returns source-supported answers and abstains or escalates when the indexed evidence is insufficient.
   - Intended result: a retrieval service with citations and failure-path tests.

3. **Inbox Agent workflow**
   - Build a TypeScript email-review workflow that classifies synthetic emails, queries the Knowledge Brain, generates draft responses, and supports approval, editing, rejection, and escalation.
   - Intended result: a review interface and auditable decision workflow.

4. **Autonomy safeguard**
   - Add a per-category safeguard that requires 20 consecutive unchanged approved drafts before marking a category eligible for autonomy, resetting the streak when a draft is edited, rejected, or escalated.
   - Intended result: eligibility tracking without automatic email delivery.

5. **Meeting-to-Scope pipeline**
   - Create modular transcript-analysis, scope, feasibility, estimation, proposal, and change-analysis stages. Compare follow-up requirements against an approved baseline and retain human approval for scope changes.
   - Intended result: structured pipeline outputs and automated tests.

## Rejected or Corrected AI-Generated Result

During Task 3 development, a generated schema change used:

`model_config = model_config(frozen=True)`

This raised a `NameError` because `model_config` was not defined as a callable. The code was corrected to use the Pydantic v2 configuration form:

`model_config = {"frozen": True}`

The Task 3 test suite subsequently passed with 76 tests. This example illustrates why generated code must be checked against the installed library version and validated through execution and tests.

## Validation and Limitations

- Task 1: 32 recorded passing tests.
- Task 2: 35 recorded passing tests; TypeScript build completed successfully.
- Task 3: 76 recorded passing tests.
- Live Claude API calls and quantitative comparisons between models were not performed.
- The prompts above are concise summaries of development requests, not verbatim transcripts. The retained coding-agent history should be used to verify the exact wording before submission.

