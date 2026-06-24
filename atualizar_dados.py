import requests
import json
import os
import sys
import time

# Garante saída imediata nos logs do GitHub Actions
sys.stdout.reconfigure(line_buffering=True)
from datetime import datetime, timezone, timedelta

# ╔══════════════════════════════════════════════════════════════════╗
# ║  PERSONALIZAÇÃO — ajuste estas variáveis para outra Casa        ║
# ╚══════════════════════════════════════════════════════════════════╝

# URL do SAPL da sua Casa Legislativa
BASE_URL = "https://sapl.itabirito.mg.leg.br"
# Anos a coletar. Adicione anos anteriores para ter histórico completo.
# Quanto mais anos, mais lenta a coleta — avalie o necessário.
ANOS     = [2025, 2026]
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

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def get_json(url, tentativas=3, espera=8):
    for i in range(tentativas):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=(15, 60))
            if resp.status_code == 200 and resp.text.strip():
                return resp.json()
            print(f"    HTTP {resp.status_code} — tentativa {i+1}/{tentativas}")
        except requests.exceptions.Timeout:
            print(f"    Timeout — tentativa {i+1}/{tentativas}")
        except Exception as e:
            print(f"    Erro: {e} — tentativa {i+1}/{tentativas}")
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

def coletar_incrementais(endpoint, max_id_conhecido):
    """
    Coleta apenas registros com id > max_id_conhecido, sem depender do filtro
    id__gt funcionar no servidor (o SAPL de Itabirito ignora esse parâmetro).

    Estratégia: começa da ÚLTIMA página (IDs mais altos) e volta página a página
    até encontrar um ID já conhecido. Para quando encontra — não pagina o passado.

    Exemplo: 273 páginas, max_id=2675 → lê ~6 páginas em vez de 273.
    Assume ordenação padrão do DRF (id crescente do início ao fim das páginas).
    """
    if max_id_conhecido == 0:
        print("  Primeira coleta — baixando tudo...")
        return coletar_paginado(endpoint)

    sep = "&" if "?" in endpoint else "?"

    # Passo 1: descobrir total de páginas
    dados_p1 = get_json(f"{BASE_URL}{endpoint}{sep}page=1")
    if not dados_p1:
        print("  Falhou ao consultar número de páginas.")
        return []
    if isinstance(dados_p1, list):
        return [r for r in dados_p1 if r["id"] > max_id_conhecido]

    total_pages = dados_p1.get("pagination", {}).get("total_pages", 1)

    # Passo 2: verificar rapidamente se há novidades na última página
    dados_ult = dados_p1 if total_pages == 1 else get_json(
        f"{BASE_URL}{endpoint}{sep}page={total_pages}"
    )
    if dados_ult:
        ids_ult = [r["id"] for r in dados_ult.get("results", [])]
        if ids_ult and max(ids_ult) <= max_id_conhecido:
            print(f"  Sem novos registros (maior ID na última página: {max(ids_ult)})")
            return []

    print(f"  {total_pages} páginas no total. Coletando da última para a primeira...")
    novos = []

    for pagina in range(total_pages, 0, -1):
        # Reutiliza a última página já buscada no passo 2
        dados = dados_ult if pagina == total_pages else get_json(
            f"{BASE_URL}{endpoint}{sep}page={pagina}"
        )
        if not dados:
            print(f"  Falhou na página {pagina} — pulando.")
            continue

        resultados   = dados.get("results", [])
        novos_pagina = [r for r in resultados if r["id"] > max_id_conhecido]
        tem_antigo   = any(r["id"] <= max_id_conhecido for r in resultados)

        novos += novos_pagina
        print(f"  ← Página {pagina}/{total_pages}: {len(novos_pagina)} novo(s)"
              + (" — ponto de corte, parando" if tem_antigo else ""))

        if tem_antigo:
            break

        time.sleep(0.5)

    return novos

def carregar_existente(nome_arquivo):
    """Carrega dados existentes do JSON, retorna lista vazia se não existir."""
    caminho = os.path.join("dados", nome_arquivo)
    if os.path.exists(caminho):
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    return []

def merge_por_id(existentes, novos):
    """
    Combina existentes + novos por ID.
    Novos registros sobrescrevem existentes (corrigem dados).
    Registros existentes sem correspondência nos novos são preservados.
    """
    mapa = {str(r["id"]): r for r in existentes}
    for r in novos:
        mapa[str(r["id"])] = r   # novo sobrescreve (atualiza) o existente
    return list(mapa.values())

def salvar_json(nome_arquivo, dados):
    os.makedirs("dados", exist_ok=True)
    caminho = os.path.join("dados", nome_arquivo)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print(f"  ✓ Salvo: {caminho} ({len(dados)} registros)")

ALERTAS_SAPL     = []   # SAPL indisponível — comportamento esperado, dados preservados
ALERTAS_CRITICOS = []   # Integridade dos dados — requer atenção imediata

def alertar(msg, critico=False):
    nivel = "🔴 CRÍTICO" if critico else "⚠️  AVISO"
    print(f"  {nivel}: {msg}")
    if critico:
        ALERTAS_CRITICOS.append(msg)
    else:
        ALERTAS_SAPL.append(msg)

# ─── 1. MATÉRIAS ──────────────────────────────────────────────────────────────

print("\n[1/6] Coletando matérias 2025 e 2026 (pesquisar-materia)...")

# Carrega estado anterior
existentes_hist = carregar_existente("materias_historico.json")
max_id_anterior = max((r["id"] for r in existentes_hist), default=0)
total_anterior  = len(existentes_hist)
print(f"  Dados anteriores: {total_anterior} matérias, maior ID={max_id_anterior}")

novos_hist = []
for ano in ANOS:
    print(f"  Ano {ano}:")
    url = (
        f"{BASE_URL}/materia/pesquisar-materia"
        f"?format=json&ano={ano}&tipo_listagem=1&salvar=Pesquisar"
    )
    dados = get_json(url)
    if dados and isinstance(dados, dict) and dados.get("results"):
        registros = dados["results"]
        novos_hist += registros
        print(f"  → {len(registros)} matérias coletadas")
    else:
        alertar(f"Falha ao coletar matérias de {ano} — endpoint sem resposta")

if novos_hist:
    merged_hist = merge_por_id(existentes_hist, novos_hist)
    total_merged = len(merged_hist)
    max_id_novo  = max((r["id"] for r in merged_hist), default=0)

    print(f"  Após merge: {total_merged} matérias, maior ID={max_id_novo}")

    # Validações
    if total_merged < total_anterior:
        alertar(
            f"Total de matérias diminuiu: {total_anterior} → {total_merged}. "
            f"Possível exclusão no SAPL ou falha parcial na coleta.",
            critico=True
        )
    if max_id_novo < max_id_anterior:
        alertar(
            f"Maior ID diminuiu: {max_id_anterior} → {max_id_novo}. "
            f"Isso não deveria acontecer — verificar SAPL.",
            critico=True
        )

    salvar_json("materias_historico.json", merged_hist)
    materias_2026 = [m for m in merged_hist if str(m.get("ano")) == "2026"]
    salvar_json("materias.json", materias_2026)
    print(f"  Matérias 2026: {len(materias_2026)}")
else:
    alertar("Nenhuma matéria nova coletada — mantendo dados anteriores intactos")

# ─── 2. NORMAS ────────────────────────────────────────────────────────────────

print("\n[2/6] Coletando normas 2026...")

existentes_normas = carregar_existente("normas.json")
max_id_normas = max((n["id"] for n in existentes_normas), default=0)
total_leis_anterior = sum(
    1 for n in existentes_normas
    if n.get("tipo") == 1 or (isinstance(n.get("tipo"), dict) and n["tipo"].get("id") == 1)
)
print(f"  Normas existentes: {len(existentes_normas)}, maior ID={max_id_normas}")
print(f"  Leis Ordinárias existentes (tipo 1): {total_leis_anterior}")

# Incremental: só busca normas de 2026 com ID maior que o já armazenado.
# Novas leis sempre têm ID maior — leis existentes não são alteradas.
if max_id_normas > 0:
    ep_normas = f"/api/norma/normajuridica/?format=json&ano=2026&id__gt={max_id_normas}"
    print(f"  Buscando apenas novas (id > {max_id_normas})...")
else:
    ep_normas = "/api/norma/normajuridica/?format=json&ano=2026"
    print("  Primeira coleta — baixando todas...")

novas_normas = coletar_paginado(ep_normas)
if novas_normas:
    merged_normas = merge_por_id(existentes_normas, novas_normas)
    # PERSONALIZAÇÃO: mesmo ID de lei ordinária acima
    total_leis_novo = sum(
        1 for n in merged_normas
        if n.get("tipo") == 1 or (isinstance(n.get("tipo"), dict) and n["tipo"].get("id") == 1)
    )
    if total_leis_novo < total_leis_anterior:
        alertar(
            f"Leis Ordinárias (tipo 1) diminuíram: {total_leis_anterior} → {total_leis_novo}. "
            f"Verificar se houve exclusão indevida no SAPL.",
            critico=True
        )
    salvar_json("normas.json", merged_normas)
    print(f"  {len(novas_normas)} nova(s) norma(s). Total: {len(merged_normas)}")
elif max_id_normas > 0:
    print("  Nenhuma norma nova — dados anteriores mantidos")
else:
    alertar("Nenhuma norma coletada — mantendo dados anteriores")

# ─── 3. ASSUNTOS ──────────────────────────────────────────────────────────────

print("\n[3/6] Coletando vínculos matéria↔assunto...")
novos_ma = coletar_paginado("/api/materia/materiaassunto/?format=json")
if novos_ma:
    salvar_json("materiaassuntos.json", novos_ma)
else:
    alertar("Nenhum vínculo de assunto coletado — mantendo dados anteriores")

# ─── 5. RELATORIAS (merge por ID — retroativas são comuns) ───────────────────

print("\n[4/6] Coletando relatorias...")
existentes_rel = carregar_existente("relatorias.json")
max_id_rel = max((r["id"] for r in existentes_rel), default=0)
print(f"  Relatorias existentes: {len(existentes_rel)}, maior ID={max_id_rel}")
# Nota: o SAPL de Itabirito ignora o parâmetro id__gt neste endpoint.
# Usamos coletar_incrementais que começa da última página e para quando
# encontra um ID já conhecido — muito mais rápido que paginar tudo.
novas_rel = coletar_incrementais("/api/materia/relatoria/?format=json", max_id_rel)
if novas_rel:
    merged_rel = merge_por_id(existentes_rel, novas_rel)
    print(f"  {len(novas_rel)} nova(s) relatoria(s) encontrada(s)")
    salvar_json("relatorias.json", merged_rel)
    print(f"  Total após merge: {len(merged_rel)} relatorias")
elif max_id_rel > 0:
    print("  Nenhuma relatoria nova — dados anteriores mantidos")
else:
    alertar("Nenhuma relatoria coletada — mantendo dados anteriores")

# Comissões e tipos de matéria são fixos — coletados uma única vez via coletar_dados_iniciais.py

# ─── 6. ORADORES (pronunciamentos) — incremental por ID ─────────────────────

print("\n[5/6] Coletando oradores (pronunciamentos)...")
existentes_or = carregar_existente("oradores.json")
print(f"  Oradores existentes: {len(existentes_or)}")

# Busca sempre o ano corrente completo (sem id__gt).
# Motivo: o orador é registrado no SAPL no dia da sessão (ID atribuído),
# mas o url_discurso é adicionado dias depois quando o vídeo é postado.
# Com id__gt nunca buscaríamos de novo o registro existente para pegar o link.
# Buscar o ano inteiro (~300-400 registros) é rápido e garante que url_discurso
# seja sempre atualizado nos registros já armazenados.
ano_atual = str(datetime.now(tz=FUSO).year)
ep_or = f"/api/sessao/oradorordemdia/?format=json&sessao_plenaria__data_inicio__gte={ano_atual}-01-01"
print(f"  Buscando todos os oradores de {ano_atual} (refresh completo do ano)...")
novos_or = coletar_paginado(ep_or)
if novos_or:
    merged_or = merge_por_id(existentes_or, novos_or)
    salvar_json("oradores.json", merged_or)
    print(f"  {len(novos_or)} orador(es) de {ano_atual}. Total no arquivo: {len(merged_or)}")
elif existentes_or:
    print("  Nenhum orador coletado — dados anteriores mantidos")
else:
    alertar("Nenhum orador coletado — mantendo dados anteriores")

# ─── 8. SESSÕES PLENÁRIAS (para cruzar data com oradores) ────────────────────

print("\n[6/6] Coletando sessões plenárias...")
existentes_sess = carregar_existente("sessoes.json")
max_id_sess = max((r["id"] for r in existentes_sess), default=0)
print(f"  Sessões existentes: {len(existentes_sess)}, maior ID={max_id_sess}")
# Mesmo comportamento das relatorias: id__gt ignorado pelo SAPL.
novas_sess = coletar_incrementais("/api/sessao/sessaoplenaria/?format=json", max_id_sess)
if novas_sess:
    merged_sess = merge_por_id(existentes_sess, novas_sess)
    salvar_json("sessoes.json", merged_sess)
    print(f"  {len(novas_sess)} nova(s) sessão(ões). Total: {len(merged_sess)}")
elif max_id_sess > 0:
    print("  Nenhuma sessão nova — dados anteriores mantidos")
else:
    alertar("Nenhuma sessão coletada — mantendo dados anteriores")

# ─── TIMESTAMP ────────────────────────────────────────────────────────────────
# Só grava o timestamp se pelo menos as matérias foram coletadas com sucesso

if novos_hist:
    agora = datetime.now(tz=FUSO).strftime("%d/%m/%Y às %H:%M")
    with open("dados/ultima_atualizacao.json", "w", encoding="utf-8") as f:
        json.dump({"data_hora": agora}, f, ensure_ascii=False)
    print(f"\n  Timestamp gravado: {agora}")
else:
    print("\n  Timestamp NÃO atualizado — coleta falhou, mantendo data anterior.")

# ─── RESULTADO FINAL ──────────────────────────────────────────────────────────

print("\n" + "="*60)
if ALERTAS_CRITICOS:
    print("🔴 ALERTAS CRÍTICOS — verificar imediatamente:")
    for a in ALERTAS_CRITICOS:
        print(f"  • {a}")
    if ALERTAS_SAPL:
        print("⚠️  Também houve falhas de conexão com o SAPL:")
        for a in ALERTAS_SAPL:
            print(f"  • {a}")
    print("="*60)
    sys.exit(1)   # falha o workflow → GitHub envia e-mail de notificação
elif ALERTAS_SAPL:
    print("⚠️  SAPL indisponível — dados anteriores preservados:")
    for a in ALERTAS_SAPL:
        print(f"  • {a}")
    print("="*60)
    sys.exit(1)   # falha o workflow → e-mail chega → lembrete para atualizar manualmente
else:
    print("✓ Atualização concluída sem alertas.")
    print("="*60)
    sys.exit(0)
