import json
import logging
import os

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from qdrant_client import QdrantClient

from app.rag.service import RAGService
from app.services.data_source import MockEsportsDataSource
from app.services.exceptions import EsportsDataError
from app.services.match_service import MatchService
from app.services.player_service import PlayerService
from app.services.team_service import TeamService
from app.tools.knowledge import make_search_knowledge_base_tool
from app.tools.match import make_get_match_tool
from app.tools.player import make_get_player_tool
from app.tools.team import make_get_team_tool
from ingestion.indexer import COLLECTION_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run(
    llm: BaseChatModel,
    tools: list,
    question: str,
    *,
    max_iterations: int = 5,
) -> list[BaseMessage]:
    tools_by_name = {tool.name: tool for tool in tools}
    llm_with_tools = llm.bind_tools(tools)
    messages: list[BaseMessage] = [HumanMessage(question)]

    for _ in range(max_iterations):
        ai_message = llm_with_tools.invoke(messages)
        messages.append(ai_message)

        if not ai_message.tool_calls:
            break

        for tool_call in ai_message.tool_calls:
            tool = tools_by_name[tool_call["name"]]
            try:
                result = tool.invoke(tool_call["args"])
                content = json.dumps(result)
            except EsportsDataError as exc:
                content = f"Error: {exc}"
            messages.append(ToolMessage(content=content, tool_call_id=tool_call["id"]))

    return messages


EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"
DEFAULT_QDRANT_URL = "http://localhost:6333"


def main() -> None:
    data_source = MockEsportsDataSource()
    qdrant_client = QdrantClient(url=os.environ.get("QDRANT_URL", DEFAULT_QDRANT_URL))
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    llm = ChatOpenAI(model=CHAT_MODEL)
    rag_service = RAGService(qdrant_client, embeddings, llm, collection_name=COLLECTION_NAME)

    tools = [
        make_get_player_tool(PlayerService(data_source)),
        make_get_team_tool(TeamService(data_source)),
        make_get_match_tool(MatchService(data_source)),
        make_search_knowledge_base_tool(rag_service),
    ]

    print("Type a question (empty line to quit):")
    while True:
        question = input("> ").strip()
        if not question:
            break
        for message in run(llm, tools, question):
            print(f"[{message.__class__.__name__}] {message.content}")
        print()


if __name__ == "__main__":
    main()
