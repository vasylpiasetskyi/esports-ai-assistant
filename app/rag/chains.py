from dataclasses import dataclass, field

from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.retrievers import BaseRetriever

from app.rag.prompts import RAG_PROMPT

NO_CONTEXT_ANSWER = "I don't have enough information to answer that question."


@dataclass
class RagAnswer:
    answer: str
    sources: list[str] = field(default_factory=list)


def _format_context(documents: list[Document]) -> str:
    return "\n\n".join(document.page_content for document in documents)


def _extract_sources(documents: list[Document]) -> list[str]:
    seen: set[str] = set()
    sources: list[str] = []
    for document in documents:
        url = document.metadata.get("url")
        if url and url not in seen:
            seen.add(url)
            sources.append(url)
    return sources


def answer_question(question: str, retriever: BaseRetriever, llm: BaseChatModel) -> RagAnswer:
    documents = retriever.invoke(question)
    if not documents:
        return RagAnswer(answer=NO_CONTEXT_ANSWER, sources=[])

    chain = RAG_PROMPT | llm | StrOutputParser()
    answer_text = chain.invoke({"context": _format_context(documents), "question": question})
    return RagAnswer(answer=answer_text, sources=_extract_sources(documents))
