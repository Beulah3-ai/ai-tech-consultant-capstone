import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from app.db import init_db, get_db_connection
from app.schemas import (
    HealthResponse,
    QueryRequest,
    QueryResponse,
    IngestionRunRequest,
    IngestionRunResponse,
    IngestionStatusResponse,
    EscalationCreateRequest,
    EscalationResolveRequest,
    EscalationResponse,
)
from app.services.mock_provider import get_ai_provider
from app.services.ingestion import IngestionService
from app.services.escalation import EscalationService

# Load environment variables if present
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database tables and indexes exist on startup
    init_db()
    yield


app = FastAPI(
    title="AI Tech Consultant - Task 1: Knowledge Brain",
    description=(
        "Production-ready vertical slice for Knowledge Brain service. "
        "Provides website ingestion, SQLite FTS5 grounded retrieval, fallback mock responses, "
        "and human expert escalation workflows."
    ),
    version="0.2.0",
    lifespan=lifespan,
)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Monitoring"],
    summary="Service Health Check",
    description="Returns the health status of the Knowledge Brain service, active provider mode, and article count.",
)
def get_health() -> HealthResponse:
    provider = os.getenv("AI_PROVIDER", "mock")
    total_articles = 0
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS count FROM articles WHERE status = 'active'")
            total_articles = cursor.fetchone()["count"]
    except Exception:
        total_articles = 0

    return HealthResponse(
        status="ok",
        service="knowledge-brain",
        provider=provider,
        total_articles=total_articles,
    )


@app.post(
    "/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    tags=["Query"],
    summary="Query Knowledge Brain",
    description=(
        "Submits a question to the Knowledge Brain. Uses the configured provider "
        "('local_retrieval' or 'mock') to produce grounded answers or explicit abstentions."
    ),
)
def query_knowledge_brain(request: QueryRequest) -> QueryResponse:
    provider = get_ai_provider(provider_type=request.provider)
    return provider.query(request.query)


@app.post(
    "/ingestion/run",
    response_model=IngestionRunResponse,
    status_code=status.HTTP_200_OK,
    tags=["Ingestion"],
    summary="Run Ingestion Pipeline",
    description="Runs a bounded, polite, and resumable ingestion of the Brilliant Directories sitemap.",
)
def run_ingestion(request: IngestionRunRequest = IngestionRunRequest()) -> IngestionRunResponse:
    service = IngestionService()
    result = service.run(
        sitemap_url=request.sitemap_url,
        max_pages=request.max_pages,
        rate_limit_delay_seconds=request.rate_limit_delay_seconds,
        force_resync=request.force_resync,
    )
    return IngestionRunResponse(**result)


@app.get(
    "/ingestion/status",
    response_model=IngestionStatusResponse,
    tags=["Ingestion"],
    summary="Get Ingestion Status",
    description="Reports the progress, timestamps, counts, and recent errors of ingestion runs.",
)
def get_ingestion_status() -> IngestionStatusResponse:
    service = IngestionService()
    status_data = service.get_status()
    return IngestionStatusResponse(**status_data)


@app.post(
    "/escalations",
    response_model=EscalationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Escalations"],
    summary="Create Question Escalation",
    description="Records an unanswered query or edge case for human consultant review.",
)
def create_escalation(request: EscalationCreateRequest) -> EscalationResponse:
    service = EscalationService()
    record = service.create(
        query=request.query,
        reason=request.reason,
        context=request.context,
    )
    return EscalationResponse(**record)


@app.post(
    "/escalations/{escalation_id}/resolve",
    response_model=EscalationResponse,
    status_code=status.HTTP_200_OK,
    tags=["Escalations"],
    summary="Resolve Question Escalation",
    description="Records an expert verified answer and marks the escalation as resolved.",
)
def resolve_escalation(escalation_id: str, request: EscalationResolveRequest) -> EscalationResponse:
    service = EscalationService()
    updated = service.resolve(
        escalation_id=escalation_id,
        expert_answer=request.expert_answer,
        resolved_by=request.resolved_by,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Escalation with ID '{escalation_id}' not found.",
        )
    return EscalationResponse(**updated)
