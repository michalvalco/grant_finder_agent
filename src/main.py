# src/main.py
import os
import sys
# Force UTF-8 encoding for Windows
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')
import logging

# Pridanie koreňového adresára do PYTHONPATH pre správne importy
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.agent.graph import create_graph
from src.logger import setup_logger

def run_agent(query: str):
    """Spustí Grant Finder agenta pre zadaný dopyt."""
    
    # 1. Nastavenie loggera (musí byť prvé)
    try:
        # Inicializuje hlavný logger a nastaví konfiguráciu pre ostatné moduly (cez __name__)
        logger = setup_logger("Main")
    except Exception as e:
        print(f"❌ Kritická chyba: Nepodarilo sa nastaviť logger: {e}")
        return

    # 2. Validácia vstupu
    if not query or len(query.strip()) < 5:
        # Použijeme logger.error pre konzistentnosť, ale keďže logger vypisuje na konzolu, je to viditeľné
        logger.error("❌ Chyba vstupu: Zadajte prosím konkrétnejší dopyt (min. 5 znakov)")
        return
        
    logger.info(f"🔍 Spúšťam Grant Finder Agenta")
    logger.info(f"📝 Vaša požiadavka: '{query}'")
    
    # 3. Inicializácia agenta (Grafu a Nástrojov)
    try:
        # create_graph() interne volá initialize_tools(). 
        # Ak inicializácia zlyhá (ValueError z config.py), zachytíme ju tu.
        app = create_graph()
    except ValueError as e:
        # Zachytáva chyby konfigurácie (chýbajúce API kľúče)
        logger.error(f"\n❌ Chyba konfigurácie: {e}")
        # Vypíšeme pomocné inštrukcie. Keďže logger vypisuje správy bez prefixov, výstup je čistý.
        logger.info("\n💡 Riešenie:")
        logger.info("1. Uistite sa, že existuje súbor .env v koreňovom adresári projektu.")
        logger.info("2. Skopírujte .env.example ako .env, ak ste tak ešte neurobili.")
        logger.info("3. Doplňte platné API kľúče do .env:")
        logger.info("   - OPENAI_API_KEY (z https://platform.openai.com)")
        logger.info("   - TAVILY_API_KEY (z https://tavily.com)")
        return
    except Exception as e:
        logger.error(f"❌ Neočakávaná chyba pri inicializácii agenta: {e}", exc_info=True)
        return

    # 4. Spustenie agenta
    initial_state = {"user_query": query}
    final_state = None
    
    try:
        # Iterujeme cez výstupy
        for output in app.stream(initial_state):
            for key, value in output.items():
                if key != "__end__":
                   final_state = value
        
        logger.info("\n================ FINÁLNY REPORT ================\n")
        if final_state and "final_report" in final_state:
            report = final_state["final_report"]
            # Vypíšeme finálny report (cez logger, ktorý má čistý console output)
            logger.info(report)
            logger.info("\n✅ Úloha úspešne dokončená.")
        else:
            logger.warning("⚠️ Agent dokončil prácu, ale nevygeneroval finálny report.")

    except Exception as e:
        logger.error(f"\n❌ Nastala chyba počas behu agenta: {e}", exc_info=True)

if __name__ == "__main__":
    # Predvolený testovací dopyt
    default_query = "Granty pre výskum etiky umelej inteligencie a jej dopadu na náboženské komunity v Európe."

    # Umožníme zadať dopyt ako argument príkazového riadku
    if len(sys.argv) > 1:
        user_query = " ".join(sys.argv[1:])
        run_agent(user_query)
    else:
        run_agent(default_query)
