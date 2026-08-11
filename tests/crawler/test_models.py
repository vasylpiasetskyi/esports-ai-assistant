from datetime import UTC, datetime

from crawler.models import PageSpec, RawArticle, RawPage, slugify


def test_slugify_lowercases_and_replaces_spaces():
    assert slugify("Natus Vincere") == "natus_vincere"


def test_slugify_strips_punctuation():
    assert slugify("What's ADR?") == "what_s_adr"


def test_page_spec_defaults_slug_from_title():
    spec = PageSpec(game="cs2", category="teams", title="Natus Vincere", tags=["team"])
    assert spec.slug == "natus_vincere"


def test_page_spec_keeps_explicit_slug():
    spec = PageSpec(game="cs2", category="teams", title="Natus Vincere", slug="navi", tags=["team"])
    assert spec.slug == "navi"


def test_raw_page_holds_fetched_content():
    page = RawPage(
        html="<p>hi</p>",
        url="https://liquipedia.net/x",
        retrieved_at=datetime.now(UTC),
    )
    assert page.html == "<p>hi</p>"


def test_raw_article_matches_tdd_schema_fields():
    article = RawArticle(
        title="Natus Vincere",
        game="cs2",
        category="teams",
        url="https://liquipedia.net/counterstrike/Natus_Vincere",
        content="Natus Vincere is a team from Ukraine.",
        updated_at=datetime.now(UTC),
        tags=["team", "ukraine"],
    )
    dumped = article.model_dump()
    assert set(dumped.keys()) == {
        "title",
        "game",
        "category",
        "url",
        "content",
        "updated_at",
        "tags",
    }
