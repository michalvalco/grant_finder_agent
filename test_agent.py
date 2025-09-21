# test_agent.py
import sys
import os
import datetime
from dotenv import load_dotenv

# Nastavenie cesty pre importy
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Načítanie .env pre testy (z koreňa projektu)
load_dotenv()

try:
    # Použijeme pydantic_v1 pre kompatibilitu s tým, čo používa LangChain interne
    from langchain_core.pydantic_v1 import ValidationError
    from src.agent.models import GrantInfo, GrantAnalysis
    from src.config import get_llm, get_search_tool
except ImportError as e:
    print(f"❌ Chyba pri importe modulov: {e}")
    print("Uistite sa, že ste nainštalovali závislosti z requirements.txt (pip install -r requirements.txt)")
    sys.exit(1)

def test_models():
    """Test Pydantic modelov."""
    try:
        grant = GrantInfo(
            title="Test Grant",
            url="https://example.com",
            relevance_explanation="Test relevancia",
            deadline="2025-03-15",
            funding_body="Test Body",
            region="EU"
        )
        assert grant.title == "Test Grant"
        analysis = GrantAnalysis(grants=[grant])
        assert len(analysis.grants) == 1
        print("✅ Pydantic modely fungujú správne.")
    except Exception as e:
        print(f"❌ Test Pydantic modelov zlyhal: {e}")

def test_llm_connection():
    """Test pripojenia k LLM (OpenAI)."""
    try:
        llm = get_llm()
        print("Testujem OpenAI API spojenie...")
        response = llm.invoke("Test: Odpovedz jedným slovom 'funguje'")
        if "funguje" in response.content.lower():
             print("✅ LLM pripojenie (OpenAI) funguje.")
        else:
            print(f"❌ LLM odpovedalo neočakávane: {response.content}")
    except ValueError as e:
        # Zachytí chýbajúci kľúč z config.py
        print(f"❌ Inicializácia LLM zlyhala (skontroluj OPENAI_API_KEY v .env): {e}")
    except Exception as e:
        # Zachytí napr. sieťové chyby alebo neplatný kľúč
        print(f"❌ Test LLM pripojenia zlyhal: {e}")

def test_search_tool():
    """Test Tavily search."""
    try:
        tool = get_search_tool()
        print("Testujem Tavily API spojenie...")
        results = tool.invoke({"query": "test grant opportunities"})
        if isinstance(results, list):
            print(f"✅ Tavily search funguje (vrátil {len(results)} výsledkov).")
        else:
            print("❌ Tavily search vrátilo neočakávaný typ výsledku.")
    except ValueError as e:
        # Zachytí chýbajúci kľúč z config.py
        print(f"❌ Inicializácia Tavily zlyhala (skontroluj TAVILY_API_KEY v .env): {e}")
    except Exception as e:
        print(f"❌ Test Tavily search zlyhal: {e}")

def test_date():
    """Overenie, či je dátum aktuálny."""
    today = datetime.date.today()
    # Predpokladáme, že rok 2025 je relevantný pre aktuálne granty
    if today.year >= 2025:
        print(f"✅ Dátum je aktuálny (Rok: {today.year})")
    else:
        print(f"⚠️ Dátum je starý (Rok: {today.year}). Agent nemusí nájsť aktuálne granty.")

if __name__ == "__main__":
    print("Spúšťam integračné testy pre Grant Finder Agenta...\n")
    test_models()
    print("-" * 20)
    test_llm_connection()
    print("-" * 20)
    test_search_tool()
    print("-" * 20)
    test_date()
    print("\nTesty dokončené!")
