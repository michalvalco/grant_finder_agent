# Použijeme oficiálny Python obraz (slim verzia pre menšiu veľkosť)
FROM python:3.12-slim

# Nastavíme pracovný adresár v kontajneri
WORKDIR /app

# Optimalizácia pre Python v kontajneri
# Zabraňuje vytváraniu .pyc súborov a zabezpečuje, že výstup (logy) je viditeľný okamžite
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Skopírujeme súbor s požiadavkami a nainštalujeme závislosti
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Skopírujeme zvyšok kódu aplikácie
COPY . .

# Vytvoríme adresár pre logy a nastavíme práva (pre prípad, že by kontajner nebežal ako root)
RUN mkdir -p logs && chmod 777 logs

# Príkaz na spustenie aplikácie. 
# Poznámka: API kľúče musia byť odovzdané pri spustení kontajnera (napr. cez --env-file).
CMD ["python", "src/main.py"]
