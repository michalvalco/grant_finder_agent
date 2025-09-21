# src/agent/models.py
from typing import TypedDict, List, Dict, Any
# Používame pydantic_v1 pre kompatibilitu s LangChain ekosystémom
from langchain_core.pydantic_v1 import BaseModel, Field

# 1. Stav Grafu (Graph State)
class GrantFinderState(TypedDict):
    """Definuje zdieľaný stav pre LangGraph workflow."""
    user_query: str                 # Pôvodný vstup používateľa
    optimized_queries: List[str]    # Dopyty z Query Optimizer
    search_results: List[Dict[str, Any]] # Surové výsledky zo Search Executor
    structured_grants: List[Dict[str, Any]] # Štruktúrované dáta z Grant Analyst
    final_report: str               # Finálny report

# 2. Pydantic Modely pre Structured Output

class GrantInfo(BaseModel):
    """Informácie o relevantnej grantovej výzve."""
    title: str = Field(description="Názov grantovej výzvy.")
    url: str = Field(description="URL adresa výzvy.")
    relevance_explanation: str = Field(description="Vysvetlenie (1-2 vety), prečo je grant relevantný pre zadané humanitné odbory.")
    deadline: str = Field(description="Deadline na podanie žiadosti (ak je uvedený), inak 'Neznámy'.")
    funding_body: str = Field(description="Inštitúcia alebo program, ktorý grant poskytuje (napr. APVV, Horizon Europe).")
    region: str = Field(description="Geografický región (Slovakia, EU, alebo Global).")

class GrantAnalysis(BaseModel):
    """Zoznam analyzovaných a relevantných grantov."""
    grants: List[GrantInfo] = Field(description="Zoznam relevantných grantov.")

class OptimizedQueries(BaseModel):
    """Zoznam optimalizovaných vyhľadávacích dopytov."""
    queries: List[str] = Field(description="Zoznam 4-6 špecifických vyhľadávacích dopytov.")
