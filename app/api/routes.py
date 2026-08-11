import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from langchain_classic.agents import AgentExecutor
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from qdrant_client import QdrantClient

from app.agents.esports_agent import make_esports_agent
from app.api.schemas import (
    AskRequest,
    AskResponse,
    AssistantRequest,
    AssistantResponse,
    HealthResponse,
    TaskStartedResponse,
)
from app.rag.service import RAGService
from app.services.data_source import MockEsportsDataSource
from app.services.match_service import MatchService
from app.services.player_service import PlayerService
from app.services.team_service import TeamService
from app.tools.knowledge import make_search_knowledge_base_tool
from app.tools.match import make_get_match_tool
from app.tools.player import make_get_player_tool
from app.tools.team import make_get_team_tool
from crawler.service import run_crawl
from ingestion.service import run_reindex

router = APIRouter()


def get_qdrant_client(request: Request) -> QdrantClient:
    return request.app.state.qdrant_client


def get_embeddings(request: Request) -> Embeddings:
    return request.app.state.embeddings


def get_llm(request: Request) -> BaseChatModel:
    return request.app.state.llm


def get_http_client(request: Request) -> httpx.Client:
    return request.app.state.http_client


def get_rag_service(
    qdrant_client: QdrantClient = Depends(get_qdrant_client),
    embeddings: Embeddings = Depends(get_embeddings),
    llm: BaseChatModel = Depends(get_llm),
) -> RAGService:
    return RAGService(qdrant_client, embeddings, llm)


@router.post("/ask", response_model=AskResponse)
def ask(
    payload: AskRequest,
    rag_service: RAGService = Depends(get_rag_service),
) -> AskResponse:
    result = rag_service.answer(
        payload.question,
        payload.game,
        use_hybrid=payload.use_hybrid,
        use_multi_query=payload.use_multi_query,
        use_compression=payload.use_compression,
    )
    return AskResponse(answer=result.answer, sources=result.sources)


def get_agent(
    qdrant_client: QdrantClient = Depends(get_qdrant_client),
    embeddings: Embeddings = Depends(get_embeddings),
    llm: BaseChatModel = Depends(get_llm),
) -> AgentExecutor:
    data_source = MockEsportsDataSource()
    rag_service = RAGService(qdrant_client, embeddings, llm)
    tools = [
        make_get_player_tool(PlayerService(data_source)),
        make_get_team_tool(TeamService(data_source)),
        make_get_match_tool(MatchService(data_source)),
        make_search_knowledge_base_tool(rag_service),
    ]
    return make_esports_agent(llm, tools)


@router.post("/assistant", response_model=AssistantResponse)
def assistant(
    payload: AssistantRequest,
    agent: AgentExecutor = Depends(get_agent),
) -> AssistantResponse:
    input_text = (
        payload.question if payload.game is None else f"{payload.question} (Game: {payload.game})"
    )
    result = agent.invoke({"input": input_text})

    sources: list[str] = []
    for action, observation in result["intermediate_steps"]:
        if action.tool == "search_knowledge_base" and isinstance(observation, dict):
            for url in observation.get("sources", []):
                if url not in sources:
                    sources.append(url)

    return AssistantResponse(answer=result["output"], sources=sources)


@router.post("/crawl", status_code=202, response_model=TaskStartedResponse)
def crawl(
    background_tasks: BackgroundTasks,
    request: Request,
    http_client: httpx.Client = Depends(get_http_client),
) -> TaskStartedResponse:
    if getattr(request.app.state, "is_crawling", False):
        raise HTTPException(status_code=409, detail="A crawl is already in progress")
    request.app.state.is_crawling = True

    def _run() -> None:
        try:
            run_crawl(http_client=http_client)
        finally:
            request.app.state.is_crawling = False

    background_tasks.add_task(_run)
    return TaskStartedResponse(status="started")


@router.post("/reindex", status_code=202, response_model=TaskStartedResponse)
def reindex(
    background_tasks: BackgroundTasks,
    qdrant_client: QdrantClient = Depends(get_qdrant_client),
    embeddings: Embeddings = Depends(get_embeddings),
) -> TaskStartedResponse:
    background_tasks.add_task(run_reindex, embeddings=embeddings, client=qdrant_client)
    return TaskStartedResponse(status="started")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")
