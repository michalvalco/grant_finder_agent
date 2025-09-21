# src/config.py
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults

# Načítanie environmentálnych premenných z .env súboru
# Hľadá .env v koreňovom adresári projektu
load_dotenv()

# Konštanty
LLM_MODEL = "gpt-4o"
LLM_TEMPERATURE = 0
TAVILY_MAX_RESULTS = 10

def get_llm() -> ChatOpenAI:
    """Vráti nakonfigurovanú inštanciu ChatOpenAI LLM."""
    if not os.getenv("OPENAI_API_KEY"):
        # Vyvoláme výnimku, ktorú zachytí main.py
        raise ValueError("Nemôžem inicializovať LLM: OPENAI_API_KEY chýba v .env súbore alebo nie je nastavený.")
    return ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)

def get_search_tool() -> TavilySearchResults:
    """Vráti nakonfigurovanú inštanciu Tavily Search nástroja."""
    if not os.getenv("TAVILY_API_KEY"):
        # Vyvoláme výnimku, ktorú zachytí main.py
        raise ValueError("Nemôžem inicializovať Tavily: TAVILY_API_KEY chýba v .env súbore alebo nie je nastavený.")
    return TavilySearchResults(max_results=TAVILY_MAX_RESULTS)
