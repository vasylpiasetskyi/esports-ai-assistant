from datetime import datetime

from pydantic import BaseModel, Field


class RawArticleRecord(BaseModel):
    title: str
    game: str
    category: str
    url: str
    content: str
    updated_at: datetime
    tags: list[str] = Field(default_factory=list)
