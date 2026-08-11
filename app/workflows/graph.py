from langgraph.graph import END, StateGraph

from app.rag.service import RAGService
from app.services.match_service import MatchService
from app.workflows.nodes import (
    make_analyze_evidence_node,
    make_analyze_question_node,
    make_generate_report_node,
    make_get_match_data_node,
    make_get_match_node,
    make_retrieve_knowledge_node,
    route_after_analysis,
)
from app.workflows.state import InvestigationState


def build_investigation_graph(llm, match_service: MatchService, rag_service: RAGService):
    graph = StateGraph(InvestigationState)
    graph.add_node("analyze_question", make_analyze_question_node(llm))
    graph.add_node("get_match", make_get_match_node(match_service))
    graph.add_node("get_match_data", make_get_match_data_node(match_service))
    graph.add_node("retrieve_knowledge", make_retrieve_knowledge_node(rag_service))
    graph.add_node("analyze_evidence", make_analyze_evidence_node(llm))
    graph.add_node("generate_report", make_generate_report_node(llm))

    graph.set_entry_point("analyze_question")
    graph.add_edge("analyze_question", "get_match")
    graph.add_edge("get_match", "get_match_data")
    graph.add_edge("get_match_data", "retrieve_knowledge")
    graph.add_edge("retrieve_knowledge", "analyze_evidence")
    graph.add_conditional_edges(
        "analyze_evidence",
        route_after_analysis,
        {"generate_report": "generate_report", "retrieve_knowledge": "retrieve_knowledge"},
    )
    graph.add_edge("generate_report", END)

    return graph.compile()
