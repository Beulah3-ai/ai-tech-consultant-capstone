"""Pydantic v2 schemas for Task 3: Meeting to Scope pipeline."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class RequirementType(str, Enum):
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    CONSTRAINT = "constraint"
    ASSUMPTION = "assumption"
    OPEN_QUESTION = "open_question"
    BUSINESS_GOAL = "business_goal"
    USER_NEED = "user_need"
    DEPENDENCY = "dependency"


class VerificationStatus(str, Enum):
    UNVERIFIED = "unverified"
    CONFIRMED = "confirmed"
    CONFLICTING = "conflicting"
    INFEASIBLE = "infeasible"


class ChangeType(str, Enum):
    ADDITION = "addition"
    MODIFICATION = "modification"
    REMOVAL = "removal"
    OUT_OF_SCOPE = "out_of_scope"


class ApprovalAction(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_REVISION = "request_revision"


class ProposalStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"


# ---------------------------------------------------------------------------
# Source reference
# ---------------------------------------------------------------------------


class TranscriptSegmentRef(BaseModel):
    """Pinpoints the exact transcript segment that supports a finding."""

    model_config = {"frozen": True}

    transcript_id: str
    segment_id: str
    line_number: int
    speaker: str


# ---------------------------------------------------------------------------
# Extracted requirements
# ---------------------------------------------------------------------------


class ExtractedRequirement(BaseModel):
    """A single requirement extracted from a meeting transcript."""

    req_id: str
    req_type: RequirementType
    description: str
    sources: List[TranscriptSegmentRef] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    tags: List[str] = Field(default_factory=list)

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("description must not be empty")
        return v


class RequirementsDocument(BaseModel):
    """Full structured requirements extracted from one transcript."""

    transcript_id: str
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    business_goals: List[ExtractedRequirement] = Field(default_factory=list)
    user_needs: List[ExtractedRequirement] = Field(default_factory=list)
    functional_requirements: List[ExtractedRequirement] = Field(default_factory=list)
    non_functional_requirements: List[ExtractedRequirement] = Field(default_factory=list)
    constraints: List[ExtractedRequirement] = Field(default_factory=list)
    assumptions: List[ExtractedRequirement] = Field(default_factory=list)
    dependencies: List[ExtractedRequirement] = Field(default_factory=list)
    open_questions: List[ExtractedRequirement] = Field(default_factory=list)

    def all_requirements(self) -> List[ExtractedRequirement]:
        return (
            self.business_goals
            + self.user_needs
            + self.functional_requirements
            + self.non_functional_requirements
            + self.constraints
            + self.assumptions
            + self.dependencies
            + self.open_questions
        )


# ---------------------------------------------------------------------------
# Feasibility
# ---------------------------------------------------------------------------


class FeasibilityFinding(BaseModel):
    """Result of a Knowledge Brain query for a single technical question."""

    question: str
    kb_answer: Optional[str] = None
    answered: bool
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    is_mock: bool = False
    error: Optional[str] = None
    disclaimer: Optional[str] = None


# ---------------------------------------------------------------------------
# Scope document
# ---------------------------------------------------------------------------


class ScopeItem(BaseModel):
    description: str
    source_req_ids: List[str] = Field(default_factory=list)
    feasibility_note: Optional[str] = None


class ScopeDocument(BaseModel):
    transcript_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    objectives: List[str] = Field(default_factory=list)
    deliverables: List[ScopeItem] = Field(default_factory=list)
    in_scope: List[ScopeItem] = Field(default_factory=list)
    out_of_scope: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Estimation
# ---------------------------------------------------------------------------


class EstimationItem(BaseModel):
    task: str
    low_hours: float = Field(ge=0)
    likely_hours: float = Field(ge=0)
    high_hours: float = Field(ge=0)
    assumptions: List[str] = Field(default_factory=list)
    source_deliverable: Optional[str] = None

    @field_validator("high_hours")
    @classmethod
    def high_gte_likely(cls, v: float, info: Any) -> float:
        likely = info.data.get("likely_hours", 0)
        if v < likely:
            raise ValueError("high_hours must be >= likely_hours")
        return v


# ---------------------------------------------------------------------------
# Proposal
# ---------------------------------------------------------------------------


class Milestone(BaseModel):
    name: str
    week: int
    deliverables: List[str] = Field(default_factory=list)


class ProposalDocument(BaseModel):
    proposal_id: str
    version: str
    transcript_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    scope: ScopeDocument
    estimation_items: List[EstimationItem] = Field(default_factory=list)
    milestones: List[Milestone] = Field(default_factory=list)
    total_low_hours: float = 0.0
    total_likely_hours: float = 0.0
    total_high_hours: float = 0.0
    caveats: List[str] = Field(default_factory=list)
    status: ProposalStatus = ProposalStatus.DRAFT
    consistency_warnings: List[str] = Field(default_factory=list)

    # Explicitly never claim Claude produced this
    provider: str = "deterministic_pipeline"
    is_mock: bool = True


# ---------------------------------------------------------------------------
# Change analysis
# ---------------------------------------------------------------------------


class ChangeRecord(BaseModel):
    change_type: ChangeType
    description: str
    original_ref: Optional[TranscriptSegmentRef] = None
    followup_ref: Optional[TranscriptSegmentRef] = None
    scope_impact: str = ""
    estimate_impact: str = ""


class RevisedEstimateItem(BaseModel):
    task: str
    reason: str
    low_hours: float
    likely_hours: float
    high_hours: float


class ChangeAnalysis(BaseModel):
    baseline_proposal_id: str
    baseline_version: str
    followup_transcript_id: str
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    changes: List[ChangeRecord] = Field(default_factory=list)
    scope_delta_summary: str = ""
    revised_estimates: List[RevisedEstimateItem] = Field(default_factory=list)
    status: ProposalStatus = ProposalStatus.DRAFT


# ---------------------------------------------------------------------------
# Human review / approval
# ---------------------------------------------------------------------------


class ApprovalRequest(BaseModel):
    action: ApprovalAction
    reviewer_id: str = Field(min_length=1)
    notes: Optional[str] = None


class ApprovalRecord(BaseModel):
    document_id: str
    version: str
    action: ApprovalAction
    reviewer_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# API request / response wrappers
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "task3-meeting-to-scope"
    provider: str = "deterministic_pipeline"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ProcessTranscriptRequest(BaseModel):
    knowledge_brain_url: Optional[str] = None  # override env default if supplied


class ProcessTranscriptResponse(BaseModel):
    proposal_id: str
    version: str
    transcript_id: str
    status: ProposalStatus
    proposal: ProposalDocument


class CompareTranscriptsResponse(BaseModel):
    change_analysis: ChangeAnalysis


class AuditEntry(BaseModel):
    document_id: str
    version: str
    action: str
    reviewer_id: str
    timestamp: str
    notes: Optional[str] = None
