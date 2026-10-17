import os
from dotenv import load_dotenv
from fastapi import FastAPI, status
from app.schemas import HealthResponse, QueryRequest, QueryResponse
from app.services.mock_provider import get_ai_provider

# Load environment variables if present
load_dotenv()

app = FastAPI(
    title="AI Tech Consultant - Task 1: Knowledge Brain",
    description=(
        "Vertical slice for Knowledge Brain service. Provides GET /health and POST /query "
        "using a transparent mock AI provider for offline testing and verification."
    ),
    version="0.1.0",
)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Monitoring"],
    summary="Service Health Check",
    description="Returns the health status of the Knowledge Brain service and active provider mode."
)
def get_health() -> HealthResponse:
    provider = os.getenv("AI_PROVIDER", "mock")
    return HealthResponse(
        status="ok",
        service="knowledge-brain",
        provider=provider
    )


@app.post(
    "/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    tags=["Query"],
    summary="Query Knowledge Brain",
    description="Submits a question to the Knowledge Brain. Handled by the mock provider in this vertical slice."
)
def query_knowledge_brain(request: QueryRequest) -> QueryResponse:
    provider = get_ai_provider()
    return provider.query(request.query)
