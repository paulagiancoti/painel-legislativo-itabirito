import requests
import json
import os
import time

BASE_URL = "https://sapl.itabirito.mg.leg.br"
ANOS     = [2025, 2026]

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
                print(f"  Falha na primeira página, abortando.")
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

# ─── 1. MATÉRIAS (2025 + 2026) ─────────────────────────────────────────────────

print("\n[1/4] Atualizando matérias...")
materias_historico = []
for ano in ANOS:
    print(f"  Ano {ano}:")
    try:
        url = (
            f"{BASE_URL}/materia/pesquisar-materia"
            f"?format=json&ano={ano}&tipo_listagem=1&salvar=Pesquisar"
        )
        resposta = requests.get(url, timeout=120)
        dados = resposta.json()
        materias_historico += dados['results']
        print(f"  {len(dados['results'])} matérias encontradas")
    except Exception as e:
        print(f"  Erro: {e}")

salvar_json("materias_historico.json", materias_historico)
materias_2026 = [m for m in materias_historico if str(m.get('ano')) == '2026']
salvar_json("materias.json", materias_2026)

# ─── 2. NORMAS 2026 ────────────────────────────────────────────────────────────

print("\n[2/4] Atualizando normas 2026...")
normas = coletar_todas_paginas("/api/norma/normajuridica/?format=json&ano=2026")
salvar_json("normas.json", normas)

# ─── 3. ASSUNTOS ───────────────────────────────────────────────────────────────

print("\n[3/4] Atualizando assuntos...")
assuntos = coletar_todas_paginas("/api/materia/assuntomateria/?format=json")
salvar_json("assuntos.json", assuntos)

# ─── 4. VÍNCULOS MATÉRIA↔ASSUNTO ──────────────────────────────────────────────

print("\n[4/4] Atualizando vínculos matéria↔assunto...")
materiaassuntos = coletar_todas_paginas("/api/materia/materiaassunto/?format=json")
salvar_json("materiaassuntos.json", materiaassuntos)

# ─── RESUMO ────────────────────────────────────────────────────────────────────

print("\n✓ Atualização concluída!")
print(f"  Matérias (painel):    {len(materias_2026)}")
print(f"  Matérias (histórico): {len(materias_historico)}")
print(f"  Normas:               {len(normas)}")
print(f"  Assuntos:             {len(assuntos)}")
print(f"  Vínculos de assunto:  {len(materiaassuntos)}")
