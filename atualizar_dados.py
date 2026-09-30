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
# Anos a coletar diariamente (só o(s) ano(s) ainda "abertos", com matérias
# que podem mudar). Anos fechados (legislativamente encerrados) NÃO entram
# aqui — ficam fixos em materias_historico.json, mesclados uma vez a partir
# de coleta pontual (ver coletar_pontual_2023_2024.py e equivalentes).
# 2023/2024/2025 foram mesclados manualmente em ago/2026 e saíram desta lista.
# Ao virar 2027, adicionar 2027 aqui e (quando 2026 fechar) removê-lo.
ANOS     = [2026]
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

def coletar_paginado_completo(endpoint):
    """
    Igual a coletar_paginado, mas também informa se a coleta chegou até a
    última página ou parou no meio por falha (timeout/erro esgotando as
    tentativas). Necessário para endpoints onde o resultado vira uma
    substituição direta do arquivo (sem merge_por_id): só é seguro substituir
    quando a coleta veio completa — uma coleta parcial não pode virar o novo
    arquivo, ou perderíamos os registros das páginas não alcançadas.
    """
    todos = []
    pagina = 1
    completo = True
    while True:
        sep = "&" if "?" in endpoint else "?"
        dados = get_json(f"{BASE_URL}{endpoint}{sep}page={pagina}")
        if dados is None:
            print(f"  Falhou na página {pagina} — abortando.")
            completo = False
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
    return todos, completo

def coletar_incrementais(endpoint, max_id_conhecido):
    """
    Coleta apenas registros com id > max_id_conhecido, sem depender do filtro
    id__gt funcionar no servidor (o SAPL de Itabirito ignora esse parâmetro
    em alguns endpoints).

    Detecta sozinha se o endpoint ordena crescente (mais antigo → mais novo,
    como relatorias/sessões) ou decrescente (mais novo → mais antigo, como
    normas — descoberto em 27/08/2026: a checagem rápida da página final
    reportava "sem novidade" com um ID bem menor que o maior já conhecido,
    sinal de que a página final tinha os registros MAIS ANTIGOS, não os mais
    novos). Compara o maior ID da página 1 com o da última página antes de
    decidir qual direção andar. Se não der pra determinar com confiança
    (falha ao buscar uma das duas), cai num fetch completo — mais lento,
    mas nunca perde registro silenciosamente.

    Exemplo (ordem crescente): 273 páginas, max_id=2675 → lê ~6 páginas em
    vez de 273 (anda da última pra primeira).
    Exemplo (ordem decrescente): anda da primeira pra última.
    """
    if max_id_conhecido == 0:
        print("  Primeira coleta — baixando tudo...")
        return coletar_paginado(endpoint)

    sep = "&" if "?" in endpoint else "?"

    dados_p1 = get_json(f"{BASE_URL}{endpoint}{sep}page=1")
    if not dados_p1:
        print("  Falhou ao consultar número de páginas.")
        return []
    if isinstance(dados_p1, list):
        return [r for r in dados_p1 if r["id"] > max_id_conhecido]

    total_pages = dados_p1.get("pagination", {}).get("total_pages", 1)
    resultados_p1 = dados_p1.get("results", [])
    ids_p1 = [r["id"] for r in resultados_p1]

    if total_pages == 1:
        return [r for r in resultados_p1 if r["id"] > max_id_conhecido]

    dados_ult = get_json(f"{BASE_URL}{endpoint}{sep}page={total_pages}")
    ids_ult = [r["id"] for r in dados_ult.get("results", [])] if dados_ult else []

    if not ids_p1 or not ids_ult:
        print("  Não deu pra confirmar a ordenação (falha ao consultar página) — baixando tudo (seguro).")
        return coletar_paginado(endpoint)

    def _varre(pagina_inicial, pagina_final, passo, dados_pagina_inicial):
        novos = []
        for pagina in range(pagina_inicial, pagina_final, passo):
            dados = dados_pagina_inicial if pagina == pagina_inicial else get_json(
                f"{BASE_URL}{endpoint}{sep}page={pagina}"
            )
            if not dados:
                print(f"  Falhou na página {pagina} — pulando.")
                continue
            resultados   = dados.get("results", [])
            novos_pagina = [r for r in resultados if r["id"] > max_id_conhecido]
            tem_antigo   = any(r["id"] <= max_id_conhecido for r in resultados)
            novos += novos_pagina
            seta = "→" if passo > 0 else "←"
            print(f"  {seta} Página {pagina}/{total_pages}: {len(novos_pagina)} novo(s)"
                  + (" — ponto de corte, parando" if tem_antigo else ""))
            if tem_antigo:
                break
            time.sleep(0.5)
        return novos

    if max(ids_p1) > max(ids_ult):
        # Ordem decrescente: página 1 tem os IDs mais novos.
        print(f"  Ordenação decrescente detectada. {total_pages} páginas — coletando da primeira em diante...")
        return _varre(1, total_pages + 1, 1, dados_p1)

    if max(ids_ult) <= max_id_conhecido:
        print(f"  Sem novos registros (maior ID na última página: {max(ids_ult)})")
        return []

    print(f"  {total_pages} páginas no total. Coletando da última para a primeira...")
    return _varre(total_pages, 0, -1, dados_ult)

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

print(f"\n[1/6] Coletando matérias {', '.join(str(a) for a in ANOS)} (pesquisar-materia)...")

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

# Busca via coletar_incrementais — agora com detecção automática de direção
# (ver docstring da função), então funciona mesmo com este endpoint
# ordenando do mais novo pro mais antigo, como descobrimos em 27/08/2026.
ep_normas = "/api/norma/normajuridica/?format=json&ano=2026"
novas_normas = coletar_incrementais(ep_normas, max_id_normas)

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

# ── 3a. Lista de assuntos (assuntomateria) ────────────────────────────────────
# Baixada a cada rodada (~5 páginas) para que assunto criado, renomeado ou
# apagado no SAPL entre sozinho. Se a coleta falhar ou vier incompleta, usa o
# assuntos.json já salvo como reserva — a etapa de vínculos segue normalmente.
print("\n[3/6] Coletando assuntos e vínculos matéria↔assunto...")
print("  Lista de assuntos:")
lista_ass_salva = carregar_existente("assuntos.json")
lista_ass_nova, completo_ass = coletar_paginado_completo("/api/materia/assuntomateria/?format=json")
if completo_ass and lista_ass_nova:
    salvar_json("assuntos.json", lista_ass_nova)
    lista_ass = lista_ass_nova
    ids_salvos = {int(a["id"]) for a in lista_ass_salva}
    ids_novos  = {int(a["id"]) for a in lista_ass_nova}
    if ids_novos != ids_salvos:
        print(f"  Assuntos novos: {sorted(ids_novos - ids_salvos)} · "
              f"removidos no SAPL: {sorted(ids_salvos - ids_novos)}")
else:
    alertar("Lista de assuntos não veio completa — usando assuntos.json salvo como reserva")
    lista_ass = lista_ass_salva
print(f"  {len(lista_ass)} assunto(s) na lista")

# ── 3b. Vínculos matéria↔assunto (pesquisar-materia, 1 pedido por assunto) ──
# Por que não paginar /api/materia/materiaassunto/: esse endpoint é ordenado
# por nome do assunto (não por id), então não tem coleta incremental — era
# preciso baixar as ~84 páginas todo dia, e o número crescia com os vínculos.
# Uma falha em qualquer página descartava a coleta inteira.
#
# A tela pesquisar-materia devolve tudo numa resposta só (sem paginação):
# 1 pedido por assunto, sem filtro de ano (pega todos os anos) — número fixo
# de pedidos (~44). Validado em 30/09/2026: os dois métodos deram exatamente
# os mesmos 831 pares (matéria, assunto).
#
# Cada assunto é independente. Se algum não responder (mesmo após uma
# repescagem), mantém os vínculos anteriores SÓ daquele assunto e avisa —
# os demais atualizam normalmente. Assunto que saiu da lista (apagado no
# SAPL) tem seus vínculos removidos. Mesmo par cadastrado 2x no SAPL vira 1.
#
# Formato salvo: {"materia": id, "assunto": id} — os únicos campos que o
# app lê de materiaassuntos.json.
print("  Vínculos (pesquisar-materia, 1 pedido por assunto):")
existentes_ma = carregar_existente("materiaassuntos.json")
anteriores_por_assunto = {}
for v in existentes_ma:
    anteriores_por_assunto.setdefault(int(v["assunto"]), set()).add(int(v["materia"]))
print(f"  Vínculos existentes: {len(existentes_ma)}")

pares_por_assunto = {}   # id do assunto → set de ids de matéria
falharam_ass = [int(a["id"]) for a in lista_ass]
for passada in range(2):
    if not falharam_ass:
        break
    if passada > 0:
        print(f"  Repescagem: {len(falharam_ass)} assunto(s) — aguardando 30s...")
        time.sleep(30)
    pendentes, falharam_ass = falharam_ass, []
    for aid in pendentes:
        dados = get_json(
            f"{BASE_URL}/materia/pesquisar-materia?format=json&materiaassunto__assunto={aid}"
        )
        if not isinstance(dados, dict) or "results" not in dados:
            falharam_ass.append(aid)
            continue
        pares_por_assunto[aid] = {int(r["id"]) for r in dados["results"]}
        time.sleep(0.5)
print(f"  {len(pares_por_assunto)}/{len(lista_ass)} assunto(s) coletado(s)")

if not pares_por_assunto:
    alertar("Nenhum assunto respondeu na coleta de vínculos — dados anteriores mantidos")
else:
    # Assunto que falhou: fica com os vínculos anteriores dele.
    for aid in falharam_ass:
        pares_por_assunto[aid] = anteriores_por_assunto.get(aid, set())
    todos_ma = [
        {"materia": m, "assunto": aid}
        for aid in sorted(pares_por_assunto) for m in sorted(pares_por_assunto[aid])
    ]
    unicos_antes = sum(len(v) for v in anteriores_por_assunto.values())
    # A trava de queda só considera assuntos que continuam na lista: apagar
    # um assunto no SAPL tira os vínculos dele de propósito, não é suspeito.
    ids_lista = {int(a["id"]) for a in lista_ass}
    antes_na_lista = sum(len(v) for k, v in anteriores_por_assunto.items() if k in ids_lista)
    removidos_ass = sorted(set(anteriores_por_assunto) - ids_lista)
    if removidos_ass:
        print(f"  Assunto(s) {removidos_ass} saíram da lista — vínculos deles removidos")
    if antes_na_lista and len(todos_ma) < 0.9 * antes_na_lista:
        # Queda grande é suspeita (SAPL devolvendo lista vazia, por exemplo):
        # não substitui, avisa para conferir.
        alertar(f"Vínculos caíram de {antes_na_lista} para {len(todos_ma)} — arquivo NÃO "
                f"substituído, conferir no SAPL", critico=True)
    else:
        salvar_json("materiaassuntos.json", todos_ma)
        print(f"  Total atual: {len(todos_ma)} vínculo(s) (antes: {unicos_antes})")
        if falharam_ass:
            alertar(f"Assunto(s) {sorted(falharam_ass)} não responderam — mantidos os "
                    f"vínculos anteriores deles, os demais foram atualizados")

# ─── 4. RELATORIAS (merge por ID — retroativas são comuns) ───────────────────

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

# ─── 5. ORADORES (pronunciamentos) — incremental por ID ─────────────────────

print("\n[5/6] Coletando oradores (pronunciamentos)...")
existentes_or = carregar_existente("oradores.json")
print(f"  Oradores existentes: {len(existentes_or)}")

# Corte: maior ID ENTRE OS QUE JÁ TÊM url_discurso preenchida — não o maior
# ID visto. O ID é atribuído na data do REGISTRO no SAPL, não na data da
# sessão (ex: um orador de 2025 registrado hoje ganha ID mais alto que um
# orador de 2026 já registrado há semanas). Um corte por "maior ID visto"
# travaria para sempre nesse tipo de registro, porque ele nunca vai ganhar
# URL. O corte por "maior ID COM url" se autocorrige: assim que qualquer
# registro mais recente ganhar URL (inclusive depois de um período sem posts
# no Instagram, como o período eleitoral), o corte anda sozinho — sem
# depender de ninguém lembrar de mudar algo manualmente.
ids_com_url = [int(o["id"]) for o in existentes_or if (o.get("url_discurso") or "").strip()]
corte_id = max(ids_com_url, default=0)

ano_atual = str(datetime.now(tz=FUSO).year)
if corte_id == 0:
    # Piso de segurança: se nenhum registro tem url ainda, cai no
    # comportamento antigo (ano corrente inteiro) em vez de arriscar buscar
    # tudo desde 2010 (o SAPL tem sessão registrada desde então).
    print(f"  Nenhum orador com url_discurso preenchida ainda — refresh completo de {ano_atual} (piso de segurança).")
    ep_or = f"/api/sessao/oradorordemdia/?format=json&sessao_plenaria__data_inicio__gte={ano_atual}-01-01"
    novos_or = coletar_paginado(ep_or)
else:
    print(f"  Maior ID com url_discurso preenchida: {corte_id}. Buscando registros mais novos que esse...")
    novos_or = coletar_incrementais("/api/sessao/oradorordemdia/?format=json", corte_id)

if novos_or:
    merged_or = merge_por_id(existentes_or, novos_or)
    salvar_json("oradores.json", merged_or)
    print(f"  {len(novos_or)} orador(es) coletado(s). Total no arquivo: {len(merged_or)}")
elif existentes_or:
    print("  Nenhum orador novo — dados anteriores mantidos")
else:
    alertar("Nenhum orador coletado — mantendo dados anteriores")

# ─── 6. SESSÕES PLENÁRIAS (para cruzar data com oradores) ────────────────────

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
