Implement Task 3: Meeting to Scope for my AI Tech Consultant capstone.

First inspect the existing repository, Task 1 Knowledge Brain API, and Task 2 Inbox Agent. Preserve both existing tasks and their tests. Implement only inside `task3-meeting-to-scope/`, except for documented integration fixes if essential.

## Requirements

### 1. Meeting transcript inputs
- Support three realistic, clearly labelled synthetic client-meeting transcripts.
- Include a follow-up meeting that changes requirements from the first meeting.
- Support long transcripts and preserve source references such as transcript ID, speaker, and line or segment number.
- Never use real customer information.

### 2. Structured requirements extraction
Extract and validate typed JSON containing:
- Business goals and user needs.
- Functional and non-functional requirements.
- Constraints, assumptions, dependencies, and open questions.
- Source references for each requirement.
- Confidence or verification status where appropriate.

Use a modular, multi-agent-style pipeline with distinct stages for extraction, validation, feasibility, scope generation, and change analysis. Make the stages independently testable; do not claim that separate LLM agents were used if the implementation is deterministic.

### 3. Knowledge Brain integration
- Call Task 1's `POST /query` API for relevant feasibility and technical questions.
- Make the API URL configurable.
- Handle timeouts, unavailable services, and abstentions safely.
- Attach source citations to feasibility findings where available.
- Do not duplicate Task 1's knowledge store.

### 4. Scope and proposal generation
Generate a structured project scope containing:
- Objectives and deliverables.
- In-scope and out-of-scope items.
- Assumptions, dependencies, risks, and acceptance criteria.
- Milestones and a transparent estimate with stated assumptions.
- Open questions requiring client confirmation.

Clearly distinguish evidence-based findings from estimates and assumptions. Never present invented effort estimates as verified facts.

### 5. Follow-up change analysis
- Save an initial approved baseline.
- Compare the follow-up transcript with that baseline.
- Classify each change as an addition, modification, removal, or out-of-scope request.
- Cite the relevant original and follow-up transcript segments.
- Show impacts on scope, dependencies, risks, and estimates.
- Require explicit human approval before replacing the approved baseline.

### 6. Human review and persistence
- Provide a simple interface or documented review API to inspect requirements, proposals, and changes.
- Support approve, reject, and request-revision actions.
- Persist approved baselines, review decisions, and change history locally.
- Record timestamps and audit events.

### 7. Evaluation and tests
- Include at least 20 deterministic evaluation cases.
- Test structured extraction, source references, long transcripts, Task 1 failures, scope generation, follow-up changes, change categories, persistence, and approval safeguards.
- Use mocked API responses in tests so they do not require the live website or an API key.
- Run the full test suite and fix failures.

### 8. Documentation and integration
- Add a README with setup instructions, architecture, API usage, limitations, and example outputs.
- Add or update root documentation to explain how Tasks 1, 2, and 3 connect.
- Ensure a straightforward local startup and test procedure.
- Keep credentials out of source control.
- Do not claim Claude integration, model evaluations, image understanding, or live integrations unless actually implemented and verified.

Implement and test the code, not just a plan. Report exact test results, changed files, and remaining gaps. Do not break Task 1 or Task 2.

Implement Task 3: Meeting to Scope for my AI Tech Consultant capstone.

First inspect the existing repository, Task 1 Knowledge Brain API, and Task 2 Inbox Agent. Preserve both existing tasks and their tests. Implement only inside `task3-meeting-to-scope/`, except for documented integration fixes if essential.

## Requirements

### 1. Meeting transcript inputs
- Support three realistic, clearly labelled synthetic client-meeting transcripts.
- Include a follow-up meeting that changes requirements from the first meeting.
- Support long transcripts and preserve source references such as transcript ID, speaker, and line or segment number.
- Never use real customer information.

### 2. Structured requirements extraction
Extract and validate typed JSON containing:
- Business goals and user needs.
- Functional and non-functional requirements.
- Constraints, assumptions, dependencies, and open questions.
- Source references for each requirement.
- Confidence or verification status where appropriate.

Use a modular, multi-agent-style pipeline with distinct stages for extraction, validation, feasibility, scope generation, and change analysis. Make the stages independently testable; do not claim that separate LLM agents were used if the implementation is deterministic.

### 3. Knowledge Brain integration
- Call Task 1's `POST /query` API for relevant feasibility and technical questions.
- Make the API URL configurable.
- Handle timeouts, unavailable services, and abstentions safely.
- Attach source citations to feasibility findings where available.
- Do not duplicate Task 1's knowledge store.

### 4. Scope and proposal generation
Generate a structured project scope containing:
- Objectives and deliverables.
- In-scope and out-of-scope items.
- Assumptions, dependencies, risks, and acceptance criteria.
- Milestones and a transparent estimate with stated assumptions.
- Open questions requiring client confirmation.

Clearly distinguish evidence-based findings from estimates and assumptions. Never present invented effort estimates as verified facts.

### 5. Follow-up change analysis
- Save an initial approved baseline.
- Compare the follow-up transcript with that baseline.
- Classify each change as an addition, modification, removal, or out-of-scope request.
- Cite the relevant original and follow-up transcript segments.
- Show impacts on scope, dependencies, risks, and estimates.
- Require explicit human approval before replacing the approved baseline.

### 6. Human review and persistence
- Provide a simple interface or documented review API to inspect requirements, proposals, and changes.
- Support approve, reject, and request-revision actions.
- Persist approved baselines, review decisions, and change history locally.
- Record timestamps and audit events.

### 7. Evaluation and tests
- Include at least 20 deterministic evaluation cases.
- Test structured extraction, source references, long transcripts, Task 1 failures, scope generation, follow-up changes, change categories, persistence, and approval safeguards.
- Use mocked API responses in tests so they do not require the live website or an API key.
- Run the full test suite and fix failures.

### 8. Documentation and integration
- Add a README with setup instructions, architecture, API usage, limitations, and example outputs.
- Add or update root documentation to explain how Tasks 1, 2, and 3 connect.
- Ensure a straightforward local startup and test procedure.
- Keep credentials out of source control.
- Do not claim Claude integration, model evaluations, image understanding, or live integrations unless actually implemented and verified.

Implement and test the code, not just a plan. Report exact test results, changed files, and remaining gaps. Do not break Task 1 or Task 2.

Let me start by inspecting the current state of the repository before implementing anything.
