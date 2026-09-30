"""
coletar_pontual.py
Coleta pontual SÓ DE ORADORES (pronunciamentos) — baixa TODOS de novo.

Uso: depois de preencher links (url_discurso) no SAPL em registros ANTIGOS.
A coleta diária (atualizar_dados.py) é incremental pelo "maior ID com url" e
nunca volta para rebaixar registros antigos — esta coleta resolve isso.

Resistente a SAPL lento:
  - cada página tem várias tentativas, com espera crescente;
  - página que falhar não aborta a coleta: segue para as próximas e, no fim,
    tenta de novo só as que falharam (até 2 repescagens).
Segurança:
  - só SUBSTITUI o arquivo se TODAS as páginas vierem (assim também reflete
    exclusões feitas no SAPL);
  - se faltar alguma página, só mescla o que chegou (nada se perde) e
    termina com erro para você rodar de novo;
  - se vier bem menos registro que o arquivo atual, não substitui (suspeito).
"""

import requests
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta

# Garante saída imediata nos logs do GitHub Actions
sys.stdout.reconfigure(line_buffering=True)

BASE_URL = "https://sapl.itabirito.mg.leg.br"
ENDPOINT = "/api/sessao/oradorordemdia/?format=json"
FUSO     = timezone(timedelta(hours=-3))

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

TENTATIVAS_POR_PAGINA = 5     # por passada
ESPERA_BASE           = 10    # segundos; cresce a cada tentativa (10, 20, 30...)
REPESCAGENS           = 2     # passadas extras só nas páginas que falharam
PAUSA_ANTES_REPESCA   = 60    # segundos de folga pro SAPL antes de repescar

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def get_json(url, tentativas=TENTATIVAS_POR_PAGINA, espera=ESPERA_BASE):
    for i in range(tentativas):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=(20, 90))
            if resp.status_code == 200 and resp.text.strip():
                return resp.json()
            print(f"    HTTP {resp.status_code} — tentativa {i+1}/{tentativas}")
        except requests.exceptions.Timeout:
            print(f"    Timeout — tentativa {i+1}/{tentativas}")
        except Exception as e:
            print(f"    Erro: {e} — tentativa {i+1}/{tentativas}")
        if i < tentativas - 1:
            time.sleep(espera * (i + 1))
    return None

def url_pagina(pagina):
    return f"{BASE_URL}{ENDPOINT}&page={pagina}"

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

def gravar_timestamp():
    agora = datetime.now(tz=FUSO).strftime("%d/%m/%Y às %H:%M")
    os.makedirs("dados", exist_ok=True)
    with open("dados/ultima_atualizacao.json", "w", encoding="utf-8") as f:
        json.dump({"data_hora": agora}, f, ensure_ascii=False)
    print(f"  Timestamp gravado: {agora} (invalida o cache do painel)")

# ─── COLETA ───────────────────────────────────────────────────────────────────

print("\n[1] Coletando TODOS os oradores (pronunciamentos)...")
existentes_or = carregar_existente("oradores.json")
print(f"  Oradores no arquivo atual: {len(existentes_or)}")

primeira = get_json(url_pagina(1))
if not primeira:
    print("  ✗ SAPL não respondeu nem a página 1 — nada alterado. Tente mais tarde.")
    sys.exit(1)

if isinstance(primeira, list):
    # Endpoint sem paginação: veio tudo de uma vez
    por_pagina  = {1: primeira}
    total_pages = 1
else:
    total_pages = primeira.get("pagination", {}).get("total_pages", 1)
    por_pagina  = {1: primeira.get("results", [])}
print(f"  Página 1/{total_pages} ({len(por_pagina[1])} registros)")

faltando = list(range(2, total_pages + 1))
for passada in range(REPESCAGENS + 1):
    if not faltando:
        break
    if passada > 0:
        print(f"\n  Repescagem {passada}/{REPESCAGENS}: {len(faltando)} página(s) — "
              f"aguardando {PAUSA_ANTES_REPESCA}s antes...")
        time.sleep(PAUSA_ANTES_REPESCA)
    falharam = []
    for pagina in faltando:
        dados = get_json(url_pagina(pagina))
        if dados is None:
            print(f"  ✗ Página {pagina}/{total_pages} falhou — segue para a próxima")
            falharam.append(pagina)
            continue
        resultados = dados.get("results", []) if isinstance(dados, dict) else dados
        por_pagina[pagina] = resultados
        print(f"  Página {pagina}/{total_pages} ({len(resultados)} registros)")
        time.sleep(0.5)
    faltando = falharam

coletados = [r for p in sorted(por_pagina) for r in por_pagina[p]]
# Remove duplicados (se a paginação "andou" durante a coleta, um registro
# pode aparecer em duas páginas) mantendo a ordem do SAPL.
vistos, novos_or = set(), []
for r in coletados:
    if str(r["id"]) not in vistos:
        vistos.add(str(r["id"]))
        novos_or.append(r)

print(f"\n  Coletados: {len(novos_or)} oradores em {len(por_pagina)}/{total_pages} páginas")

# ─── SALVAR ───────────────────────────────────────────────────────────────────

sucesso = False
if faltando:
    print(f"  ⚠️  Páginas que não vieram mesmo após as repescagens: {faltando}")
    if novos_or:
        merged = merge_por_id(existentes_or, novos_or)
        salvar_json("oradores.json", merged)
        print("  Arquivo NÃO substituído — só mesclado o que chegou (nada foi perdido).")
        gravar_timestamp()
    print("  → Rode de novo mais tarde para completar.")
elif existentes_or and len(novos_or) < 0.9 * len(existentes_or):
    print(f"  🔴 Veio {len(novos_or)} oradores, bem menos que os {len(existentes_or)} atuais — "
          f"arquivo NÃO alterado. Conferir o SAPL antes de rodar de novo.")
else:
    ids_antes  = {str(o["id"]) for o in existentes_or}
    ids_depois = {str(o["id"]) for o in novos_or}
    com_url    = sum(1 for o in novos_or if (o.get("url_discurso") or "").strip())
    antes_url  = sum(1 for o in existentes_or if (o.get("url_discurso") or "").strip())
    salvar_json("oradores.json", novos_or)
    print(f"  Arquivo substituído. Com url_discurso: {antes_url} → {com_url}. "
          f"Novos: {len(ids_depois - ids_antes)} · removidos (excluídos no SAPL): "
          f"{len(ids_antes - ids_depois)}")
    gravar_timestamp()
    sucesso = True

print("\n" + "=" * 60)
if sucesso:
    print("✓ Coleta pontual de oradores concluída e completa.")
    print("=" * 60)
    sys.exit(0)
print("⚠️  Coleta pontual NÃO ficou completa — ver mensagens acima.")
print("=" * 60)
sys.exit(1)
