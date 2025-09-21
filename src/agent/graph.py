# src/agent/graph.py
from langgraph.graph import StateGraph, END
from src.agent.models import GrantFinderState
from src.agent.nodes import (
    node_query_optimizer,
    node_search_executor,
    node_grant_analyst,
    node_report_generator,
    initialize_tools # Importujeme inicializačnú funkciu
)

def create_graph():
    """Vytvorí a skompiluje LangGraph workflow."""
    
    # 1. Inicializácia nástrojov. Ak zlyhá (napr. kvôli API kľúčom), 
    # chyba (ValueError) sa propaguje a zachytí v main.py.
    initialize_tools()
    
    # 2. Inicializácia grafu so stavom
    workflow = StateGraph(GrantFinderState)

    # 3. Pridanie uzlov
    workflow.add_node("query_optimizer", node_query_optimizer)
    workflow.add_node("search_executor", node_search_executor)
    workflow.add_node("grant_analyst", node_grant_analyst)
    workflow.add_node("report_generator", node_report_generator)

    # 4. Definícia hrán (postupnosti)
    workflow.set_entry_point("query_optimizer")
    workflow.add_edge("query_optimizer", "search_executor")
    workflow.add_edge("search_executor", "grant_analyst")
    workflow.add_edge("grant_analyst", "report_generator")
    workflow.add_edge("report_generator", END)

    # 5. Kompilácia grafu
    app = workflow.compile()
    return app
