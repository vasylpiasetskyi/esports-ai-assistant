import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from qdrant_client import QdrantClient

from api.schemas import AskRequest, AskResponse, HealthResponse, TaskStartedResponse
from crawler.service import run_crawl
from ingestion.indexer import COLLECTION_NAME
from ingestion.service import run_reindex
from rag.chains import answer_question
from rag.retriever import build_retriever

router = APIRouter()


def get_qdrant_client(request: Request) -> QdrantClient:
    return request.app.state.qdrant_client


def get_embeddings(request: Request) -> Embeddings:
    return request.app.state.embeddings


def get_llm(request: Request) -> BaseChatModel:
    return request.app.state.llm


def get_http_client(request: Request) -> httpx.Client:
    return request.app.state.http_client


@router.post("/ask", response_model=AskResponse)
def ask(
    payload: AskRequest,
    qdrant_client: QdrantClient = Depends(get_qdrant_client),
    embeddings: Embeddings = Depends(get_embeddings),
    llm: BaseChatModel = Depends(get_llm),
) -> AskResponse:
    metadata_filter = {"game": payload.game} if payload.game else None
    retriever = build_retriever(
        qdrant_client,
        embeddings,
        collection_name=COLLECTION_NAME,
        metadata_filter=metadata_filter,
        use_hybrid=payload.use_hybrid,
        use_multi_query=payload.use_multi_query,
        use_compression=payload.use_compression,
        llm=llm,
    )
    result = answer_question(payload.question, retriever, llm)
    return AskResponse(answer=result.answer, sources=result.sources)


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
