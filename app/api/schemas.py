from pydantic import BaseModel


class AskRequest(BaseModel):
    question: str
    game: str | None = None
    use_hybrid: bool = False
    use_multi_query: bool = False
    use_compression: bool = False


class AskResponse(BaseModel):
    answer: str
    sources: list[str]


class AssistantRequest(BaseModel):
    question: str
    game: str | None = None


class AssistantResponse(BaseModel):
    answer: str
    sources: list[str]


class HealthResponse(BaseModel):
    status: str


class TaskStartedResponse(BaseModel):
    status: str
