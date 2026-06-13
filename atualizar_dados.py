import requests
import json
import os
import time

BASE_URL = "https://sapl.itabirito.mg.leg.br"
ANOS     = [2025, 2026]

# Cabeçalhos que imitam um navegador — evita bloqueio por servidores SAPL
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": BASE_URL,
}

def get_json(url, tentativas=3, espera=3):
    """Faz GET com retry e valida que a resposta é JSON."""
    for i in range(tentativas):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=60)
            if resp.status_code == 200:
                dados = resp.json()
                return dados
            else:
                print(f"    HTTP {resp.status_code} — tentativa {i+1}/{tentativas}")
        except requests.exceptions.Timeout:
            print(f"    Timeout — tentativa {i+1}/{tentativas}")
        except Exception as e:
            print(f"    Erro: {e} — tentativa {i+1}/{tentativas}")
        if i < tentativas - 1:
            time.sleep(espera)
    return None

def coletar_paginado(endpoint):
    """Coleta endpoint paginado /api/.../?format=json"""
    todos = []
    pagina = 1
    total_paginas = None
    while True:
        sep = "&" if "?" in endpoint else "?"
        dados = get_json(f"{BASE_URL}{endpoint}{sep}page={pagina}")
        if dados is None:
            print(f"  Falhou na página {pagina} — abortando.")
            break
        if isinstance(dados, list):
            # resposta sem paginação
            todos += dados
            break
        resultados = dados.get("results", [])
        todos += resultados
        total_paginas = dados.get("pagination", {}).get("total_pages", 1)
        print(f"  Página {pagina}/{total_paginas} ({len(resultados)} registros)")
        if pagina >= total_paginas:
            break
        pagina += 1
        time.sleep(0.3)
    return todos

def salvar_json(nome_arquivo, dados, nao_salvar_se_vazio=True):
    """Salva JSON. Se vazio e nao_salvar_se_vazio=True, mantém arquivo anterior."""
    os.makedirs("dados", exist_ok=True)
    caminho = os.path.join("dados", nome_arquivo)
    if nao_salvar_se_vazio and not dados:
        print(f"  ⚠️  Resultado vazio — arquivo {caminho} NÃO foi sobrescrito")
        return False
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print(f"  ✓ Salvo: {caminho} ({len(dados)} registros)")
    return True

# ─── 1. MATÉRIAS (endpoint REST paginado — mais confiável que pesquisar-materia) ─

print("\n[1/4] Coletando matérias 2025 e 2026 via API REST...")
materias_historico = []
for ano in ANOS:
    print(f"  Ano {ano}:")
    # Tenta endpoint REST paginado
    endpoint = f"/api/materia/materialegislativa/?format=json&ano={ano}"
    registros = coletar_paginado(endpoint)

    # Fallback: endpoint de pesquisa (precisa de ?format=json)
    if not registros:
        print(f"  ↩ Tentando endpoint de pesquisa para {ano}...")
        url_pesquisa = (
            f"{BASE_URL}/materia/pesquisar-materia"
            f"?format=json&ano={ano}&tipo_listagem=1&salvar=Pesquisar"
        )
        dados = get_json(url_pesquisa)
        if dados and isinstance(dados, dict):
            registros = dados.get("results", [])

    print(f"  → {len(registros)} matérias coletadas")
    materias_historico += registros

if salvar_json("materias_historico.json", materias_historico):
    materias_2026 = [m for m in materias_historico if str(m.get("ano")) == "2026"]
    salvar_json("materias.json", materias_2026)
else:
    print("  ⚠️  Matérias não coletadas — dados anteriores preservados")

# ─── 2. NORMAS ───────────────────────────────────────────────────────────────────

print("\n[2/4] Coletando normas 2026...")
normas = coletar_paginado("/api/norma/normajuridica/?format=json&ano=2026")
salvar_json("normas.json", normas)

# ─── 3. ASSUNTOS ─────────────────────────────────────────────────────────────────

print("\n[3/4] Coletando assuntos...")
assuntos = coletar_paginado("/api/materia/assuntomateria/?format=json")
salvar_json("assuntos.json", assuntos)

# ─── 4. VÍNCULOS MATÉRIA↔ASSUNTO ─────────────────────────────────────────────────

print("\n[4/4] Coletando vínculos matéria↔assunto...")
materiaassuntos = coletar_paginado("/api/materia/materiaassunto/?format=json")
salvar_json("materiaassuntos.json", materiaassuntos)

# ─── RESUMO ───────────────────────────────────────────────────────────────────────

print("\n✓ Atualização concluída!")
for arq in ["materias.json", "materias_historico.json", "normas.json", "assuntos.json", "materiaassuntos.json"]:
    caminho = os.path.join("dados", arq)
    if os.path.exists(caminho):
        dados = json.load(open(caminho, encoding="utf-8"))
        print(f"  {arq}: {len(dados)} registros")
    else:
        print(f"  {arq}: arquivo não encontrado")

# Verifica estrutura das matérias (para debug de campos)
if os.path.exists("dados/materias.json"):
    mats = json.load(open("dados/materias.json", encoding="utf-8"))
    if mats:
        print(f"\nCampos da primeira matéria: {list(mats[0].keys())}")
        print(f"Autoria: {mats[0].get('autoria', 'CAMPO NÃO ENCONTRADO')}")
    else:
        print("\n⚠️  materias.json está vazio!")
