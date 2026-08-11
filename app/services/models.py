from pydantic import BaseModel


class Player(BaseModel):
    name: str
    game: str
    team: str | None = None


class Team(BaseModel):
    name: str
    game: str
    players: list[str] = []


class Match(BaseModel):
    match_id: str
    game: str
    teams: list[str]
    score: str
    status: str
    date: str
    tournament: str
