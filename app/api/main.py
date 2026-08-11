import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from qdrant_client import QdrantClient

from app.api.routes import router

EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"
DEFAULT_QDRANT_URL = "http://localhost:6333"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.qdrant_client = QdrantClient(url=os.environ.get("QDRANT_URL", DEFAULT_QDRANT_URL))
    app.state.embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    app.state.llm = ChatOpenAI(model=CHAT_MODEL)
    app.state.http_client = httpx.Client()
    app.state.is_crawling = False
    yield
    app.state.http_client.close()


app = FastAPI(lifespan=lifespan)
app.include_router(router)
