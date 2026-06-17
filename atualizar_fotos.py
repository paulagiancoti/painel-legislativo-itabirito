"""
atualizar_fotos.py
Baixa as fotos dos vereadores do SAPL e salva localmente em static/fotos/.
Rode este script manualmente sempre que uma foto for atualizada no SAPL.
"""

import json
import os
import time
import requests

BASE_URL  = "https://sapl.itabirito.mg.leg.br"
PASTA     = "static/fotos"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}

os.makedirs(PASTA, exist_ok=True)

# Carrega vereadores
with open("dados/vereadores.json", encoding="utf-8") as f:
    vereadores = json.load(f)

print(f"Baixando fotos de {len(vereadores)} vereadores...\n")

atualizados = 0
sem_foto    = 0

for v in vereadores:
    vid       = v.get("id")
    nome      = v.get("nome_parlamentar") or v.get("nome_completo", f"ID {vid}")
    foto_url  = v.get("fotografia") or v.get("foto") or ""

    if not foto_url:
        print(f"  ⚠ Sem foto: {nome}")
        sem_foto += 1
        continue

    # Garante URL absoluta
    if foto_url.startswith("/"):
        foto_url = BASE_URL + foto_url

    destino = os.path.join(PASTA, f"{vid}.jpg")

    try:
        resp = requests.get(foto_url, headers=HEADERS, timeout=30)
        if resp.status_code == 200 and resp.content:
            with open(destino, "wb") as f:
                f.write(resp.content)
            print(f"  ✓ {nome} → {destino}")
            atualizados += 1
        else:
            print(f"  ✗ {nome}: HTTP {resp.status_code}")
    except Exception as e:
        print(f"  ✗ {nome}: {e}")

    time.sleep(0.3)

print(f"\nConcluído: {atualizados} fotos baixadas, {sem_foto} sem foto cadastrada.")
