from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.retrievers import BaseRetriever

from app.rag.chains import NO_CONTEXT_ANSWER, answer_question


class FakeRetriever(BaseRetriever):
    documents: list[Document]

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> list[Document]:
        return self.documents


def test_answer_question_short_circuits_when_no_documents_found():
    retriever = FakeRetriever(documents=[])
    llm = FakeListChatModel(responses=["should not be used"])

    result = answer_question("What is ADR?", retriever, llm)

    assert result.answer == NO_CONTEXT_ANSWER
    assert result.sources == []


def test_answer_question_returns_llm_answer_when_documents_found():
    documents = [
        Document(
            page_content="ADR stands for Average Damage per Round.",
            metadata={"url": "https://liquipedia.net/counterstrike/Economy_Round"},
        )
    ]
    retriever = FakeRetriever(documents=documents)
    llm = FakeListChatModel(responses=["ADR is Average Damage per Round."])

    result = answer_question("What is ADR?", retriever, llm)

    assert result.answer == "ADR is Average Damage per Round."


def test_answer_question_deduplicates_sources_preserving_order():
    documents = [
        Document(page_content="chunk 1", metadata={"url": "https://liquipedia.net/a"}),
        Document(page_content="chunk 2", metadata={"url": "https://liquipedia.net/b"}),
        Document(page_content="chunk 3", metadata={"url": "https://liquipedia.net/a"}),
    ]
    retriever = FakeRetriever(documents=documents)
    llm = FakeListChatModel(responses=["answer"])

    result = answer_question("question", retriever, llm)

    assert result.sources == ["https://liquipedia.net/a", "https://liquipedia.net/b"]
