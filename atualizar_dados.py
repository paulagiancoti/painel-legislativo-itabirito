import requests
import json
import os
import sys
import time

# Garante saída imediata nos logs do GitHub Actions
sys.stdout.reconfigure(line_buffering=True)
from datetime import datetime, timezone, timedelta

BASE_URL = "https://sapl.itabirito.mg.leg.br"
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

def get_json(url, tentativas=2, espera=3):
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

ALERTAS = []

def alertar(msg):
    print(f"  ⚠️  ALERTA: {msg}")
    ALERTAS.append(msg)

# ─── 1. MATÉRIAS ──────────────────────────────────────────────────────────────

print("\n[1/4] Coletando matérias 2025 e 2026 (pesquisar-materia)...")

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
            f"Possível exclusão no SAPL ou falha parcial na coleta."
        )
    if max_id_novo < max_id_anterior:
        alertar(
            f"Maior ID diminuiu: {max_id_anterior} → {max_id_novo}. "
            f"Isso não deveria acontecer — verificar SAPL."
        )

    salvar_json("materias_historico.json", merged_hist)
    materias_2026 = [m for m in merged_hist if str(m.get("ano")) == "2026"]
    salvar_json("materias.json", materias_2026)
    print(f"  Matérias 2026: {len(materias_2026)}")
else:
    alertar("Nenhuma matéria nova coletada — mantendo dados anteriores intactos")

# ─── 2. NORMAS ────────────────────────────────────────────────────────────────

print("\n[2/4] Coletando normas 2026...")

existentes_normas = carregar_existente("normas.json")
total_leis_anterior = sum(
    1 for n in existentes_normas
    if n.get("tipo") == 1 or (isinstance(n.get("tipo"), dict) and n["tipo"].get("id") == 1)
)
print(f"  Leis Ordinárias existentes (tipo 1): {total_leis_anterior}")

novas_normas = coletar_paginado("/api/norma/normajuridica/?format=json&ano=2026")
if novas_normas:
    merged_normas = merge_por_id(existentes_normas, novas_normas)
    total_leis_novo = sum(
        1 for n in merged_normas
        if n.get("tipo") == 1 or (isinstance(n.get("tipo"), dict) and n["tipo"].get("id") == 1)
    )
    if total_leis_novo < total_leis_anterior:
        alertar(
            f"Leis Ordinárias (tipo 1) diminuíram: {total_leis_anterior} → {total_leis_novo}. "
            f"Verificar se houve exclusão indevida no SAPL."
        )
    salvar_json("normas.json", merged_normas)
else:
    alertar("Nenhuma norma coletada — mantendo dados anteriores")

# ─── 3. ASSUNTOS ──────────────────────────────────────────────────────────────

print("\n[3/4] Coletando assuntos...")
novos_ass = coletar_paginado("/api/materia/assuntomateria/?format=json")
if novos_ass:
    salvar_json("assuntos.json", novos_ass)
else:
    alertar("Nenhum assunto coletado — mantendo dados anteriores")

# ─── 4. VÍNCULOS MATÉRIA↔ASSUNTO ─────────────────────────────────────────────

print("\n[4/4] Coletando vínculos matéria↔assunto...")
novos_ma = coletar_paginado("/api/materia/materiaassunto/?format=json")
if novos_ma:
    salvar_json("materiaassuntos.json", novos_ma)
else:
    alertar("Nenhum vínculo de assunto coletado — mantendo dados anteriores")

# ─── TIMESTAMP ────────────────────────────────────────────────────────────────

agora = datetime.now(tz=FUSO).strftime("%d/%m/%Y às %H:%M")
with open("dados/ultima_atualizacao.json", "w", encoding="utf-8") as f:
    json.dump({"data_hora": agora}, f, ensure_ascii=False)
print(f"\n  Timestamp gravado: {agora}")

# ─── RESULTADO FINAL ──────────────────────────────────────────────────────────

print("\n" + "="*60)
if ALERTAS:
    print("⚠️  ALERTAS DETECTADOS — verificar antes do próximo deploy:")
    for a in ALERTAS:
        print(f"  • {a}")
    print("="*60)
    # Falha o workflow → GitHub envia e-mail de notificação
    import sys
    sys.exit(1)
else:
    print("✓ Atualização concluída sem alertas.")
    print("="*60)
