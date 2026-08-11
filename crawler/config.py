import json
from pathlib import Path

from crawler.models import PageSpec


def load_page_specs(path: Path) -> list[PageSpec]:
    raw_entries = json.loads(path.read_text(encoding="utf-8"))
    return [PageSpec(**entry) for entry in raw_entries]
