"""
coletar_pontual.py
Coleta arquivos específicos sem rodar o processo completo.
Use este script para baixar comissões, tipos de matéria e relatorias
sem precisar esperar a coleta de matérias, normas e assuntos.
"""

import requests
import json
import os
import time

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
    print(f"  ✓ {caminho} ({len(dados)} registros)")

# ─── COMISSÕES ────────────────────────────────────────────────────────────────
# PERSONALIZAÇÃO: tente os endpoints abaixo em ordem até um funcionar

print("\n[1] Tentando coletar comissões...")
# PERSONALIZAÇÃO: endpoint confirmado para Itabirito é /api/comissoes/comissao/
# Para outras instalações, tente as variações abaixo em ordem.
ENDPOINTS_COMISSAO = [
    "/api/comissoes/comissao/?format=json",   # ← correto para Itabirito
    "/api/comissao/comissao/?format=json",
    "/api/comissao/?format=json",
]

comissoes = []
for ep in ENDPOINTS_COMISSAO:
    print(f"  Tentando: {ep}")
    dados = get_json(f"{BASE_URL}{ep}")
    if dados:
        if isinstance(dados, list):
            comissoes = dados
        elif isinstance(dados, dict):
            comissoes = dados.get("results", [])
            if comissoes:
                # É paginado — coleta todas as páginas
                comissoes = coletar_paginado(ep)
        if comissoes:
            print(f"  ✓ Endpoint encontrado: {ep}")
            break

if comissoes:
    salvar_json("comissoes.json", comissoes)
else:
    print("  ✗ Nenhum endpoint funcionou para comissões.")
    print("    Consulte os endpoints disponíveis em:")
    print(f"    {BASE_URL}/api/schema/swagger-ui/")

# ─── TIPOS DE MATÉRIA ─────────────────────────────────────────────────────────

print("\n[2] Tentando coletar tipos de matéria...")
# PERSONALIZAÇÃO: endpoint de tipo de matéria — tente as variações abaixo.
ENDPOINTS_TIPOMATERIA = [
    "/api/materia/tipomateria/?format=json",
    "/api/materia/tipo/?format=json",
]

tipomaterias = []
for ep in ENDPOINTS_TIPOMATERIA:
    print(f"  Tentando: {ep}")
    dados = get_json(f"{BASE_URL}{ep}")
    if dados:
        if isinstance(dados, list):
            tipomaterias = dados
        elif isinstance(dados, dict):
            tipomaterias = dados.get("results", [])
            if tipomaterias:
                tipomaterias = coletar_paginado(ep)
        if tipomaterias:
            print(f"  ✓ Endpoint encontrado: {ep}")
            break

if tipomaterias:
    salvar_json("tipomaterias.json", tipomaterias)
else:
    print("  ✗ Nenhum endpoint funcionou para tipos de matéria.")

# ─── RELATORIAS (se ainda não baixadas) ──────────────────────────────────────

existentes = carregar_existente("relatorias.json")
if not existentes:
    print("\n[3] Coletando relatorias (primeira vez)...")
    novas = coletar_paginado("/api/materia/relatoria/?format=json")
    if novas:
        salvar_json("relatorias.json", novas)
else:
    print(f"\n[3] Relatorias: {len(existentes)} já existentes — pulando.")

# ─── RESUMO ───────────────────────────────────────────────────────────────────

print("\n─── Resultado ───")
for arq in ["comissoes.json", "tipomaterias.json", "relatorias.json"]:
    caminho = os.path.join("dados", arq)
    if os.path.exists(caminho):
        d = json.load(open(caminho, encoding="utf-8"))
        print(f"  {arq}: {len(d)} registros")
    else:
        print(f"  {arq}: não encontrado")
