import json
import logging

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage

from app.services.exceptions import EsportsDataError

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
