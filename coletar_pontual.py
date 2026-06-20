"""
coletar_pontual.py
Coleta dados pontuais sem rodar o processo completo.
Atualmente: sessões plenárias e oradores (pronunciamentos).
"""

import requests
import json
import os
import sys
import time

# Garante saída imediata nos logs do GitHub Actions
sys.stdout.reconfigure(line_buffering=True)

BASE_URL = "https://sapl.itabirito.mg.leg.br"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, */*; q=0.01",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "X-Requested-With": "XMLHttpRequest",
}

def get_json(url, tentativas=2, espera=3):
    for i in range(tentativas):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=(15, 60))
            print(f"    [{resp.status_code}] {url}")
            if resp.status_code == 200 and resp.text.strip():
                return resp.json()
        except Exception as e:
            print(f"    Erro: {e}")
        if i < tentativas - 1:
            time.sleep(espera)
    return None

def coletar_paginado(endpoint):
    todos = []
    pagina = 1
    while True:
        sep = "&" if "?" in endpoint else "?"
        dados = get_json(f"{BASE_URL}{endpoint}{sep}page={pagina}")
        if dados is None:
            print(f"  Falhou na página {pagina} — abortando.")
            break
        if isinstance(dados, list):
            todos += dados
            break
        resultados = dados.get("results", [])
        todos += resultados
        total = dados.get("pagination", {}).get("total_pages", 1)
        print(f"  Página {pagina}/{total} ({len(resultados)} registros)")
        if pagina >= total:
            break
        pagina += 1
        time.sleep(0.3)
    return todos

def carregar_existente(nome):
    caminho = os.path.join("dados", nome)
    if os.path.exists(caminho):
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    return []

def merge_por_id(existentes, novos):
    mapa = {str(r["id"]): r for r in existentes}
    for r in novos:
        mapa[str(r["id"])] = r
    return list(mapa.values())

def salvar_json(nome, dados):
    os.makedirs("dados", exist_ok=True)
    caminho = os.path.join("dados", nome)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print(f"  ✓ {caminho} salvo ({len(dados)} registros)")

# ─── ORADORES ─────────────────────────────────────────────────────────────────

print("\n[1] Coletando oradores (pronunciamentos)...")
existentes_or = carregar_existente("oradores.json")
max_id_or = max((r["id"] for r in existentes_or), default=0)
print(f"  Oradores existentes: {len(existentes_or)}, maior ID={max_id_or}")
ep_or = (
    f"/api/sessao/oradorordemdia/?format=json&id__gt={max_id_or}"
    if max_id_or > 0 else "/api/sessao/oradorordemdia/?format=json"
)
print(f"  Endpoint: {ep_or}")
novos_or = coletar_paginado(ep_or)
print(f"  Retornou: {len(novos_or)} registro(s)")
if novos_or:
    merged_or = merge_por_id(existentes_or, novos_or)
    salvar_json("oradores.json", merged_or)
elif max_id_or > 0:
    print("  Nenhum orador novo — dados anteriores mantidos")
else:
    print("  ✗ Nenhum orador coletado e não havia arquivo anterior")

# ─── SESSÕES PLENÁRIAS ────────────────────────────────────────────────────────

print("\n[2] Coletando sessões plenárias...")
existentes_sess = carregar_existente("sessoes.json")
max_id_sess = max((r["id"] for r in existentes_sess), default=0)
print(f"  Sessões existentes: {len(existentes_sess)}, maior ID={max_id_sess}")
ep_sess = (
    f"/api/sessao/sessaoplenaria/?format=json&id__gt={max_id_sess}"
    if max_id_sess > 0 else "/api/sessao/sessaoplenaria/?format=json"
)
print(f"  Endpoint: {ep_sess}")
novas_sess = coletar_paginado(ep_sess)
print(f"  Retornou: {len(novas_sess)} registro(s)")
if novas_sess:
    merged_sess = merge_por_id(existentes_sess, novas_sess)
    salvar_json("sessoes.json", merged_sess)
elif max_id_sess > 0:
    print("  Nenhuma sessão nova — dados anteriores mantidos")
else:
    print("  ✗ Nenhuma sessão coletada e não havia arquivo anterior")

# ─── RESUMO ───────────────────────────────────────────────────────────────────

print("\n─── Resultado ───")
for arq in ["oradores.json", "sessoes.json"]:
    caminho = os.path.join("dados", arq)
    if os.path.exists(caminho):
        d = json.load(open(caminho, encoding="utf-8"))
        print(f"  {arq}: {len(d)} registros")
    else:
        print(f"  {arq}: não encontrado")
