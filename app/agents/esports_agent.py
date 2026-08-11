from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool, ToolException, tool

from app.services.exceptions import EsportsDataError

SYSTEM_PROMPT = (
    "You are an esports assistant. Use the available tools — "
    "search_knowledge_base for general knowledge, get_player/get_team/"
    "get_match for structured data. Only state facts a tool actually "
    "returned; if a tool fails or finds nothing, say so plainly instead "
    "of guessing."
)


def _tolerant(base_tool: BaseTool) -> BaseTool:
    """Wrap a tool so domain errors (`EsportsDataError`) surface to the
    agent as a `ToolMessage` instead of crashing the run — without changing
    `base_tool`'s own behavior when invoked directly (Milestone 2/3's
    existing tests keep calling the unwrapped tools)."""

    @tool(base_tool.name, args_schema=base_tool.args_schema, description=base_tool.description)
    def wrapped(**kwargs):
        try:
            return base_tool.invoke(kwargs)
        except EsportsDataError as exc:
            raise ToolException(str(exc)) from exc

    wrapped.handle_tool_error = True
    wrapped.handle_validation_error = True
    return wrapped


def make_esports_agent(llm: BaseChatModel, tools: list[BaseTool]) -> AgentExecutor:
    wrapped_tools = [_tolerant(t) for t in tools]
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )
    agent = create_tool_calling_agent(llm, wrapped_tools, prompt)
    return AgentExecutor(
        agent=agent,
        tools=wrapped_tools,
        return_intermediate_steps=True,
        max_execution_time=60.0,
    )
