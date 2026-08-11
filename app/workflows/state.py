from typing import TypedDict


class InvestigationState(TypedDict):
    question: str
    game: str
    team_name: str | None
    match_id: str | None
    evidence: list[str]
    findings: list[str]
    needs_more_data: bool
    retry_count: int
    final_answer: str | None
