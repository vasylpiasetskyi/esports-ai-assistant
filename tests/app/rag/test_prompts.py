from app.rag.prompts import RAG_PROMPT


def test_rag_prompt_has_context_and_question_input_variables():
    assert set(RAG_PROMPT.input_variables) == {"context", "question"}
