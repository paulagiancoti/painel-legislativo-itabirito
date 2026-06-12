"""
Coleta inicial — roda UMA VEZ para baixar dados que raramente mudam:
vereadores, autores e composição da mesa diretora.

Depois disso, use apenas atualizar_dados.py periodicamente.
"""

import requests
import json
import os
import time

BASE_URL = "https://sapl.itabirito.mg.leg.br"

def coletar_todas_paginas(endpoint):
    todos = []
    pagina = 1
    total_paginas = None
    while True:
        tentativas = 0
        dados = None
        while tentativas < 3:
            try:
                resposta = requests.get(f"{BASE_URL}{endpoint}&page={pagina}", timeout=30)
                if resposta.status_code == 200 and resposta.text.strip():
                    dados = resposta.json()
                    break
            except Exception:
                pass
            tentativas += 1
            time.sleep(2)
        if dados is None:
            if pagina == 1:
                print("  Falha na primeira página, abortando.")
                break
            pagina += 1
            if total_paginas and pagina > total_paginas:
                break
            continue
        todos += dados['results']
        total_paginas = dados['pagination']['total_pages']
        print(f"  Página {pagina}/{total_paginas}...")
        if pagina >= total_paginas:
            break
        pagina += 1
        time.sleep(0.3)
    return todos

def salvar_json(nome_arquivo, dados):
    os.makedirs("dados", exist_ok=True)
    caminho = os.path.join("dados", nome_arquivo)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print(f"  ✓ Salvo: {caminho} ({len(dados)} registros)")

# ─── 1. PARLAMENTARES (vereadores) ─────────────────────────────────────────────

print("[1/3] Coletando parlamentares...")
todos_parlamentares = coletar_todas_paginas("/api/parlamentares/parlamentar/?format=json")

# Filtra apenas os ativos (sem data de fim de mandato)
vereadores_ativos = [
    p for p in todos_parlamentares
    if not p.get('mandato_externo') and p.get('ativo', True)
]
# Caso a API não tenha campo 'ativo', filtra pelos que estão em filiação atual
if not any('ativo' in p for p in todos_parlamentares):
    vereadores_ativos = todos_parlamentares  # ajuste manual pode ser necessário

salvar_json("vereadores.json", vereadores_ativos)
print(f"  → {len(vereadores_ativos)} vereadores salvos (revise manualmente se necessário)")

# ─── 2. AUTORES ─────────────────────────────────────────────────────────────────

print("\n[2/3] Coletando autores...")
autores = coletar_todas_paginas("/api/base/autor/?format=json")
salvar_json("autores.json", autores)

# ─── 3. MESA DIRETORA ────────────────────────────────────────────────────────────

print("\n[3/3] Coletando mesa diretora...")
# IMPORTANTE: ajuste o ID da composição da mesa atual conforme o ano/legislatura
MESA_DIRETORA_ID = 49  # "2026 Atual" — confirme em /api/parlamentares/composicaomesa/
try:
    url = f"{BASE_URL}/api/parlamentares/composicaomesa/?format=json&mesa_diretora={MESA_DIRETORA_ID}"
    resposta = requests.get(url, timeout=30)
    dados = resposta.json()
    mesa = dados.get('results', dados if isinstance(dados, list) else [])
    salvar_json("mesa_diretora.json", mesa)
except Exception as e:
    print(f"  Erro: {e}")
    print("  Verifique o ID correto em /api/parlamentares/cargomesa/?format=json")

print("\n✓ Coleta inicial concluída!")
print("  Revise dados/vereadores.json para garantir que só estão os 15 ativos.")
print("  Em seguida, rode atualizar_dados.py para baixar matérias, normas e assuntos.")
