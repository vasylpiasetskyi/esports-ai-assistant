import re
from datetime import datetime

from pydantic import BaseModel, Field, model_validator


def slugify(text: str) -> str:
    normalized = text.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    return normalized.strip("_")


class PageSpec(BaseModel):
    game: str
    category: str
    title: str
    slug: str | None = None
    tags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def apply_default_slug(self) -> "PageSpec":
        if self.slug is None:
            self.slug = slugify(self.title)
        return self


class RawPage(BaseModel):
    html: str
    url: str
    retrieved_at: datetime


class RawArticle(BaseModel):
    title: str
    game: str
    category: str
    url: str
    content: str
    updated_at: datetime
    tags: list[str] = Field(default_factory=list)
