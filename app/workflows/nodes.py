from typing import Literal

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field

from app.rag.service import RAGService
from app.services.exceptions import MatchNotFoundError
from app.services.match_service import MatchService
from app.workflows.state import InvestigationState

MAX_RETRIES = 1


class QuestionAnalysis(BaseModel):
    game: str = Field(description="Game slug, e.g. 'cs2', 'dota2', 'lol', 'valorant'.")
    team_name: str = Field(description="The team the question is about, e.g. 'NAVI'.")


def make_analyze_question_node(llm: BaseChatModel):
    structured_llm = llm.with_structured_output(QuestionAnalysis)

    def analyze_question(state: InvestigationState) -> dict:
        analysis = structured_llm.invoke(state["question"])
        return {
            "game": state["game"] or analysis.game,
            "team_name": analysis.team_name,
        }

    return analyze_question


def make_get_match_node(match_service: MatchService):
    def get_match(state: InvestigationState) -> dict:
        try:
            match = match_service.get_latest_match_for_team(state["game"], state["team_name"])
        except MatchNotFoundError as exc:
            return {"evidence": [*state["evidence"], f"Error: {exc}"]}
        evidence_line = (
            f"Match {match.match_id}: {match.teams[0]} vs {match.teams[1]}, "
            f"score {match.score}, status {match.status}, {match.tournament} on {match.date}."
        )
        return {"match_id": match.match_id, "evidence": [*state["evidence"], evidence_line]}

    return get_match


def make_get_match_data_node(match_service: MatchService):
    def get_match_data(state: InvestigationState) -> dict:
        if state["match_id"] is None:
            return {}
        match = match_service.get_match(state["game"], state["match_id"])
        home, away = match.teams[0], match.teams[1]
        home_score, away_score = (int(part) for part in match.score.split("-"))
        if home_score == away_score:
            outcome = f"{home} and {away} drew {match.score}."
        else:
            winner, loser = (home, away) if home_score > away_score else (away, home)
            outcome = f"{winner} beat {loser} {match.score}."
        return {"evidence": [*state["evidence"], outcome]}

    return get_match_data


def make_retrieve_knowledge_node(rag_service: RAGService):
    def retrieve_knowledge(state: InvestigationState) -> dict:
        game_filter = None if state["retry_count"] > 0 else (state["game"] or None)
        result = rag_service.answer(state["question"], game_filter)
        return {"evidence": [*state["evidence"], result.answer]}

    return retrieve_knowledge


class EvidenceAnalysis(BaseModel):
    sufficient: bool = Field(description="Whether the evidence is enough to explain the outcome.")
    findings: list[str] = Field(description="Key findings distilled from the evidence.")


def make_analyze_evidence_node(llm: BaseChatModel):
    structured_llm = llm.with_structured_output(EvidenceAnalysis)

    def analyze_evidence(state: InvestigationState) -> dict:
        prompt = "Question: {}\nEvidence:\n{}".format(
            state["question"],
            "\n".join(f"- {item}" for item in state["evidence"]),
        )
        analysis = structured_llm.invoke(prompt)
        return {
            "findings": analysis.findings,
            "needs_more_data": not analysis.sufficient,
            "retry_count": state["retry_count"] + (0 if analysis.sufficient else 1),
        }

    return analyze_evidence


def route_after_analysis(
    state: InvestigationState,
) -> Literal["generate_report", "retrieve_knowledge"]:
    if state["needs_more_data"] and state["retry_count"] <= MAX_RETRIES:
        return "retrieve_knowledge"
    return "generate_report"


def make_generate_report_node(llm: BaseChatModel):
    def generate_report(state: InvestigationState) -> dict:
        prompt = (
            "Question: {}\nFindings:\n{}\n\nWrite a short final report answering the "
            "question, based only on these findings."
        ).format(
            state["question"],
            "\n".join(f"- {item}" for item in state["findings"]),
        )
        response = llm.invoke(prompt)
        return {"final_answer": response.content}

    return generate_report
