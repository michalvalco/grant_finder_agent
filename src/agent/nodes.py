# src/agent/nodes.py
import datetime
import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Importy z nášho projektu
from src.agent.models import GrantFinderState, GrantAnalysis, OptimizedQueries
from src.config import get_llm, get_search_tool

# Získanie loggera pre tento modul. Konfigurácia (setup) prebehne v main.py.
logger = logging.getLogger(__name__)

# Globálne premenné pre nástroje (budú inicializované cez initialize_tools)
llm = None
search_tool = None

def initialize_tools():
    """Inicializuje globálne nástroje (LLM a Search). Volá sa z create_graph()."""
    global llm, search_tool
    # Skontrolujeme, či už boli inicializované
    if llm is None or search_tool is None:
        logger.info("Inicializujem nástroje (LLM, Tavily)...")
        try:
            llm = get_llm()
            search_tool = get_search_tool()
            logger.info("✅ Nástroje úspešne inicializované.")
        except ValueError as e:
            # Logujeme chybu a propagujeme ju ďalej (zachytí ju main.py)
            logger.error(f"❌ Chyba pri inicializácii nástrojov: {e}")
            raise

# --- Uzol 1: Query Optimizer ---
def node_query_optimizer(state: GrantFinderState) -> dict:
    logger.info("\n--- KROK 1: Optimalizácia dopytov ---")
    user_query = state["user_query"]
    
    # Získame aktuálny a budúci rok pre lepšie vyhľadávanie
    current_year = datetime.date.today().year
    next_year = current_year + 1

    system_prompt = f"""
    Si expert na vyhľadávanie akademických grantových príležitostí pre humanitné vedy (teológia, filozofia, etika, religionistika).
    Analyzuj požiadavku používateľa a vygeneruj 4 až 6 špecifických, optimalizovaných dopytov pre internetový vyhľadávač.
    
    Dôležité pravidlá:
    1. Pokry rôzne regióny: Slovensko (SK), EÚ, Globálne.
    2. Pre SK používaj slovenčinu a zahrň kľúčové inštitúcie (napr. APVV, VEGA, KEGA).
    3. Pre EÚ/Globálne používaj angličtinu a zahrň programy (napr. Horizon Europe, ERC grants).
    4. Zameraj sa na aktuálne alebo budúce výzvy (použi roky {current_year}/{next_year}).
    
    Odpovedz presne podľa definovanej Pydantic schémy (OptimizedQueries).
    """
    
    # Využijeme Structured Output
    structured_llm_optimizer = llm.with_structured_output(OptimizedQueries)
    
    result = structured_llm_optimizer.invoke(
        [
            ("system", system_prompt),
            ("human", f"Požiadavka používateľa: {user_query}")
        ]
    )
    
    queries = result.queries
    logger.info(f"Vygenerované dopyty: {queries}")
    return {"optimized_queries": queries}

# --- Uzol 2: Search Executor ---
def node_search_executor(state: GrantFinderState) -> dict:
    logger.info("\n--- KROK 2: Vyhľadávanie ---")
    queries = state["optimized_queries"]
    all_results = []
    
    for query in queries:
        if not isinstance(query, str) or not query.strip(): continue
        
        logger.info(f"Vyhľadávam: '{query}'...")
        try:
            results = search_tool.invoke({"query": query})
            for res in results:
                all_results.append({
                    "title": res.get("title"),
                    "url": res.get("url"),
                    "content": res.get("content", "")
                })
        except Exception as e:
            # Logujeme chybu aj so stack trace (exc_info=True) a pokračujeme ďalej
            logger.error(f"Chyba pri vyhľadávaní dopytu '{query}': {e}", exc_info=True)
            continue

    logger.info(f"Celkový počet nájdených surových výsledkov: {len(all_results)}")
    return {"search_results": all_results}

# --- Uzol 3: Grant Analyst ---
def node_grant_analyst(state: GrantFinderState) -> dict:
    logger.info("\n--- KROK 3: Analýza a extrakcia (Structured Output) ---")
    results = state["search_results"]
    user_query = state["user_query"]

    if not results:
        logger.info("Žiadne výsledky na analýzu.")
        return {"structured_grants": []}

    # Nakonfigurujeme LLM pre Structured Output
    structured_llm_analyst = llm.with_structured_output(GrantAnalysis)

    # Pripravíme výsledky pre LLM (optimalizácia pre kontextové okno)
    results_str = ""
    MAX_CONTENT_LEN = 600
    MAX_RESULTS_TO_ANALYZE = 15

    for i, res in enumerate(results[:MAX_RESULTS_TO_ANALYZE]):
        content = res.get('content', '')
        if content:
            content = content[:MAX_CONTENT_LEN] + "..." if len(content) > MAX_CONTENT_LEN else content
        
        results_str += f"[{i+1}] Title: {res.get('title')}\nURL: {res.get('url')}\nContent Snippet: {content}\n\n---\n\n"

    system_prompt = """
    Si výskumný analytik špecializujúci sa na humanitné vedy (teológia, filozofia, etika, religionistika). 
    Tvojou úlohou je analyzovať poskytnuté výsledky vyhľadávania a extrahovať relevantné grantové príležitosti podľa definovanej schémy (GrantInfo).

    Pravidlá filtrovania:
    1. **Prísna relevancia:** Zahrň iba výzvy priamo relevantné pre zadané odbory alebo pôvodnú požiadavku používateľa.
    2. **Ignoruj irelevantný obsah:** Vylúč novinové články, blogy, všeobecné stránky univerzít alebo archívne/neaktuálne/uzavreté výzvy.
    3. **Interdisciplinarita:** Akceptuj výzvy z iných oblastí (napr. AI), len ak majú jasne definovaný presah do humanitných vied (napr. Etika AI).
    4. **Presnosť extrakcie:** Extrahuj informácie čo najpresnejšie. Ak deadline nie je explicitne uvedený v snippete, použi 'Neznámy'.
    """
    
    # Spustenie analýzy
    try:
        analysis_result = structured_llm_analyst.invoke(
            [
                ("system", system_prompt),
                ("human", f"Pôvodná požiadavka: {user_query}\n\nAnalyzuj tieto výsledky vyhľadávania a extrahuj relevantné granty:\n\n{results_str}")
            ]
        )
    except Exception as e:
        logger.error(f"Chyba pri analýze LLM alebo parsovaní výstupu: {e}", exc_info=True)
        return {"structured_grants": []} # Vrátime prázdny zoznam v prípade chyby

    # Konverzia Pydantic objektov na slovníky (používame .dict() pre Pydantic V1 kompatibilitu)
    structured_grants_list = [grant.dict() for grant in analysis_result.grants]
    logger.info(f"Počet extrahovaných relevantných grantov: {len(structured_grants_list)}")
    return {"structured_grants": structured_grants_list}

# --- Uzol 4: Report Generator ---
def node_report_generator(state: GrantFinderState) -> dict:
    logger.info("\n--- KROK 4: Generovanie reportu ---")
    grants = state["structured_grants"]
    user_query = state["user_query"]

    if not grants:
        report = "Bohužiaľ, na základe aktuálnych informácií sa mi nepodarilo nájsť žiadne relevantné otvorené grantové výzvy pre vašu požiadavku. Odporúčam skúsiť širšie alebo inak formulované zadanie."
        return {"final_report": report}

    system_prompt = """
    Si profesionálny AI asistent pre akademických pracovníkov. Tvojou úlohou je vytvoriť prehľadný, detailný a profesionálne pôsobiaci report o nájdených grantových príležitostiach.
    Píš výhradne v Slovenčine. Použi Markdown formátovanie pre štruktúru a čitateľnosť.
    """
    
    human_prompt = """
    Vytvor finálny report na základe nasledujúcich štruktúrovaných dát o grantoch.

    Pôvodná požiadavka používateľa: "{user_query}"
    Dáta o grantoch (JSON):
    {grants_json}

    Požadovaná štruktúra reportu:
    # Prehľad grantových príležitostí pre: "{user_query}"

    Našiel som {count} relevantných otvorených výziev. Tu je ich podrobný prehľad:

    ---

    ## [Názov grantu]
    *   **Región:** [Region]
    *   **Poskytovateľ:** [Funding Body]
    *   **Deadline:** 🗓️ [Deadline]
    *   **Zameranie a relevancia:** [Relevance Explanation]
    *   **Odkaz:** [URL]

    ---
    (Pokračuj týmto formátom pre všetky nájdené granty)

    *Poznámka: Odporúčam vždy skontrolovať detaily a podmienky priamo na oficiálnej stránke výzvy.*
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt)
    ])

    report_chain = prompt | llm | StrOutputParser()
    report = report_chain.invoke({
        "user_query": user_query, 
        "grants_json": grants,
        "count": len(grants)
    })
    
    return {"final_report": report}
