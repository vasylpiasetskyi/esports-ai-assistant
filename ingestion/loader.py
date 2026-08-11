import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from langchain_core.documents import Document
from pydantic import ValidationError

from ingestion.models import RawArticleRecord

logger = logging.getLogger(__name__)


def discover_json_files(base_dir: Path) -> list[Path]:
    return sorted(base_dir.rglob("*.json"))


def load_raw_article(path: Path) -> RawArticleRecord:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return RawArticleRecord(**raw)


def to_document(record: RawArticleRecord) -> Document:
    return Document(
        page_content=record.content,
        metadata={
            "game": record.game,
            "category": record.category,
            "title": record.title,
            "url": record.url,
            "updated_at": record.updated_at.isoformat(),
            "tags": record.tags,
        },
    )


@dataclass
class LoadResult:
    documents: list[Document] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)


def load_documents(base_dir: Path) -> LoadResult:
    result = LoadResult()
    for path in discover_json_files(base_dir):
        try:
            record = load_raw_article(path)
        except (json.JSONDecodeError, ValidationError) as error:
            logger.warning("Failed to load %s: %s", path, error)
            result.failed.append((str(path), str(error)))
            continue
        result.documents.append(to_document(record))
    return result
