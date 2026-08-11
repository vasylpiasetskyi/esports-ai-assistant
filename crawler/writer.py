from pathlib import Path

from crawler.models import RawArticle


class JsonArticleWriter:
    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir

    def save(self, article: RawArticle, slug: str) -> Path:
        target_dir = self._base_dir / article.game / article.category
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / f"{slug}.json"
        target_path.write_text(article.model_dump_json(indent=2), encoding="utf-8")
        return target_path
