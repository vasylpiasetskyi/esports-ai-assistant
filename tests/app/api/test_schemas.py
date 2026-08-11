from app.api.schemas import AskRequest, AskResponse, HealthResponse, TaskStartedResponse


def test_ask_request_game_defaults_to_none():
    request = AskRequest(question="What is ADR?")
    assert request.game is None


def test_ask_request_accepts_game():
    request = AskRequest(question="What is Baron Nashor?", game="lol")
    assert request.game == "lol"


def test_ask_response_holds_answer_and_sources():
    response = AskResponse(
        answer="ADR is average damage per round.", sources=["https://example.test"]
    )
    assert response.answer == "ADR is average damage per round."
    assert response.sources == ["https://example.test"]


def test_health_response_status():
    response = HealthResponse(status="ok")
    assert response.status == "ok"


def test_task_started_response_status():
    response = TaskStartedResponse(status="started")
    assert response.status == "started"
