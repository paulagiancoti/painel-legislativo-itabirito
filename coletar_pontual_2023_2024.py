"""
coletar_pontual_2023_2024.py

Coleta PONTUAL (rodar 1x manualmente) para completar a verificação de relatorias.
NÃO mexe em nada do painel: não toca em dados/, não faz merge com materias_historico.json
nem com normas.json, não altera app.py. Salva tudo numa pasta separada.

O que baixa:
  1. Matérias de 2023 e 2024 (mesmo endpoint que o atualizar_dados.py usa para 2025/2026)
     -> dados_pontual/materias_2023_2024.json
  2. Normas (leis) de 2023, 2024 e 2025 (hoje só temos normas de 2026)
     -> dados_pontual/normas_2023_2024_2025.json

Como rodar (Codespaces ou local, com internet liberada para o SAPL):
  python coletar_pontual_2023_2024.py

Depois: me manda os 2 arquivos gerados em dados_pontual/ (upload aqui no chat)
que eu completo a verificação das relatorias desses anos.
"""

import requests
import json
import os
import sys
import time

sys.stdout.reconfigure(line_buffering=True)

# ╔══════════════════════════════════════════════════════════════════╗
# ║  CONFIGURAÇÃO                                                    ║
# ╚══════════════════════════════════════════════════════════════════╝

BASE_URL = "https://sapl.itabirito.mg.leg.br"
ANOS_MATERIAS = [2023, 2024]
ANOS_NORMAS = [2023, 2024, 2025]
PASTA_SAIDA = "dados_pontual"

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

# ─── HELPERS (mesmo padrão do atualizar_dados.py) ─────────────────────────────

def get_json(url, tentativas=3, espera=8):
    for i in range(tentativas):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=(15, 60))
            if resp.status_code == 200 and resp.text.strip():
                return resp.json()
            print(f"    HTTP {resp.status_code} — tentativa {i + 1}/{tentativas}")
        except requests.exceptions.Timeout:
            print(f"    Timeout — tentativa {i + 1}/{tentativas}")
        except Exception as e:
            print(f"    Erro: {e} — tentativa {i + 1}/{tentativas}")
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
        time.sleep(0.5)
    return todos


def salvar_json(nome_arquivo, dados):
    os.makedirs(PASTA_SAIDA, exist_ok=True)
    caminho = os.path.join(PASTA_SAIDA, nome_arquivo)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print(f"  ✓ Salvo: {caminho} ({len(dados)} registros)")


erros = []

# ─── 1. MATÉRIAS 2023-2024 ─────────────────────────────────────────────────

print(f"\n[1/2] Coletando matérias de {ANOS_MATERIAS} (pesquisar-materia)...")

todas_materias = []
for ano in ANOS_MATERIAS:
    print(f"  Ano {ano}:")
    url = (
        f"{BASE_URL}/materia/pesquisar-materia"
        f"?format=json&ano={ano}&tipo_listagem=1&salvar=Pesquisar"
    )
    dados = get_json(url)
    if dados and isinstance(dados, dict) and dados.get("results"):
        registros = dados["results"]
        todas_materias += registros
        print(f"  → {len(registros)} matérias coletadas")
    else:
        erros.append(f"Falha ao coletar matérias de {ano} — endpoint sem resposta")
        print(f"  ✗ Falha ao coletar matérias de {ano}")

if todas_materias:
    # remove eventuais duplicados por id, mantendo a última ocorrência
    mapa = {str(r["id"]): r for r in todas_materias}
    todas_materias = list(mapa.values())
    salvar_json("materias_2023_2024.json", todas_materias)
    for ano in ANOS_MATERIAS:
        qtd = sum(1 for m in todas_materias if str(m.get("ano")) == str(ano))
        print(f"    {ano}: {qtd} matérias")
else:
    erros.append("Nenhuma matéria coletada em nenhum dos anos.")

# ─── 2. NORMAS (LEIS) 2023-2025 ────────────────────────────────────────────

print(f"\n[2/2] Coletando normas de {ANOS_NORMAS}...")

todas_normas = []
for ano in ANOS_NORMAS:
    print(f"  Ano {ano}:")
    ep_normas = f"/api/norma/normajuridica/?format=json&ano={ano}"
    normas_ano = coletar_paginado(ep_normas)
    if normas_ano:
        todas_normas += normas_ano
        print(f"  → {len(normas_ano)} normas coletadas")
    else:
        erros.append(f"Falha ao coletar normas de {ano} — endpoint sem resposta")
        print(f"  ✗ Falha ao coletar normas de {ano}")

if todas_normas:
    mapa = {str(n["id"]): n for n in todas_normas}
    todas_normas = list(mapa.values())
    salvar_json("normas_2023_2024_2025.json", todas_normas)
    for ano in ANOS_NORMAS:
        qtd = sum(1 for n in todas_normas if str(n.get("ano")) == str(ano))
        print(f"    {ano}: {qtd} normas")
else:
    erros.append("Nenhuma norma coletada em nenhum dos anos.")

# ─── RESULTADO FINAL ────────────────────────────────────────────────────────

print("\n" + "=" * 60)
if erros:
    print("⚠️  Concluído com avisos:")
    for e in erros:
        print(f"  • {e}")
    print(f"\nArquivos gerados (o que deu certo) estão em {PASTA_SAIDA}/")
    print("Me manda esses arquivos que eu já uso o que foi coletado.")
else:
    print("✓ Coleta concluída sem erros.")
    print(f"Arquivos gerados em {PASTA_SAIDA}/:")
    print("  - materias_2023_2024.json")
    print("  - normas_2023_2024_2025.json")
    print("\nMe manda os 2 arquivos (upload aqui no chat) que eu completo a verificação.")
print("=" * 60)
