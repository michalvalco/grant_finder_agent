# src/logger.py
import logging
import os
from datetime import datetime

def setup_logger(name="GrantFinderAgent"):
    """Nastaví logger pre debug a audit trail."""
    
    # Vytvorenie adresára logs v koreni projektu
    # Zistíme absolútnu cestu k tomuto súboru, a ideme o dve úrovne vyššie (src/ -> root)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(project_root, 'logs')

    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except OSError as e:
            print(f"Warning: Nemôžem vytvoriť adresár pre logy {log_dir}: {e}")
            log_dir = None # Nebudeme logovať do súboru

    logger = logging.getLogger(name)
    
    # Ak už má handlery, neinicializujeme znova (prevencia duplicitných logov)
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.INFO)

    # Formát pre súbor (detailný)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # Formát pre konzolu (jednoduchší, bez prefixov, aby bol výstup čistý)
    console_formatter = logging.Formatter('%(message)s')

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File Handler
    if log_dir:
        log_filename = os.path.join(log_dir, f"agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        try:
            file_handler = logging.FileHandler(log_filename)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except IOError as e:
            logger.warning(f"Nemôžem zapisovať do log súboru {log_filename}: {e}. Pokračujem len s výstupom na konzolu.")

    # Zamedzíme propagácii správ k root loggeru
    logger.propagate = False
    
    # Vypneme "ukecané" logy z knižníc tretích strán
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    return logger
