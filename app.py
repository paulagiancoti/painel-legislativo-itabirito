import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
from collections import defaultdict

st.set_page_config(
    page_title="Painel Legislativo — Itabirito",
    page_icon="🏛️",
    layout="wide"
)

@st.cache_data(show_spinner="⏳ Carregando dados do Painel Legislativo...")
def carregar_dados(ultima_atualizacao=""):
    """O parâmetro ultima_atualizacao serve como chave de cache:
    quando os dados são atualizados, o timestamp muda e o cache é invalidado automaticamente."""
    with open("dados/vereadores.json", encoding="utf-8") as f:
        vereadores = json.load(f)
    with open("dados/mesa_diretora.json", encoding="utf-8") as f:
        mesa = json.load(f)
    with open("dados/autores.json", encoding="utf-8") as f:
        autores = json.load(f)
    with open("dados/materias.json", encoding="utf-8") as f:
        materias = json.load(f)
    hist_path = "dados/materias_historico.json"
    with open(hist_path if os.path.exists(hist_path) else "dados/materias.json", encoding="utf-8") as f:
        materias_hist = json.load(f)
    with open("dados/normas.json", encoding="utf-8") as f:
        normas = json.load(f)
    with open("dados/assuntos.json", encoding="utf-8") as f:
        assuntos = json.load(f)
    with open("dados/materiaassuntos.json", encoding="utf-8") as f:
        materiaassuntos = json.load(f)
    # Relatorias e comissões — opcionais (arquivo pode não existir ainda)
    relatorias_raw = []
    if os.path.exists("dados/relatorias.json"):
        with open("dados/relatorias.json", encoding="utf-8") as f:
            relatorias_raw = json.load(f)
    sessoes_raw = []
    if os.path.exists("dados/sessoes.json"):
        with open("dados/sessoes.json", encoding="utf-8") as f:
            sessoes_raw = json.load(f)
    oradores_raw = []
    if os.path.exists("dados/oradores.json"):
        with open("dados/oradores.json", encoding="utf-8") as f:
            oradores_raw = json.load(f)
    pronunc_extras_raw = []
    if os.path.exists("dados/pronunciamentos_extras.json"):
        with open("dados/pronunciamentos_extras.json", encoding="utf-8") as f:
            pronunc_extras_raw = json.load(f)
    comissoes_raw = []
    if os.path.exists("dados/comissoes.json"):
        with open("dados/comissoes.json", encoding="utf-8") as f:
            comissoes_raw = json.load(f)
    tipomaterias_raw = []
    if os.path.exists("dados/tipomaterias.json"):
        with open("dados/tipomaterias.json", encoding="utf-8") as f:
            tipomaterias_raw = json.load(f)

    df_vereadores    = pd.DataFrame(vereadores)[['id', 'nome_completo', 'nome_parlamentar', 'fotografia']]
    # ╔══════════════════════════════════════════════════════════════════╗
    # ║  PERSONALIZAÇÃO — ajuste conforme os tipos de autor da sua Casa  ║
    # ╚══════════════════════════════════════════════════════════════════╝
    # Os IDs 1-7 são tipos fixos do SAPL (iguais em qualquer instalação):
    #   1=Parlamentar, 2=Comissão, 3=Bancada, 4=Externo,
    #   5=Frente, 6=Bloco, 7=Órgão
    # A partir do ID 8 são tipos criados por cada Casa — verifique em:
    # <BASE_SAPL_URL>/api/base/tipodeautor/?format=json
    # No SAPL de Itabirito: 8=Chefe do Executivo (tipo local da Casa)
    # Em outras Casas, "Chefe do Executivo" pode ter outro ID ou nome diferente.
    MAPA_TIPO_AUTOR = {
        1: 'Parlamentar', 2: 'Comissão', 3: 'Bancada', 4: 'Externo',
        5: 'Frente', 6: 'Bloco', 7: 'Órgão', 8: 'Chefe do Executivo',
    }
    df_autores = pd.DataFrame(autores)[['id', 'nome', 'tipo']].copy()
    df_autores['tipo_descricao'] = df_autores['tipo'].map(MAPA_TIPO_AUTOR).fillna('Desconhecido')

    # nome do parlamentar → id de Autor no SAPL (para montar links de pesquisa)
    # PERSONALIZAÇÃO: tipo == 1 filtra apenas "Parlamentar" (fixo no SAPL).
    # Se sua Casa usar tipo diferente para vereadores, ajuste aqui.
    mapa_autor_id = (
        df_autores[df_autores['tipo'] == 1]
        .set_index('nome')['id'].to_dict()
    )
    df_materias      = pd.DataFrame(materias)        # só 2026 — exibição
    df_materias_hist = pd.DataFrame(materias_hist)   # 2025+2026 — cruzamento normas

    def normalizar_campos(df):
        """Garante que os campos tipo__sigla, tipo__descricao e autoria existam,
        independente de virem do endpoint de pesquisa ou da API REST."""
        if df.empty:
            return df
        # tipo__sigla / tipo__descricao — API REST retorna campo 'tipo' como objeto
        if 'tipo__sigla' not in df.columns:
            if 'tipo' in df.columns:
                df['tipo__sigla']    = df['tipo'].apply(
                    lambda t: t.get('sigla', '') if isinstance(t, dict) else '')
                df['tipo__descricao'] = df['tipo'].apply(
                    lambda t: t.get('descricao', '') if isinstance(t, dict) else '')
            else:
                df['tipo__sigla']    = ''
                df['tipo__descricao'] = ''
        # autoria — API REST pode usar 'autoria_set' em vez de 'autoria'
        if 'autoria' not in df.columns:
            if 'autoria_set' in df.columns:
                df['autoria'] = df['autoria_set']
            else:
                df['autoria'] = ''
        return df

    df_materias      = normalizar_campos(df_materias)
    df_materias_hist = normalizar_campos(df_materias_hist)
    df_normas        = pd.DataFrame(normas)

    mapa_cargo_mesa = {
        str(m['parlamentar']): m['__str__'].split(' - ')[-1].strip()
        for m in mesa
    }
    df_vereadores['cargo_mesa'] = df_vereadores['id'].astype(str).map(mapa_cargo_mesa).fillna('')

    mapa_assunto_nome = {a['id']: a['assunto'] for a in assuntos}
    # nome do assunto → id (para montar links de pesquisa)
    mapa_assunto_id = {a['assunto']: a['id'] for a in assuntos}
    mapa_id_assuntos  = defaultdict(list)
    for v in materiaassuntos:
        nome = mapa_assunto_nome.get(v['assunto'], f"ID {v['assunto']}")
        mapa_id_assuntos[str(v['materia'])].append(nome)

    mapa_id_numero = {
        str(row['id']): int(row['numero'])
        for _, row in df_materias.iterrows()
        # PERSONALIZAÇÃO: siglas dos tipos de matéria da sua Casa.
        # PLO=Projeto de Lei Ordinária, PLS=Substitutivo, PLS2=2º Substitutivo.
        # Verifique as siglas em /api/materia/tipomateria/?format=json
        if row['tipo__sigla'] in ('PLO', 'PLS', 'PLS2')
    }
    assuntos_por_numero = defaultdict(set)
    for mid, ass_lista in mapa_id_assuntos.items():
        numero = mapa_id_numero.get(mid)
        if numero is not None:
            for a in ass_lista:
                assuntos_por_numero[numero].add(a)

    # Expandir autorias — só 2026
    linhas = []
    for _, row in df_materias.iterrows():
        autoria_raw = (
            row.get('autoria') or
            row.get('autoria_set') or
            row.get('autores') or
            ''
        )
        # Extrai nomes de autores — pode vir como:
        # 1. String "Nome1, Nome2" (endpoint pesquisar-materia)
        # 2. Lista de objetos [{autor: {nome: "..."}, ...}] (API REST)
        if isinstance(autoria_raw, list):
            nomes_autores = []
            for item in autoria_raw:
                if isinstance(item, dict):
                    # Tenta vários caminhos possíveis no objeto
                    nome = (
                        (item.get('autor') or {}).get('nome') or
                        (item.get('autor') or {}).get('__str__') or
                        item.get('nome') or
                        item.get('__str__') or
                        ''
                    )
                    if nome:
                        nomes_autores.append(nome.strip())
                elif isinstance(item, str) and item.strip():
                    nomes_autores.append(item.strip())
        elif isinstance(autoria_raw, str):
            nomes_autores = [a.strip() for a in autoria_raw.split(',') if a.strip()]
        else:
            nomes_autores = []

        numero      = int(row['numero'])
        tipo_sigla  = row['tipo__sigla']
        assuntos_proj = (
            list(assuntos_por_numero.get(numero, []))
            if tipo_sigla == 'PLO'
            else mapa_id_assuntos.get(str(row['id']), [])
        )
        for nome_autor in nomes_autores:
            linhas.append({
                'materia_id':     row['id'],
                'numero':         numero,
                'ano':            row['ano'],
                'tipo_sigla':     tipo_sigla,
                'tipo_descricao': row['tipo__descricao'],
                'ementa':         row['ementa'],
                'autor_nome':     nome_autor,
                'assuntos':       assuntos_proj,
                'tem_assunto':    len(assuntos_proj) > 0,
            })

    df = pd.DataFrame(linhas)
    if df.empty or 'autor_nome' not in df.columns:
        st.warning(
            "⚠️ Os dados de autoria das matérias não foram encontrados. "
            "Rode `atualizar_dados.py` localmente e suba os JSONs atualizados para o GitHub. "
            f"Campos disponíveis: {list(df_materias.columns[:8]) if not df_materias.empty else 'arquivo vazio'}"
        )
        df = pd.DataFrame(columns=[
            'materia_id', 'numero', 'ano', 'tipo_sigla', 'tipo_descricao',
            'ementa', 'autor_nome', 'assuntos', 'tem_assunto'
        ])
    mapa_tipo    = df_autores.set_index('nome')['tipo_descricao'].to_dict()
    nomes_ativos = set(df_vereadores['nome_parlamentar'])
    df['autor_tipo']       = df['autor_nome'].map(mapa_tipo).fillna('Desconhecido')
    df['e_vereador_ativo'] = df['autor_nome'].isin(nomes_ativos)

    pls_numeros = set(df[df['tipo_sigla'].isin(['PLS', 'PLS2'])]['numero'])
    df['plo_teve_substitutivo'] = (
        (df['tipo_sigla'] == 'PLO') & (df['numero'].isin(pls_numeros))
    )

    # ── Cruzamento normas → PLOs (histórico 2025+2026) ──────────────────────────
    df_materias_hist['id_str']     = df_materias_hist['id'].astype(str)
    df_materias_hist['numero_int'] = df_materias_hist['numero'].astype(int)
    mapa_tipo_mat   = df_materias_hist.set_index('id_str')['tipo__sigla'].to_dict()
    mapa_numero_mat = df_materias_hist.set_index('id_str')['numero_int'].to_dict()
    mapa_ano_mat    = df_materias_hist.set_index('id_str')['ano'].to_dict()
    # mapa_plo_num: só PLOs de 2026 — evita colisão de número entre anos
    # (PLO nº 30 de 2025 e PLO nº 30 de 2026 têm o mesmo numero_int;
    #  sem filtro de ano, um sobrescreveria o outro no dict)
    mapa_plo_num    = (
        df_materias_hist[
            (df_materias_hist['tipo__sigla'] == 'PLO') &
            (df_materias_hist['ano'].astype(str) == '2026')
        ]
        .set_index('numero_int')['id_str'].to_dict()
    )
    # Mapa: plo_id → autoria (do histórico)
    mapa_plo_autoria = (
        df_materias_hist[df_materias_hist['tipo__sigla'] == 'PLO']
        .set_index('id_str')['autoria']
        .fillna('')
        .to_dict()
    )

    detalhes_leis = []
    for _, norma in df_normas[df_normas['materia'].notna()].iterrows():
        mid  = str(int(norma['materia']))
        tipo = mapa_tipo_mat.get(mid)
        num  = mapa_numero_mat.get(mid)
        if not tipo or num is None:
            continue
        if tipo == 'PLO':
            plo_id = mid
        elif tipo in ('PLS', 'PLS2'):
            plo_id = mapa_plo_num.get(num)
            if not plo_id:
                continue
        else:
            continue

        # Só conta PLOs do ano de referência (2026) — PLOs de 2025 aprovados
        # em 2026 não são creditados ao desempenho do ano corrente
        if str(mapa_ano_mat.get(plo_id, '')).strip() != '2026':
            continue

        # Autores do PLO original (sempre de 2026 após o filtro acima)
        autoria_plo = mapa_plo_autoria.get(plo_id, '')
        autores_plo = [a.strip() for a in autoria_plo.split(',') if a.strip()] or ['']

        for autor_plo in autores_plo:
            detalhes_leis.append({
                'plo_id':        plo_id,
                'numero_plo':    num,
                'vinculado_via': tipo,
                'lei_numero':    norma['numero'],
                'lei_ementa':    norma['ementa'],
                'autor_nome':    autor_plo,
            })

    df_leis = (
        pd.DataFrame(detalhes_leis).drop_duplicates(['plo_id', 'autor_nome'])
        if detalhes_leis else pd.DataFrame(
            columns=['plo_id', 'numero_plo', 'vinculado_via', 'lei_numero', 'lei_ementa', 'autor_nome']
        )
    )

    # Marca plo_virou_lei em df (2026) para uso nas flags de assunto
    plos_lei_set = set(df_leis['plo_id'])
    df['plo_virou_lei'] = (
        (df['tipo_sigla'] == 'PLO') &
        (df['materia_id'].astype(str).isin(plos_lei_set))
    )

    # ── Resumo por vereador ──────────────────────────────────────────────────────
    df_parl     = df[df['e_vereador_ativo']]
    df_plo_parl = df[(df['e_vereador_ativo']) & (df['tipo_sigla'] == 'PLO')]

    ids_mesa   = set(str(m['parlamentar']) for m in mesa)
    nomes_mesa = set(df_vereadores[df_vereadores['id'].astype(str).isin(ids_mesa)]['nome_parlamentar'])
    qtd_mesa   = len(df[
        (df['autor_nome'] == 'Mesa Diretora - MESA') |
        (df['autor_nome'].str.contains('Mesa Diretora', na=False))
    ]['materia_id'].unique())
    df_vereadores['materias_mesa'] = df_vereadores['nome_parlamentar'].apply(
        lambda n: qtd_mesa if n in nomes_mesa else 0
    )

    resumo = (
        df_parl[~df_parl['tipo_sigla'].isin(['PLS', 'PLS2'])].groupby('autor_nome')
        .agg(
            total_geral   = ('materia_id', 'count'),
            indicacoes    = ('tipo_sigla', lambda x: (x == 'IND').sum()),
            requerimentos = ('tipo_sigla', lambda x: (x == 'REQ').sum()),
            emendas       = ('tipo_sigla', lambda x: (x == 'EME').sum()),
            mocoes        = ('tipo_sigla', lambda x: x.isin(['MOC']).sum()),
            resolucoes    = ('tipo_sigla', lambda x: (x == 'PRE').sum()),
        )
        .reset_index()
    )

    # PLOs por vereador — contagem única (deduplifica co-autorias)
    plo_por_autor = (
        df_plo_parl.groupby('autor_nome')['materia_id']
        .nunique().reset_index(name='projetos_lei')
    )
    sub_por_autor = (
        df_plo_parl.groupby('autor_nome')['plo_teve_substitutivo']
        .sum().reset_index(name='projetos_com_substitutivo')
    )

    # PLOs aprovados por vereador — via df_leis (inclui 2025+2026)
    df_leis_ativos = df_leis[df_leis['autor_nome'].isin(nomes_ativos)]
    aprov_por_autor = (
        df_leis_ativos.groupby('autor_nome')['plo_id']
        .nunique().reset_index(name='projetos_virou_lei')
    )

    plo_res = plo_por_autor.merge(sub_por_autor, on='autor_nome', how='left')
    plo_res = plo_res.merge(aprov_por_autor, on='autor_nome', how='left')
    plo_res = plo_res.fillna(0)
    for col in ['projetos_lei', 'projetos_com_substitutivo', 'projetos_virou_lei']:
        plo_res[col] = plo_res[col].astype(int)

    resumo = resumo.merge(plo_res, on='autor_nome', how='left').fillna(0)
    for col in ['projetos_lei', 'projetos_com_substitutivo', 'projetos_virou_lei']:
        resumo[col] = resumo[col].astype(int)

    resumo['taxa_aprovacao'] = (
        (resumo['projetos_virou_lei'] / resumo['projetos_lei'] * 100)
        .round(1).fillna(0)
    )
    mapa_materias_mesa = df_vereadores.set_index('nome_parlamentar')['materias_mesa'].to_dict()
    resumo['materias_mesa'] = resumo['autor_nome'].map(mapa_materias_mesa).fillna(0).astype(int)

    # Assuntos por PLO (2026)
    linhas_ass = []
    for _, row in df_plo_parl[df_plo_parl['tem_assunto']].iterrows():
        for assunto in row['assuntos']:
            linhas_ass.append({
                'autor_nome': row['autor_nome'],
                'assunto':    assunto,
                'materia_id': row['materia_id'],
            })
    df_ass = (
        pd.DataFrame(linhas_ass).drop_duplicates(['autor_nome', 'materia_id', 'assunto'])
        if linhas_ass else pd.DataFrame(columns=['autor_nome', 'assunto', 'materia_id'])
    )
    df_ass['virou_lei'] = df_ass['materia_id'].astype(str).isin(plos_lei_set)

    # Processa relatorias
    mapa_comissao = {str(c['id']): c.get('nome', f"Comissão {c['id']}") for c in comissoes_raw}
    mapa_materia  = {str(m['id']): m for m in materias_hist}
    linhas_rel = []
    for r in relatorias_raw:
        mid  = str(r.get('materia', ''))
        mat  = mapa_materia.get(mid, {})
        linhas_rel.append({
            'rel_id':         r['id'],
            'parlamentar':    r.get('parlamentar'),
            'materia_id':     r.get('materia'),
            'comissao_id':    r.get('comissao'),
            'comissao':       mapa_comissao.get(str(r.get('comissao', '')), '—'),
            'tipo_sigla':     mat.get('tipo__sigla', ''),
            'tipo_descricao': mat.get('tipo__descricao', ''),
            'numero':       mat.get('numero', ''),
            'ano':          mat.get('ano', ''),
            'ementa':       mat.get('ementa', ''),
        })
    df_rel = pd.DataFrame(linhas_rel) if linhas_rel else pd.DataFrame(
        columns=['rel_id','parlamentar','materia_id','comissao_id','comissao',
                 'tipo_sigla','numero','ano','ementa'])

    # Mapa tipo_descricao → id SAPL (para links do ranking com filtro de tipo)
    mapa_tipo_sapl_id = {}
    mapa_tipo_seq = {}   # sigla → sequencia_regimental (para ordenação)
    for t in tipomaterias_raw:
        desc  = t.get('descricao') or t.get('nome') or ''
        sigla = t.get('sigla', '')
        seq   = t.get('sequencia_regimental') or 999
        tid   = t.get('id')
        if desc and tid:
            mapa_tipo_sapl_id[desc]  = tid   # descricao → id
        if sigla and tid:
            mapa_tipo_sapl_id[sigla] = tid   # sigla → id (para filtro de relatorias)
        if sigla:
            mapa_tipo_seq[sigla] = seq

    # Processa pronunciamentos (oradores)
    mapa_sessao = {str(s['id']): s for s in sessoes_raw}
    linhas_pronunc = []
    for o in oradores_raw:
        sess_id  = str(o.get('sessao_plenaria', ''))
        sess     = mapa_sessao.get(sess_id, {})
        data     = sess.get('data_inicio', '')
        str_sess = sess.get('__str__', f'Sessão {sess_id}')
        nome_sessao = ' '.join(str_sess.split()[:3]) if str_sess else f'Sessão {sess_id}'
        linhas_pronunc.append({
            'orador_id':    o['id'],
            'parlamentar':  o.get('parlamentar'),
            'sessao_id':    o.get('sessao_plenaria'),
            'numero_ordem': o.get('numero_ordem', 99),
            'data':         data,
            'ano':          str(data[:4]) if data else '',
            'sessao_nome':  nome_sessao,
            'url_video':    sess.get('url_video', '') or '',
            'url_discurso': o.get('url_discurso', '') or '',
            'observacao':   o.get('observacao', '') or '',
        })

    # Combina com pronunciamentos_extras (ex: considerações finais da Presidência)
    for e in pronunc_extras_raw:
        sess_id  = str(e.get('sessao_plenaria', ''))
        sess     = mapa_sessao.get(sess_id, {})
        data     = e.get('data') or sess.get('data_inicio', '')
        linhas_pronunc.append({
            'orador_id':    f"extra_{sess_id}",   # ID fictício, sem conflito
            'parlamentar':  e.get('parlamentar'),
            'sessao_id':    e.get('sessao_plenaria'),
            'data':         data,
            'ano':          str(data[:4]) if data else '',
            'sessao_nome':  e.get('sessao_nome', f'Sessão {sess_id}'),
            'url_video':    sess.get('url_video', '') or '',
            'url_discurso': e.get('url_discurso', '') or '',
            'observacao':   e.get('observacao', '') or '',
        })

    df_pronunc = pd.DataFrame(linhas_pronunc) if linhas_pronunc else pd.DataFrame(
        columns=['orador_id','parlamentar','sessao_id','data','ano','sessao_nome',
                 'url_video','url_discurso','observacao'])

    return df_vereadores, df, df_parl, resumo, df_leis, df_ass, mapa_autor_id, mapa_assunto_id, df_rel, mapa_tipo_sapl_id, mapa_tipo_seq, df_pronunc


try:
    _ts = json.load(open("dados/ultima_atualizacao.json", encoding="utf-8")).get("data_hora", "")
except Exception:
    _ts = ""

df_vereadores, df_expandido, df_parl, df_resumo, df_leis, df_ass, mapa_autor_id, mapa_assunto_id, df_relatorias, mapa_tipo_sapl_id, mapa_tipo_seq, df_pronunciamentos = carregar_dados(_ts)

# ID do parlamentar no SAPL → para URL /parlamentar/<id>
mapa_parlamentar_id = df_vereadores.set_index('nome_parlamentar')['id'].to_dict()

# ─── CABEÇALHO ─────────────────────────────────────────────────────────────────

st.markdown(
    # PERSONALIZAÇÃO: URL do seu app no Streamlit Cloud
    '## <a href="https://painel-legislativo-itabirito.streamlit.app/" '
    'target="_blank" style="text-decoration:none;color:inherit" '
    'title="Abrir versão completa no Streamlit">'
    # PERSONALIZAÇÃO: nome da sua Casa no título do painel
    '🏛️ Painel Legislativo — Câmara Municipal de Itabirito ↗</a>',
    unsafe_allow_html=True
)
st.caption("Dados: SAPL · Câmara Municipal de Itabirito (MG) · 2026")

# ─── FILTROS (barra horizontal no topo) ────────────────────────────────────────

f1, f2, f3, f4 = st.columns([1.6, 1.4, 1.4, 1])

assunto_selecionado = "Todos"
tipo_opcoes = ["Todos"] + sorted([
    t for t in df_parl['tipo_descricao'].unique()
    if t not in ['Projeto de Lei Substitutivo', 'Projeto de Lei Substitutivo (2)']
])

# Tipo precisa ser lido antes do assunto (mas exibido depois) — calcula primeiro
with f3:
    tipo_selecionado = st.selectbox("📁 Tipo de matéria", tipo_opcoes)

with f1:
    if tipo_selecionado in ["Todos", "Projeto de Lei Ordinária"]:
        assuntos_lista = ["Todos"] + sorted(df_ass['assunto'].unique().tolist())
        total_plos     = df_parl[df_parl['tipo_sigla'] == 'PLO']['materia_id'].nunique()
        plos_c_assunto = df_ass['materia_id'].nunique()
        pct            = round(plos_c_assunto / total_plos * 100, 1) if total_plos > 0 else 0
        assunto_selecionado = st.selectbox(
            "🏷️ Assunto (Projetos de Lei)", assuntos_lista,
            help=f"Assuntos disponíveis para {pct}% dos PLOs cadastrados"
        )
    else:
        st.write("")

with f2:
    vereadores_lista     = ["Todos"] + sorted(df_parl['autor_nome'].unique().tolist())
    vereador_selecionado = st.selectbox("👤 Vereador", vereadores_lista)

with f4:
    tema = st.selectbox("🎨 Contraste", ["🌞 Claro", "🌙 Escuro", "🏛️ Institucional"])

# Nota informativa + data de atualização — numa única linha compacta
# _ts já lido no topo do arquivo como string "DD/MM/YYYY às HH:MM"
_atu = f"  ·  🔄 Última atualização dos dados: {_ts}" if _ts else ""
st.caption(f"ℹ️ PLS e PLS2 são substitutivos de PLOs e não contam como projetos separados{_atu}")

# ─── TEMAS ─────────────────────────────────────────────────────────────────────

if tema == "🌞 Claro":
    st.markdown("""<style>
    header[data-testid="stHeader"] { background-color: #FFFFFF !important; }
    [data-testid="stHeader"]::before { background-color: #FFFFFF !important; }
    .stApp { background-color: #FFFFFF !important; }
    .stApp, .stApp p, .stApp span, .stApp div, .stApp label { color: #1A1A1A !important; }
    h1, h2, h3 { color: #033983 !important; }
    [data-testid="stMetricValue"] { color: #033983 !important; }
    .stTabs [aria-selected="true"] { color: #033983 !important; border-bottom-color: #033983 !important; }
    .card-pop { border: 1px solid rgba(0,99,169,0.2) !important; }
    </style>""", unsafe_allow_html=True)
    plot_bg = "#FFFFFF"; plot_paper = "#FFFFFF"; plot_font = "#1A1A1A"; plot_grid = "#E5E5E5"
    plot_colorscale = 'Blues'
    aprov_bg = "#f0faf0"; aprov_color = "#2d8a2d"; card_border = "rgba(0,99,169,0.2)"

elif tema == "🌙 Escuro":
    st.markdown("""<style>
    header[data-testid="stHeader"] { background-color: #0E1117 !important; }
    [data-testid="stHeader"]::before { background-color: #0E1117 !important; }
    .stApp { background-color: #0E1117 !important; }
    .stApp, .stApp p, .stApp span, .stApp div, .stApp label { color: #FAFAFA !important; }
    h1, h2, h3 { color: #5B9BD5 !important; }
    [data-testid="stMetricValue"] { color: #5B9BD5 !important; }
    .stTabs [aria-selected="true"] { color: #5B9BD5 !important; border-bottom-color: #5B9BD5 !important; }
    .stSelectbox > div > div { background-color: #1A1F2E !important; color: #FAFAFA !important; }
    [data-testid="stDataFrame"] iframe { filter: invert(0.85) hue-rotate(180deg); }
    .card-pop { border: 1px solid rgba(255,255,255,0.25) !important; }
    /* Botão de link — tema escuro */
    [data-testid="stLinkButton"] a {
        background-color: #1A1F2E !important;
        color: #FAFAFA !important;
        border: 1px solid rgba(255,255,255,0.35) !important;
    }
    [data-testid="stLinkButton"] a:hover {
        background-color: #2D3748 !important;
        color: #FFFFFF !important;
    }
    </style>""", unsafe_allow_html=True)
    plot_bg = "#0E1117"; plot_paper = "#0E1117"; plot_font = "#FAFAFA"; plot_grid = "#2D3748"
    plot_colorscale = 'Blues'
    aprov_bg = "rgba(112,173,71,0.25)"; aprov_color = "#90d470"; card_border = "rgba(255,255,255,0.25)"

elif tema == "🏛️ Institucional":
    st.markdown("""<style>
    header[data-testid="stHeader"] { background-color: #033983 !important; }
    [data-testid="stHeader"]::before { background-color: #033983 !important; }
    .stApp { background-color: #033983 !important; }
    .stApp, .stApp p, .stApp span, .stApp div, .stApp label { color: #FFFFFF !important; }
    h1 { color: #FFCD00 !important; } h2, h3 { color: #FFCD00 !important; }
    [data-testid="stMetricLabel"] { color: rgba(255,255,255,0.85) !important; }
    [data-testid="stMetricValue"] { color: #FFCD00 !important; }
    .stTabs [data-baseweb="tab"] { color: rgba(255,255,255,0.7) !important; }
    .stTabs [aria-selected="true"] { color: #FFCD00 !important; border-bottom-color: #FFCD00 !important; }
    .stSelectbox > div > div { background-color: #022B6B !important; color: #FFFFFF !important; border-color: rgba(255,255,255,0.3) !important; }
    hr { border-color: rgba(255,255,255,0.2) !important; }
    .stAlert { background-color: #022B6B !important; color: #FFFFFF !important; }
    .stCaption { color: rgba(255,255,255,0.65) !important; }
    [data-testid="stDataFrame"] iframe { filter: invert(0.85) hue-rotate(200deg) saturate(1.5); }
    .card-pop { border: 1px solid rgba(255,205,0,0.5) !important; }
    /* Botão de link — tema institucional */
    [data-testid="stLinkButton"] a {
        background-color: #033983 !important;
        color: #FFFFFF !important;
        border: 1px solid #FFCD00 !important;
    }
    [data-testid="stLinkButton"] a:hover {
        background-color: #022B6B !important;
        color: #FFCD00 !important;
    }
    </style>""", unsafe_allow_html=True)
    plot_bg = "#033983"; plot_paper = "#033983"; plot_font = "#FFFFFF"; plot_grid = "rgba(255,255,255,0.2)"
    plot_colorscale = [[0, 'rgba(255,255,255,0.35)'], [1, '#FFCD00']] #grade amarela.
    #plot_colorscale = 'Greys'
    aprov_bg = "rgba(255,205,0,0.2)"; aprov_color = "#FFCD00"; card_border = "rgba(255,205,0,0.5)"

st.markdown("""<style>
/* Remove toolbar, rodapé, header e espaços extras do Streamlit */
footer { display: none !important; }
#MainMenu { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }
header[data-testid="stHeader"] { display: none !important; height: 0 !important; }
.stApp > header { display: none !important; }

/* Força o app a caber em qualquer largura de iframe */
.stApp {
    min-width: 0 !important;
    overflow-x: hidden !important;
}
.block-container {
    min-width: 0 !important;
    width: 100% !important;
    padding-top: 0.5rem !important;
    padding-bottom: 0.5rem !important;
    padding-left: 1rem !important;
    padding-right: 2rem !important;
    max-width: 100% !important;
}
[data-testid="stAppViewBlockContainer"] {
    padding-bottom: 0 !important;
    min-width: 0 !important;
}

/* Reduz o gap vertical padrão entre elementos — cabeçalho muito mais compacto */
[data-testid="stVerticalBlock"] { gap: 0.4rem !important; }

/* Divisor mais fino e compacto */
hr { margin: 0.2rem 0 !important; }

/* Colunas responsivas — quebram linha em vez de criar scroll */
[data-testid="stHorizontalBlock"] {
    flex-wrap: wrap !important;
    gap: 0.5rem !important;
    min-width: 0 !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="column"] {
    min-width: 120px !important;
    flex: 1 1 120px !important;
}

/* h2/h3 menores em telas estreitas */
@media (max-width: 900px) {
    h2 { font-size: 1.1rem !important; }
    [data-testid="stMetricValue"] { font-size: 1.4rem !important; }
    [data-testid="stHorizontalBlock"] > [data-testid="column"] {
        min-width: 90px !important;
        flex: 1 1 90px !important;
    }
}
</style>""", unsafe_allow_html=True)

st.markdown(f"""<style>
.card-pop {{ border-radius:16px;padding:20px 16px;text-align:center;margin-bottom:14px;
             min-height:260px;display:flex;flex-direction:column;justify-content:space-between; }}
.card-secondary {{ background:rgba(128,128,128,0.15);border-radius:8px;padding:6px;font-size:11px; }}
.card-nome {{ font-size:14px;font-weight:600;color:var(--text-color);margin-bottom:6px;
              min-height:44px;display:flex;align-items:center;justify-content:center; }}
.card-muted {{ font-size:10px;color:var(--text-color);opacity:0.55;margin-top:3px; }}
.pill-ass {{ background:rgba(91,155,213,0.2);color:var(--text-color);border-radius:20px;
             padding:5px 14px;font-size:13px;font-weight:500;margin:3px;display:inline-block; }}
</style>""", unsafe_allow_html=True)

def aplicar_tema_plot(fig):
    fig.update_layout(
        plot_bgcolor=plot_bg, paper_bgcolor=plot_paper, font_color=plot_font,
        xaxis=dict(gridcolor=plot_grid, color=plot_font, zerolinecolor=plot_grid, fixedrange=True),
        yaxis=dict(gridcolor=plot_grid, color=plot_font, zerolinecolor=plot_grid, fixedrange=True),
        dragmode=False,   # impede pan/zoom por arraste — toque passa para o scroll da página
        legend=dict(bgcolor=plot_paper, font=dict(color=plot_font),
                    bordercolor=plot_grid, borderwidth=1),
        modebar=dict(
            remove=[
                "zoom", "pan", "select", "lasso2d",
                "zoomIn2d", "zoomOut2d", "autoScale2d", "resetAxes",
                "select2d", "lasso2d", "drawclosedpath",
                "drawopenpath", "drawline", "drawrect",
                "drawcircle", "eraseshape",
                "hoverClosestCartesian", "hoverCompareCartesian",
                "toggleSpikelines",
            ],
            add=["toImage"],   # só mantém o botão de salvar imagem
            orientation="v",
        ),
    )
    return fig

PLOT_CONFIG = {
    "modeBarButtonsToRemove": [
        "zoom2d", "pan2d", "select2d", "lasso2d",
        "zoomIn2d", "zoomOut2d", "resetAxes", "autoScale2d",
        "hoverClosestCartesian", "hoverCompareCartesian", "toggleSpikelines",
    ],
    "modeBarButtonsToAdd": [],
    "displayModeBar": "hover",   # desktop: aparece ao passar o mouse | mobile: nunca aparece
    "displaylogo": False,
    "responsive": True,
}

# ─── FILTRAR ───────────────────────────────────────────────────────────────────

df_sem_pls  = df_parl[~df_parl['tipo_sigla'].isin(['PLS', 'PLS2'])].copy()
df_filtrado = df_sem_pls.copy()
if tipo_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['tipo_descricao'] == tipo_selecionado]
if vereador_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['autor_nome'] == vereador_selecionado]
if assunto_selecionado != "Todos":
    ids_com_assunto = set(df_ass[df_ass['assunto'] == assunto_selecionado]['materia_id'])
    df_filtrado = df_filtrado[df_filtrado['materia_id'].isin(ids_com_assunto)]

# ─── CARDS GERAIS ──────────────────────────────────────────────────────────────

# Contagens únicas (sem inflar por co-autorias)
total_plos_unicos    = df_parl[df_parl['tipo_sigla'] == 'PLO']['materia_id'].nunique()
nomes_ativos_set     = set(df_vereadores['nome_parlamentar'])
total_aprov_unicos   = df_leis[df_leis['autor_nome'].isin(nomes_ativos_set)]['plo_id'].nunique()
taxa_geral           = round(total_aprov_unicos / total_plos_unicos * 100, 1) if total_plos_unicos else 0

# Totais para cálculo dos extras
total_plos_todos  = df_expandido[df_expandido['tipo_sigla'] == 'PLO']['materia_id'].nunique()
total_aprov_todos = df_leis['plo_id'].nunique()
total_mat_todos   = df_expandido[~df_expandido['tipo_sigla'].isin(['PLS', 'PLS2'])]['materia_id'].nunique()
extra_plos  = total_plos_todos - total_plos_unicos
extra_aprov = total_aprov_todos - total_aprov_unicos
extra_mat   = total_mat_todos - df_sem_pls['materia_id'].nunique()

# Sets de IDs com vereador ativo — evita dupla contagem nos breakdowns
_ids_mat_ver = set(df_parl[~df_parl['tipo_sigla'].isin(['PLS', 'PLS2'])]['materia_id'])
_ids_plo_ver = set(df_parl[df_parl['tipo_sigla'] == 'PLO']['materia_id'])

# Breakdown por origem — Matérias (card 2)
_df = df_expandido[
    (~df_expandido['tipo_sigla'].isin(['PLS', 'PLS2'])) &
    (~df_expandido['materia_id'].isin(_ids_mat_ver))
]
c2_exec   = _df[_df['autor_tipo'] == 'Chefe do Executivo']['materia_id'].nunique()
c2_mesa   = _df[_df['autor_nome'].str.contains('Mesa Diretora', na=False)]['materia_id'].nunique()
c2_outros = max(0, int(extra_mat) - c2_exec - c2_mesa)

# Breakdown por origem — PLOs (card 3)
_df = df_expandido[
    (df_expandido['tipo_sigla'] == 'PLO') &
    (~df_expandido['materia_id'].isin(_ids_plo_ver))
]
c3_exec   = _df[_df['autor_tipo'] == 'Chefe do Executivo']['materia_id'].nunique()
c3_mesa   = _df[_df['autor_nome'].str.contains('Mesa Diretora', na=False)]['materia_id'].nunique()
c3_outros = max(0, int(extra_plos) - c3_exec - c3_mesa)

# Breakdown por origem — PLOs aprovados (card 4)
# Usa autor_nome de df_leis cruzado com autor_tipo de df_expandido
_mapa_nome_tipo = (
    df_expandido.drop_duplicates('autor_nome')
    .set_index('autor_nome')['autor_tipo'].to_dict()
)
_df_leis_nao_v = (
    df_leis[~df_leis['autor_nome'].isin(nomes_ativos_set)]
    .drop_duplicates('plo_id').copy()
)
_df_leis_nao_v['at'] = _df_leis_nao_v['autor_nome'].map(_mapa_nome_tipo).fillna('')
c4_exec   = int((_df_leis_nao_v['at'] == 'Chefe do Executivo').sum())
c4_mesa   = int(_df_leis_nao_v['autor_nome'].str.contains('Mesa Diretora', na=False).sum())
c4_outros = max(0, int(extra_aprov) - c4_exec - c4_mesa)

def _rod_orig(c_exec, c_mesa, c_outros):
    """Renderiza '+N Origem' num único st.caption com quebras compactas."""
    linhas = []
    if c_exec   > 0: linhas.append(f"+{c_exec} Executivo")
    if c_mesa   > 0: linhas.append(f"+{c_mesa} Mesa")
    if c_outros > 0: linhas.append(f"+{c_outros} Outros")
    if linhas:
        st.caption("  \n".join(linhas))  # dois espaços + \n = <br> em markdown

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("Vereadores ativos", len(df_vereadores))
with c2:
    st.metric("Matérias apresentadas", df_sem_pls['materia_id'].nunique())
    _rod_orig(c2_exec, c2_mesa, c2_outros)
with c3:
    st.metric("Projetos de Lei", total_plos_unicos)
    _rod_orig(c3_exec, c3_mesa, c3_outros)
with c4:
    st.metric("PLOs aprovados", total_aprov_unicos)
    _rod_orig(c4_exec, c4_mesa, c4_outros)
with c5:
    st.metric("Taxa geral de aprovação", f"{taxa_geral}%")
    st.caption("dos vereadores ativos")


# ─── NOTA DE TRANSPARÊNCIA (em expander para não ocupar espaço por padrão) ─────

qtd_executivo = df_expandido[df_expandido['autor_tipo'] == 'Chefe do Executivo']['materia_id'].nunique()
qtd_mesa_dir  = df_expandido[df_expandido['autor_nome'].str.contains('Mesa Diretora', na=False)]['materia_id'].nunique()
qtd_externos  = df_expandido[df_expandido['autor_tipo'] == 'Externo']['materia_id'].nunique()
qtd_pls_pls2  = df_expandido[
    df_expandido['e_vereador_ativo'] & df_expandido['tipo_sigla'].isin(['PLS', 'PLS2'])
]['materia_id'].nunique()

partes = []
if qtd_executivo > 0:
    partes.append(f"**{qtd_executivo} matérias** pelo Poder Executivo (Élio da Mata)")
if qtd_mesa_dir > 0:
    partes.append(f"**{qtd_mesa_dir} matérias** pela Mesa Diretora")
if qtd_externos > 0:
    partes.append(f"**{qtd_externos} matéria{"s" if qtd_externos > 1 else ""}** por autores externos")
if qtd_pls_pls2 > 0:
    partes.append(f"**{qtd_pls_pls2} substitutivos** de PLOs (PLS/PLS2), contados junto ao projeto original")
if partes:
    qtd_leis_nao_vereadores = df_leis[
        ~df_leis['autor_nome'].isin(nomes_ativos_set)
    ]['plo_id'].nunique()
    nota_leis = ""
    if qtd_leis_nao_vereadores > 0:
        nota_leis = (
            f" Além disso, **{qtd_leis_nao_vereadores}**"
            f" lei{'s foram aprovadas' if qtd_leis_nao_vereadores > 1 else ' foi aprovada'}"
            f" a partir de projetos do Executivo e da Mesa Diretora"
            f" — não contabilizadas nos {total_aprov_unicos} PLOs aprovados acima."
        )
    with st.expander("ℹ️ Sobre os dados exibidos"):
        st.caption(
            "Em 2026 também foram apresentados: " +
            ", ".join(partes) +
            " — não incluídos nos comparativos entre vereadores." +
            nota_leis
        )

# ─── HELPERS ───────────────────────────────────────────────────────────────────

@st.cache_data
def carregar_fotos():
    """Carrega fotos locais como base64 (sem depender de URL do servidor).
    Fallback para URL do SAPL se o arquivo local não existir."""
    import base64
    fotos = {}
    for _, row in df_vereadores.iterrows():
        vid  = row['id']
        nome = row['nome_parlamentar']
        caminho = f"static/fotos/{vid}.jpg"
        if os.path.exists(caminho):
            try:
                with open(caminho, "rb") as f:
                    data = base64.b64encode(f.read()).decode()
                fotos[nome] = f"data:image/jpeg;base64,{data}"
            except Exception:
                fotos[nome] = row.get('fotografia', '') or ''
        else:
            fotos[nome] = row.get('fotografia', '') or ''
    return fotos

mapa_foto = carregar_fotos()
mapa_cargo = df_vereadores.set_index('nome_parlamentar')['cargo_mesa'].fillna('').to_dict()

# ╔══════════════════════════════════════════════════════════════════╗
# ║  PERSONALIZAÇÃO — URLs e IDs de tipos de matéria                ║
# ╚══════════════════════════════════════════════════════════════════╝

# URL do SAPL da sua Casa
BASE_SAPL_URL = "https://sapl.itabirito.mg.leg.br"

# ID do tipo "Projeto de Lei Ordinária" no SAPL.
# Verifique em <BASE_SAPL_URL>/api/materia/tipomateria/?format=json
# No SAPL de Itabirito, PLO = ID 1. Pode ser diferente em outras Casas.
TIPO_MATERIA_SAPL = {'PLO': 1}

# PERSONALIZAÇÃO: o padrão ano=2026 nas URLs de pesquisa.
# Se adaptar para múltiplos anos, o ano virá do contexto de cada chamada.
def url_sapl(ano=2026, autor_id=None, assunto_id=None, so_parlamentar=False, tipo_materia_id=None):
    """Monta URL curta de pesquisa no SAPL com apenas os filtros necessários."""
    params = {"salvar": "Pesquisar", "ano": ano}
    if autor_id:
        params["autoria__autor"] = autor_id
    if tipo_materia_id:
        params["tipo"] = tipo_materia_id
    if assunto_id:
        params["materiaassunto__assunto"] = assunto_id
    if so_parlamentar:
        params["autoria__autor__tipo"] = 1
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{BASE_SAPL_URL}/materia/pesquisar-materia?{query}"

def foto_html(nome, foto_url, size=80):
    if foto_url:
        return (
            f'<img src="{foto_url}" style="width:{size}px;height:{size}px;border-radius:50%;'
            f'object-fit:cover;border:3px solid rgba(128,128,128,0.3);display:block;margin:0 auto">'
        )
    iniciais = ''.join(p[0].upper() for p in nome.split()[:2])
    cores = ['#5b9bd5', '#70ad47', '#ed7d31', '#a855f7', '#ec4899', '#14b8a6']
    cor = cores[hash(nome) % len(cores)]
    return (
        f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:{cor};'
        f'display:flex;align-items:center;justify-content:center;font-size:{size//3}px;'
        f'font-weight:700;color:white;border:3px solid rgba(128,128,128,0.3);margin:0 auto">{iniciais}</div>'
    )

# ─── VISÃO GERAL ───────────────────────────────────────────────────────────────

if vereador_selecionado == "Todos":

    aba1, aba2, aba3, aba_pop, aba_pron_geral = st.tabs([
        "📊 Ranking por matérias", "⚖️ Aprovação de PLOs",
        "🏷️ Projetos por assunto", "📱 Em Destaque", "📢 Pronunciamentos",
    ])

    with aba1:
        df_ranking = (
            df_filtrado.groupby('autor_nome').size()
            .reset_index(name='total').sort_values('total', ascending=True)
        )
        fig = px.bar(df_ranking, x='total', y='autor_nome', orientation='h',
                     labels={'total': 'Total de matérias', 'autor_nome': ''},
                     color='total', color_continuous_scale=plot_colorscale, text='total',
                     custom_data=['autor_nome'])
        fig.update_traces(textposition='outside')
        fig.update_layout(coloraxis_showscale=False, height=500, margin=dict(l=10, r=40, t=10, b=10))
        fig = aplicar_tema_plot(fig)
        evento1 = st.plotly_chart(fig, width='stretch', on_select="rerun", key="chart_ranking", config=PLOT_CONFIG)
        pontos = evento1.get("selection", {}).get("points", []) if evento1 else []
        if pontos:
            ponto1    = pontos[0]
            cd1       = ponto1.get("customdata") or []
            nome_sel  = cd1[0] if cd1 else ponto1.get("y")
            autor_id  = mapa_autor_id.get(nome_sel)
            assunto_id_sel = mapa_assunto_id.get(assunto_selecionado) if assunto_selecionado != "Todos" else None
            tipo_id_sel = mapa_tipo_sapl_id.get(tipo_selecionado) if tipo_selecionado != "Todos" else None
            if autor_id:
                st.link_button(
                    f"🔗 Ver matérias de {nome_sel} em 2026 no SAPL",
                    url_sapl(ano=2026, autor_id=autor_id, assunto_id=assunto_id_sel,
                             tipo_materia_id=tipo_id_sel)
                )
        else:
            st.caption("💡 Clique em uma barra para abrir as matérias do vereador no SAPL.")

    with aba2:
        df_aprov = df_resumo[df_resumo['projetos_lei'] > 0].sort_values('taxa_aprovacao', ascending=True)
        fig2 = px.bar(df_aprov, x='taxa_aprovacao', y='autor_nome', orientation='h',
                      labels={'taxa_aprovacao': 'Taxa de aprovação (%)', 'autor_nome': ''},
                      color='taxa_aprovacao', color_continuous_scale='Greens', text='taxa_aprovacao',
                      custom_data=['autor_nome'])
        fig2.update_traces(texttemplate='%{text}%', textposition='outside')
        fig2.update_layout(coloraxis_showscale=False, height=500, margin=dict(l=10, r=40, t=10, b=10))
        fig2 = aplicar_tema_plot(fig2)
        evento2 = st.plotly_chart(fig2, width='stretch', on_select="rerun", key="chart_aprovacao", config=PLOT_CONFIG)
        pontos2 = evento2.get("selection", {}).get("points", []) if evento2 else []
        if pontos2:
            ponto2   = pontos2[0]
            # customdata é mais confiável que y em gráficos com colorscale
            cd2      = ponto2.get("customdata") or []
            nome_sel2 = cd2[0] if cd2 else ponto2.get("y")
            autor_id2 = mapa_autor_id.get(nome_sel2)
            if autor_id2:
                st.link_button(
                    f"🔗 Ver Projetos de Lei de {nome_sel2} em 2026 no SAPL",
                    url_sapl(ano=2026, autor_id=autor_id2, so_parlamentar=True,
                             tipo_materia_id=TIPO_MATERIA_SAPL['PLO'])
                )
        else:
            st.caption("💡 Clique em uma barra para abrir os Projetos de Lei do vereador no SAPL.")
        st.dataframe(
            df_aprov[['autor_nome', 'projetos_lei', 'projetos_virou_lei',
                      'taxa_aprovacao', 'projetos_com_substitutivo']]
            .rename(columns={'autor_nome': 'Vereador', 'projetos_lei': 'PLOs',
                             'projetos_virou_lei': 'Aprovados', 'taxa_aprovacao': 'Taxa (%)',
                             'projetos_com_substitutivo': 'Com substitutivo'})
            .sort_values('Taxa (%)', ascending=False),
            width='stretch', hide_index=True,
            height=len(df_aprov) * 35 + 45,  # mostra todas as linhas sem scroll interno
        )

    with aba3:
        if df_ass.empty:
            st.info("Nenhum assunto cadastrado nos dados carregados.")
        else:
            top_assuntos = (
                df_ass.groupby('assunto')['materia_id'].nunique()
                .sort_values(ascending=False).head(15).index.tolist()
            )
            df_ass_top = df_ass[df_ass['assunto'].isin(top_assuntos)]
            df_comp = (
                df_ass_top.groupby('assunto')
                .agg(
                    apresentados=('materia_id', 'nunique'),
                    aprovados=('virou_lei', lambda x: df_ass_top.loc[x.index]
                               .drop_duplicates('materia_id')['virou_lei'].sum()),
                )
                .reset_index().sort_values('apresentados', ascending=False)
            )
            df_comp_long = df_comp.melt(
                id_vars='assunto', value_vars=['apresentados', 'aprovados'],
                var_name='situação', value_name='projetos'
            )
            fig_comp = px.bar(
                df_comp_long, x='assunto', y='projetos', color='situação', barmode='group',
                labels={'assunto': '', 'projetos': 'Projetos de Lei', 'situação': ''},
                color_discrete_map={'apresentados': '#5b9bd5', 'aprovados': '#70ad47'},
                title="Projetos de Lei por assunto — apresentados vs aprovados"
            )
            fig_comp.update_layout(height=480, xaxis_tickangle=-40,
                                   margin=dict(l=10, r=10, t=40, b=140),
                                   legend=dict(orientation='h', y=1.05))
            fig_comp = aplicar_tema_plot(fig_comp)
            evento_ass = st.plotly_chart(fig_comp, width='stretch', on_select="rerun", key="chart_assunto", config=PLOT_CONFIG)
            pontos_ass = evento_ass.get("selection", {}).get("points", []) if evento_ass else []
            autor_id_fil = mapa_autor_id.get(vereador_selecionado) if vereador_selecionado != "Todos" else None
            if pontos_ass:
                assunto_clicado = pontos_ass[0].get("x")
                assunto_id_clicado = mapa_assunto_id.get(assunto_clicado)
                if assunto_id_clicado:
                    label = f"🔗 Ver PLOs sobre '{assunto_clicado}' em 2026 no SAPL"
                    if autor_id_fil:
                        label += f" ({vereador_selecionado})"
                    st.link_button(label, url_sapl(ano=2026, autor_id=autor_id_fil,
                                                   assunto_id=assunto_id_clicado,
                                                   so_parlamentar=True))
            else:
                st.caption("💡 Clique em uma barra para abrir os PLOs do assunto no SAPL.")
            df_comp['taxa'] = (df_comp['aprovados'] / df_comp['apresentados'] * 100).round(1)
            df_comp.columns = ['Assunto', 'Apresentados', 'Aprovados', 'Taxa (%)']
            st.dataframe(df_comp.sort_values('Taxa (%)', ascending=False),
                         width='stretch', hide_index=True)
            st.divider()
            st.markdown("**Comparativo entre vereadores por assunto**")
            df_heat = (
                df_ass_top.groupby(['autor_nome', 'assunto'])
                ['materia_id'].nunique().reset_index(name='qtd')
            )
            # Tabela pivot para go.Heatmap (suporta on_select corretamente)
            import plotly.graph_objects as go
            df_pivot   = df_heat.pivot_table(values='qtd', index='autor_nome', columns='assunto', fill_value=0)
            autores_px = df_pivot.index.tolist()
            assuntos_px = df_pivot.columns.tolist()
            # customdata: matriz com (autor, assunto) por célula
            custom = [[[a, s] for s in assuntos_px] for a in autores_px]
            fig_heat = go.Figure(data=go.Heatmap(
                z=df_pivot.values.tolist(),
                x=assuntos_px,
                y=autores_px,
                colorscale=plot_colorscale if isinstance(plot_colorscale, list) else 'Blues',
                customdata=custom,
                hovertemplate='<b>%{y}</b><br>%{x}: %{z} PLO(s)<extra></extra>',
            ))
            fig_heat.update_layout(height=500, xaxis_tickangle=-40,
                                   margin=dict(l=10, r=10, t=20, b=140))
            fig_heat = aplicar_tema_plot(fig_heat)
            st.plotly_chart(fig_heat, width='stretch', key="chart_heat", config=PLOT_CONFIG)

    with aba_pop:
        if assunto_selecionado == "Todos":
            st.markdown("### Vereadores de Itabirito — 2026")
            df_grid_list = list(df_resumo.sort_values('taxa_aprovacao', ascending=False).iterrows())
            for row_start in range(0, len(df_grid_list), 3):
                cols = st.columns(3)
                for j, (_, row) in enumerate(df_grid_list[row_start:row_start + 3]):
                    nome       = row['autor_nome']
                    foto       = mapa_foto.get(nome, '')
                    cargo_mesa = mapa_cargo.get(nome, '')
                    cargo_badge = (
                        f'<div style="font-size:10px;font-weight:600;color:#ed7d31;'
                        f'margin-bottom:8px;letter-spacing:0.5px">⭐ {cargo_mesa}</div>'
                    ) if cargo_mesa else '<div style="height:22px"></div>'

                    # URL da foto: pesquisa filtrada (com assunto) ou página do parlamentar
                    parl_id    = mapa_parlamentar_id.get(nome)
                    autor_id_c = mapa_autor_id.get(nome)
                    assunto_id_c = mapa_assunto_id.get(assunto_selecionado) if assunto_selecionado != "Todos" else None
                    if assunto_id_c and autor_id_c:
                        foto_href = url_sapl(ano=2026, autor_id=autor_id_c, assunto_id=assunto_id_c, so_parlamentar=True)
                        foto_title = f"Ver PLOs sobre {assunto_selecionado} no SAPL"
                    elif parl_id:
                        foto_href  = f"https://sapl.itabirito.mg.leg.br/parlamentar/{parl_id}"
                        foto_title = "Ver parlamentar no SAPL"
                    else:
                        foto_href  = None
                        foto_title = ""
                    foto_tag = (
                        f'<a href="{foto_href}" target="_blank" style="display:block;cursor:pointer" title="{foto_title}">'
                        f'{foto_html(nome, foto, 80)}</a>'
                    ) if foto_href else foto_html(nome, foto, 80)

                    with cols[j]:
                        st.markdown(
                            f'<div class="card-pop" style="border:1px solid {card_border}">'
                            f'<div style="margin-bottom:12px">{foto_tag}</div>'
                            f'<div class="card-nome">{nome}</div>{cargo_badge}'
                            f'<div style="display:flex;justify-content:space-around;margin-bottom:12px">'
                            f'<div><div style="font-size:26px;font-weight:700;color:#5b9bd5;line-height:1">{int(row["projetos_lei"])}</div>'
                            f'<div class="card-muted">Projetos</div></div>'
                            f'<div><div style="font-size:26px;font-weight:700;color:#70ad47;line-height:1">{int(row["projetos_virou_lei"])}</div>'
                            f'<div class="card-muted">Aprovados</div></div>'
                            f'<div><div style="font-size:26px;font-weight:700;color:#ed7d31;line-height:1">{row["taxa_aprovacao"]}%</div>'
                            f'<div class="card-muted">Taxa</div></div></div>'
                            f'<div class="card-secondary">{int(row["total_geral"])} matérias apresentadas</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
        else:
            st.markdown(f"### 🏷️ {assunto_selecionado}")
            st.markdown("**Vereadores com mais projetos neste tema:**")
            top3 = (
                df_ass[df_ass['assunto'] == assunto_selecionado]
                .groupby('autor_nome')['materia_id'].nunique()
                .sort_values(ascending=False).head(3)
            )
            cols     = st.columns(len(top3))
            bordas   = ['#ffd700', '#adb5bd', '#cd7f32']
            medalhas = ['🥇', '🥈', '🥉']
            for i, (nome, qtd) in enumerate(top3.items()):
                foto       = mapa_foto.get(nome, '')
                autor_id_p = mapa_autor_id.get(nome)
                assunto_id_p = mapa_assunto_id.get(assunto_selecionado)
                aprov = df_ass[
                    (df_ass['autor_nome'] == nome) &
                    (df_ass['assunto']    == assunto_selecionado) &
                    (df_ass['virou_lei'])
                ]['materia_id'].nunique()
                # Foto clicável → pesquisa autor + assunto no SAPL
                if autor_id_p and assunto_id_p:
                    foto_link_p = url_sapl(ano=2026, autor_id=autor_id_p, assunto_id=assunto_id_p, so_parlamentar=True)
                    foto_tag_p  = (
                        f'<a href="{foto_link_p}" target="_blank" style="display:block;cursor:pointer" '
                        f'title="Ver PLOs sobre {assunto_selecionado} no SAPL">'
                        f'{foto_html(nome, foto, 100)}</a>'
                    )
                else:
                    foto_tag_p = foto_html(nome, foto, 100)
                with cols[i]:
                    st.markdown(
                        f'<div style="background:{plot_paper};border-radius:16px;'
                        f'border:2px solid {bordas[i]};padding:28px 16px;text-align:center">'
                        f'<div style="font-size:32px;margin-bottom:10px">{medalhas[i]}</div>'
                        f'<div style="margin-bottom:14px">{foto_tag_p}</div>'
                        f'<div style="font-size:15px;font-weight:600;color:{plot_font};margin-bottom:18px">{nome}</div>'
                        f'<div style="font-size:42px;font-weight:700;color:#5b9bd5;line-height:1">{qtd}</div>'
                        f'<div style="font-size:12px;color:{plot_font};opacity:0.7;margin-bottom:14px">'
                        f'projeto{"s" if qtd > 1 else ""} sobre {assunto_selecionado}</div>'
                        f'<div style="background:{aprov_bg};border-radius:8px;padding:8px;'
                        f'font-size:13px;font-weight:600;color:{aprov_color}">'
                        f'✅ {aprov} aprovado{"s" if aprov != 1 else ""}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

    # ─── ABA PRONUNCIAMENTOS (visão geral) ────────────────────────────────────
    with aba_pron_geral:
        st.markdown("##### Selecione uma sessão para ver quais vereadores fizeram uso da palavra livre")

        if df_pronunciamentos.empty:
            st.info("📢 Os dados de pronunciamentos ainda não foram coletados. "
                    "Execute o workflow 'Coletar dados pontuais' para incluí-los.")
        else:
            mapa_id_parl = df_vereadores.set_index('id')['nome_parlamentar'].to_dict()

            # Apenas oradores reais (não extras) de 2026
            df_pron_2026 = df_pronunciamentos[
                (df_pronunciamentos['ano'] == '2026') &
                (df_pronunciamentos['orador_id'].apply(lambda x: str(x).isdigit()))
            ].copy()

            # Tabela de sessões com contagem de oradores
            sessoes_resumo = (
                df_pron_2026.groupby(['sessao_id','data','sessao_nome'])
                .size().reset_index(name='Oradores')
                .sort_values('data', ascending=False)
            )
            sessoes_resumo['Data'] = pd.to_datetime(
                sessoes_resumo['data']).dt.strftime('%d/%m/%Y')
            sessoes_resumo['Sessão'] = sessoes_resumo['sessao_nome']

            # ── CORREÇÃO: reordenar colunas para Oradores ficar no centro ──
            df_tabela = sessoes_resumo[['Data','Oradores','Sessão']].reset_index(drop=True)

            st.caption("Clique em uma sessão para ver os oradores.")
            evento = st.dataframe(
                df_tabela,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                height=280,  # ~7 sessões visíveis — permite scroll de página até os oradores
                column_config={
                    'Data':     st.column_config.TextColumn(width='small'),
                    'Oradores': st.column_config.NumberColumn(format='%d', width='small'),
                    'Sessão':   st.column_config.TextColumn(width='large'),
                }
            )

            linhas_sel = evento.selection.rows if evento.selection else []
            if linhas_sel:
                idx        = linhas_sel[0]
                sessao_row = sessoes_resumo.iloc[idx]
                sessao_id  = sessao_row['sessao_id']
                url_video_sess = df_pron_2026[
                    df_pron_2026['sessao_id'] == sessao_id]['url_video'].iloc[0]
                url_sapl_sess = f"{BASE_SAPL_URL}/sessao/{int(sessao_id)}"

                st.markdown(f"**{sessao_row['Data']} — {sessao_row['Sessão']}**")

                # Oradores regulares ordenados por numero_ordem
                df_sess = df_pron_2026[
                    df_pron_2026['sessao_id'] == sessao_id
                ].sort_values('numero_ordem')

                # Extras (ex: Presidente) para esta sessão — sempre por último
                df_extras_sess = df_pronunciamentos[
                    (df_pronunciamentos['sessao_id'] == sessao_id) &
                    (~df_pronunciamentos['orador_id'].apply(lambda x: str(x).isdigit()))
                ]

                def cel_orador_geral(row, label):
                    nome = mapa_id_parl.get(row['parlamentar'],
                                            f"Parlamentar {row['parlamentar']}")
                    obs  = row.get('observacao', '') or ''
                    url  = row.get('url_discurso', '') or ''
                    if url:
                        return (f"{label} — "
                                f'<a href="{url}" target="_blank" '
                                f'style="color:#4A90D9">{nome} 🎥</a>')
                    elif obs:
                        return f"{label} — {nome} <span style='color:#888;font-size:0.9em'>({obs})</span>"
                    return f"{label} — {nome}"

                linhas_o = ""
                for _, row in df_sess.iterrows():
                    ordem = int(row['numero_ordem'])
                    label = f"{ordem}°"
                    linhas_o += (
                        f"<tr style='border-bottom:1px solid #eee'>"
                        f"<td style='padding:6px 12px'>{cel_orador_geral(row, label)}</td>"
                        f"</tr>"
                    )
                for _, row in df_extras_sess.iterrows():
                    linhas_o += (
                        f"<tr style='border-bottom:1px solid #eee'>"
                        f"<td style='padding:6px 12px'>{cel_orador_geral(row, 'Presidente')}</td>"
                        f"</tr>"
                    )

                st.markdown(
                    f"""<table style="width:100%;border-collapse:collapse;font-size:0.95em">
                    <thead><tr style="border-bottom:2px solid #ddd">
                      <th style="text-align:left;padding:6px 12px">Orador</th>
                    </tr></thead>
                    <tbody>{linhas_o}</tbody></table>""",
                    unsafe_allow_html=True
                )
                st.markdown("")
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    st.link_button("🏛️ Ver dados desta sessão no SAPL", url_sapl_sess)
                with col_b2:
                    if url_video_sess:
                        st.link_button("▶️ Assistir à sessão na íntegra no YouTube",
                                       url_video_sess)
                    else:
                        st.caption("Vídeo não disponível para esta sessão.")


# ─── DETALHE DO VEREADOR ───────────────────────────────────────────────────────

if vereador_selecionado != "Todos":
    dados_v    = df_resumo[df_resumo['autor_nome'] == vereador_selecionado].iloc[0]
    df_detalhe = df_parl[df_parl['autor_nome'] == vereador_selecionado]
    foto       = mapa_foto.get(vereador_selecionado, '')
    cargo_v    = mapa_cargo.get(vereador_selecionado, '')

    aba_pop2, aba_d1, aba_d2, aba_d3, aba_rel, aba_pron = st.tabs([
        "📱 Em Destaque", "📂 Matérias", "✅ PLOs aprovados", "🏷️ Assuntos", "📋 Relatorias", "📢 Pronunciamentos"
    ])

    with aba_pop2:
        taxa     = float(dados_v['taxa_aprovacao'])
        taxa_cor = '#70ad47' if taxa >= 50 else '#ed7d31' if taxa >= 25 else '#dc3545'
        taxa_bar = min(int(taxa), 100)
        cargo_str = (
            f' <span style="font-size:14px;font-weight:500;color:#ed7d31">⭐ {cargo_v}</span>'
        ) if cargo_v else ''
        # Assuntos apenas dos PLOs aprovados
        plos_aprov_v = set(df_leis[df_leis['autor_nome'] == vereador_selecionado]['plo_id'])
        ass_v_aprov  = df_ass[
            (df_ass['autor_nome'] == vereador_selecionado) &
            (df_ass['materia_id'].astype(str).isin(plos_aprov_v))
        ]
        top_ass = (
            ass_v_aprov.groupby('assunto')['materia_id'].nunique()
            .sort_values(ascending=False).head(6).index.tolist()
            if not ass_v_aprov.empty else []
        )
        autor_id_v = mapa_autor_id.get(vereador_selecionado)
        pills_parts = []
        for a in top_ass:
            aid = mapa_assunto_id.get(a)
            if autor_id_v and aid:
                href = url_sapl(ano=2026, autor_id=autor_id_v, assunto_id=aid, so_parlamentar=True)
                pills_parts.append(
                    f'<a href="{href}" target="_blank" class="pill-ass" '
                    f'style="text-decoration:none;cursor:pointer" title="Ver no SAPL">{a} 🔗</a>'
                )
            else:
                pills_parts.append(f'<span class="pill-ass">{a}</span>')
        pills = ''.join(pills_parts) or \
            f'<span style="color:{plot_font};opacity:0.6;font-size:13px">Nenhum assunto em PLOs aprovados</span>'

        col_f, col_i = st.columns([1, 2])
        with col_f:
            st.markdown(
                f'<div style="text-align:center;padding:30px 10px">'
                f'{foto_html(vereador_selecionado, foto, 180)}</div>',
                unsafe_allow_html=True
            )
        with col_i:
            st.markdown(f'<h2 style="margin:0">{vereador_selecionado}{cargo_str}</h2>',
                        unsafe_allow_html=True)
            r1, r2, r3 = st.columns(3)
            with r1:
                st.metric("📋 Total de matérias", int(dados_v['total_geral']))
            with r2:
                st.metric("📜 Projetos de Lei", int(dados_v['projetos_lei']))
            with r3:
                st.metric("✅ PLOs aprovados", int(dados_v['projetos_virou_lei']))
            r4, r5, r6 = st.columns(3)
            with r4:
                st.metric("📊 Taxa de aprovação", f"{taxa}%")
            with r5:
                st.metric("📨 Indicações", int(dados_v['indicacoes']))
            with r6:
                st.metric("📝 Requerimentos", int(dados_v['requerimentos']))
            st.markdown(f"""
            <div style="margin-top:8px">
                <div style="font-size:12px;color:{plot_font};opacity:0.7;margin-bottom:4px">Taxa de aprovação de PLOs</div>
                <div style="background:rgba(128,128,128,0.2);border-radius:8px;height:12px;overflow:hidden">
                    <div style="background:{taxa_cor};width:{taxa_bar}%;height:100%;border-radius:8px"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.divider()
        st.markdown("**🏷️ Principais assuntos de atuação**")
        st.markdown(f'<div style="padding:6px 0 16px 0">{pills}</div>', unsafe_allow_html=True)
        materias_mesa = int(dados_v.get('materias_mesa', 0))
        if materias_mesa > 0:
            st.markdown(
                f'<div style="font-size:13px;color:{plot_font};opacity:0.7;margin-top:4px">'
                f'+ {materias_mesa} matéria{"s" if materias_mesa > 1 else ""} '
                f'apresentada{"s" if materias_mesa > 1 else ""} como Mesa Diretora</div>',
                unsafe_allow_html=True
            )

    with aba_d1:
        st.subheader(f"📋 {vereador_selecionado}")
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1:
            st.metric("Total de matérias", int(dados_v['total_geral']))
        with c2:
            st.metric("Projetos de Lei", int(dados_v['projetos_lei']))
        with c3:
            st.metric("PLOs aprovados", int(dados_v['projetos_virou_lei']))
        with c4:
            st.metric("Taxa de aprovação", f"{dados_v['taxa_aprovacao']}%")
        with c5:
            st.metric("Requerimentos", int(dados_v['requerimentos']))
        with c6:
            st.metric("Indicações", int(dados_v['indicacoes']))
        st.divider()
        materias_mesa = int(dados_v.get('materias_mesa', 0))
        if materias_mesa > 0:
            st.caption(
                f"ℹ️ + {materias_mesa} matéria(s) apresentada(s) como Mesa Diretora "
                f"(não incluídas no total acima)"
            )
        col_pizza, col_lista = st.columns([1, 2])
        with col_pizza:
            df_tipos = (
                df_detalhe[~df_detalhe['tipo_sigla'].isin(['PLS', 'PLS2'])]
                .groupby('tipo_descricao').size()
                .reset_index(name='quantidade').sort_values('quantidade', ascending=False)
            )
            fig4 = px.pie(df_tipos, values='quantidade', names='tipo_descricao',
                          title="Distribuição por tipo")
            fig4.update_traces(textposition='inside', textinfo='percent+label')
            fig4.update_layout(showlegend=False)
            fig4 = aplicar_tema_plot(fig4)
            st.plotly_chart(fig4, width='stretch', config=PLOT_CONFIG)
        with col_lista:
            tipo_det = st.selectbox(
                "Filtrar por tipo",
                ["Todos"] + sorted(
                    df_detalhe[~df_detalhe['tipo_sigla'].isin(['PLS', 'PLS2'])]
                    ['tipo_descricao'].unique().tolist()
                ),
                key="tipo_detalhe"
            )
            df_lista = df_detalhe[~df_detalhe['tipo_sigla'].isin(['PLS', 'PLS2'])].copy()
            if tipo_det != "Todos":
                df_lista = df_lista[df_lista['tipo_descricao'] == tipo_det]
            df_lista = df_lista[['tipo_sigla', 'numero', 'ano', 'ementa']].copy()
            df_lista.columns = ['Tipo', 'Nº', 'Ano', 'Ementa']
            st.dataframe(df_lista, width='stretch', hide_index=True, height=320)

    with aba_d2:
        st.subheader(f"✅ {vereador_selecionado}")
        st.divider()
        # PLOs aprovados do vereador (apenas 2026 — filtro aplicado em carregar_dados)
        df_leis_v = df_leis[df_leis['autor_nome'] == vereador_selecionado].drop_duplicates('plo_id')
        if df_leis_v.empty:
            st.info("Nenhum PLO aprovado como lei até o momento.")
        else:
            df_leis_v = df_leis_v[['numero_plo', 'lei_numero', 'vinculado_via', 'lei_ementa']].copy()
            df_leis_v.columns = ['Nº PLO', 'Lei nº', 'Via', 'Ementa da Lei']
            st.dataframe(df_leis_v.sort_values('Nº PLO'), width='stretch', hide_index=True)
        # Projetos com substitutivo — todos onde o vereador participou (PLO, PLS ou PLS2)
        numeros_com_subst = set(df_parl[df_parl['tipo_sigla'].isin(['PLS', 'PLS2'])]['numero'])
        numeros_participou = set(
            df_parl[
                (df_parl['autor_nome'] == vereador_selecionado) &
                (df_parl['tipo_sigla'].isin(['PLO', 'PLS', 'PLS2']))
            ]['numero']
        )
        numeros_relevantes = sorted(numeros_participou & numeros_com_subst)

        if numeros_relevantes:
            st.divider()
            st.markdown("**🔄 Projetos com substitutivo — participação**")
            linhas_subst = []
            for num in numeros_relevantes:
                versoes_vereador = df_parl[
                    (df_parl['autor_nome'] == vereador_selecionado) &
                    (df_parl['numero'] == num)
                ]['tipo_sigla'].unique().tolist()
                autores_plo = df_parl[
                    (df_parl['tipo_sigla'] == 'PLO') &
                    (df_parl['numero'] == num)
                ]['autor_nome'].unique().tolist()
                ementa_rows = df_parl[(df_parl['numero'] == num) & (df_parl['tipo_sigla'] == 'PLO')]['ementa']
                ementa = ementa_rows.iloc[0] if not ementa_rows.empty else ''
                roles = []
                for tipo_v, sigla_v in [('PLO', 'PLO'), ('PLS', 'PLS'), ('PLS2', 'PLS2')]:
                    if tipo_v in versoes_vereador:
                        todos_autores_v = df_parl[
                            (df_parl['tipo_sigla'] == tipo_v) &
                            (df_parl['numero'] == num)
                        ]['autor_nome'].unique().tolist()
                        prefixo = 'co-autor' if len(todos_autores_v) > 1 else 'autor'
                        roles.append(f'{prefixo} do {sigla_v}')
                linhas_subst.append({
                    'Nº': num,
                    'Papel': ', '.join(roles),
                    'Autores do PLO original': ', '.join(autores_plo),
                    'Ementa': ementa[:80],
                })
            st.dataframe(pd.DataFrame(linhas_subst), width='stretch', hide_index=True)

    with aba_d3:
        st.subheader(f"🏷️ {vereador_selecionado}")
        st.divider()
        df_ass_v = df_ass[df_ass['autor_nome'] == vereador_selecionado]
        if df_ass_v.empty:
            st.info("Nenhum assunto cadastrado nos PLOs deste vereador.")
        else:
            df_ass_count = (
                df_ass_v.groupby('assunto').size()
                .reset_index(name='projetos').sort_values('projetos', ascending=True)
            )
            fig5 = px.bar(df_ass_count, x='projetos', y='assunto', orientation='h',
                          labels={'projetos': 'Projetos de Lei', 'assunto': ''},
                          color='projetos', color_continuous_scale=plot_colorscale, text='projetos',
                          custom_data=['assunto'])
            fig5.update_traces(textposition='outside')
            fig5.update_layout(coloraxis_showscale=False, height=400,
                               margin=dict(l=10, r=40, t=10, b=10))
            fig5 = aplicar_tema_plot(fig5)
            autor_id_v = mapa_autor_id.get(vereador_selecionado)
            evento5 = st.plotly_chart(fig5, width='stretch', on_select="rerun", key="chart_ass_v", config=PLOT_CONFIG)
            pontos5 = evento5.get("selection", {}).get("points", []) if evento5 else []
            if pontos5:
                cd5 = pontos5[0].get("customdata") or []
                assunto_clicado5 = cd5[0] if cd5 else pontos5[0].get("y")
                assunto_id5 = mapa_assunto_id.get(assunto_clicado5)
                if assunto_id5:
                    st.link_button(
                        f"🔗 Ver PLOs de {vereador_selecionado} sobre '{assunto_clicado5}' no SAPL",
                        url_sapl(ano=2026, autor_id=autor_id_v,
                                 assunto_id=assunto_id5, so_parlamentar=True)
                    )
            else:
                st.caption("💡 Clique em uma barra para abrir os PLOs deste assunto no SAPL.")
            pct_cobertura = round(
                len(df_ass_v['materia_id'].unique()) / int(dados_v['projetos_lei']) * 100, 1
            )
            st.caption(
                f"ℹ️ Assuntos cadastrados em {len(df_ass_v['materia_id'].unique())} "
                f"de {int(dados_v['projetos_lei'])} PLOs ({pct_cobertura}%)"
            )
            df_ass_v_aprov = df_ass_v.groupby('assunto').agg(
                apresentados=('materia_id', 'nunique'),
                aprovados=('virou_lei', lambda x: df_ass_v.loc[x.index]
                           .drop_duplicates('materia_id')['virou_lei'].sum())
            ).reset_index()
            if df_ass_v_aprov['aprovados'].sum() > 0:
                df_aprov_long = df_ass_v_aprov.melt(
                    id_vars='assunto', value_vars=['apresentados', 'aprovados'],
                    var_name='situação', value_name='projetos'
                )
                fig6 = px.bar(
                    df_aprov_long, x='assunto', y='projetos',
                    color='situação', barmode='group',
                    labels={'assunto': '', 'projetos': 'PLOs', 'situação': ''},
                    color_discrete_map={'apresentados': '#5b9bd5', 'aprovados': '#70ad47'},
                    title="Apresentados vs aprovados por assunto"
                )
                fig6.update_layout(height=350, xaxis_tickangle=-35,
                                   margin=dict(l=10, r=10, t=40, b=100),
                                   legend=dict(orientation='h', y=1.08))
                fig6 = aplicar_tema_plot(fig6)
                evento6 = st.plotly_chart(fig6, width='stretch', on_select="rerun", key="chart_ass_v2", config=PLOT_CONFIG)
                pontos6 = evento6.get("selection", {}).get("points", []) if evento6 else []
                if pontos6:
                    assunto_clicado6 = pontos6[0].get("x")
                    assunto_id6 = mapa_assunto_id.get(assunto_clicado6)
                    if assunto_id6:
                        st.link_button(
                            f"🔗 Ver PLOs de {vereador_selecionado} sobre '{assunto_clicado6}' no SAPL",
                            url_sapl(ano=2026, autor_id=autor_id_v,
                                     assunto_id=assunto_id6, so_parlamentar=True)
                        )
                else:
                    st.caption("💡 Clique em uma barra para abrir os PLOs deste assunto no SAPL.")
# ─── ABA RELATORIAS ────────────────────────────────────────────────────────────

    with aba_rel:
        st.markdown(f"### 🏷️ {vereador_selecionado}")
        st.divider()

        parl_id_v = int(df_vereadores[df_vereadores['nome_parlamentar'] == vereador_selecionado]['id'].iloc[0])

        if df_relatorias.empty:
            st.info("📋 Os dados de relatorias ainda não foram coletados. "
                    "Execute o workflow 'Atualizar dados SAPL' para incluí-los.")
        else:
            # Filtra por vereador e por 2026
            df_rel_v = df_relatorias[
                (df_relatorias['parlamentar'] == parl_id_v) &
                (df_relatorias['ano'].astype(str) == '2026')
            ].copy()

            total_rel = len(df_rel_v)
            st.caption(f"📋 {total_rel} relatoria(s) registrada(s) para {vereador_selecionado} em 2026")

            if df_rel_v.empty:
                st.info(f"Nenhuma relatoria registrada para {vereador_selecionado} em 2026.")
            else:
                # Ordenação: sequencia_regimental → número → comissão
                df_rel_v['seq_reg'] = df_rel_v['tipo_sigla'].map(mapa_tipo_seq).fillna(999)
                df_rel_v = df_rel_v.sort_values(['seq_reg', 'numero', 'comissao'])

                # Filtros lado a lado
                fc1, fc2 = st.columns(2)
                with fc1:
                    tipos_v = ["Todos"] + sorted(df_rel_v['tipo_sigla'].dropna().unique().tolist())
                    tipo_rel_sel = st.selectbox("📁 Tipo de matéria", tipos_v, key="sel_tipo_rel")
                with fc2:
                    comissoes_v = ["Todas"] + sorted(df_rel_v['comissao'].dropna().unique().tolist())
                    comissao_sel = st.selectbox("🏛️ Comissão", comissoes_v, key="sel_comissao_rel")

                if tipo_rel_sel != "Todos":
                    df_rel_v = df_rel_v[df_rel_v['tipo_sigla'] == tipo_rel_sel]
                if comissao_sel != "Todas":
                    df_rel_v = df_rel_v[df_rel_v['comissao'] == comissao_sel]

                # Botão(ões) de link para o SAPL
                # Quando sigla tem múltiplas descrições (ex: MOC), gera um botão por tipo
                tipos_desc_rel = (
                    df_rel_v['tipo_descricao'].dropna().unique().tolist()
                    if tipo_rel_sel != "Todos"
                    else []
                )
                if not tipos_desc_rel:
                    # Sem filtro de tipo: link geral por parlamentar
                    st.link_button(
                        f"🔗 Ver matérias de relatoria de {vereador_selecionado} em 2026 no SAPL",
                        f"{BASE_SAPL_URL}/materia/pesquisar-materia"
                        f"?salvar=Pesquisar&ano=2026&relatoria__parlamentar_id={parl_id_v}"
                    )
                elif len(tipos_desc_rel) == 1:
                    # Uma descrição — botão único com nome completo do tipo
                    tid = mapa_tipo_sapl_id.get(tipos_desc_rel[0])
                    url_t = (
                        f"{BASE_SAPL_URL}/materia/pesquisar-materia"
                        f"?salvar=Pesquisar&ano=2026&relatoria__parlamentar_id={parl_id_v}"
                        + (f"&tipo={tid}" if tid else "")
                    )
                    st.link_button(
                        f"🔗 Ver {tipos_desc_rel[0]} de relatoria de {vereador_selecionado} no SAPL",
                        url_t
                    )
                else:
                    # Múltiplas descrições (ex: MOC) — um botão por tipo
                    st.caption("Este tipo possui subtipagens — selecione o link desejado:")
                    for desc in sorted(tipos_desc_rel):
                        tid = mapa_tipo_sapl_id.get(desc)
                        url_t = (
                            f"{BASE_SAPL_URL}/materia/pesquisar-materia"
                            f"?salvar=Pesquisar&ano=2026&relatoria__parlamentar_id={parl_id_v}"
                            + (f"&tipo={tid}" if tid else "")
                        )
                        st.link_button(
                            f"🔗 Ver {desc} de relatoria de {vereador_selecionado} em 2026 no SAPL",
                            url_t, key=f"rel_link_{desc}"
                        )

                # Tabela
                df_exibir = df_rel_v[['tipo_sigla', 'numero', 'ementa', 'comissao']].copy()
                df_exibir.columns = ['Tipo', 'Número', 'Ementa', 'Comissão']
                st.dataframe(df_exibir, use_container_width=True, hide_index=True,
                             column_config={
                                 'Ementa':  st.column_config.TextColumn(width='large'),
                                 'Número':  st.column_config.NumberColumn(format='%d'),
                             })
                if tipo_rel_sel != "Todos" or comissao_sel != "Todas":
                    st.caption(f"Mostrando {len(df_rel_v)} de {total_rel} relatoria(s).")

# ─── ABA PRONUNCIAMENTOS ───────────────────────────────────────────────────────

    with aba_pron:
        st.markdown(f"### 🏷️ {vereador_selecionado}")
        st.divider()

        if df_pronunciamentos.empty:
            st.info("📢 Os dados de pronunciamentos ainda não foram coletados. "
                    "Execute o workflow 'Coletar dados pontuais' para incluí-los.")
        else:
            df_pron_v = df_pronunciamentos[
                (df_pronunciamentos['parlamentar'] == parl_id_v) &
                (df_pronunciamentos['ano'] == '2026')
            ].copy()

            total_pron = len(df_pron_v)
            st.caption(f"📢 {total_pron} pronunciamento(s) registrado(s) para {vereador_selecionado} em 2026")

            if df_pron_v.empty:
                st.info(f"Nenhum pronunciamento registrado para {vereador_selecionado} em 2026.")
            else:
                df_pron_v = df_pron_v.sort_values('data', ascending=False)
                df_pron_v['Data'] = pd.to_datetime(df_pron_v['data']).dt.strftime('%d/%m/%Y')

                # Tabela HTML: link clicável quando há URL, observação entre parênteses quando não há
                def cel_discurso_html(row):
                    if row['url_discurso']:
                        return (f'<a href="{row["url_discurso"]}" target="_blank" '
                                f'style="color:#4A90D9">🎥 Assistir no Instagram</a>')
                    elif row['observacao']:
                        return f'<span style="color:#888;font-size:0.9em">({row["observacao"]})</span>'
                    return '—'

                linhas_html = ""
                for _, row in df_pron_v.iterrows():
                    # Sessão: link para o YouTube se disponível
                    if row.get('url_video'):
                        cel_sessao = (f'<a href="{row["url_video"]}" target="_blank" '
                                      f'style="color:#4A90D9">{row["sessao_nome"]} 📺</a>')
                    else:
                        cel_sessao = row['sessao_nome']
                    linhas_html += (
                        f"<tr style='border-bottom:1px solid #eee'>"
                        f"<td style='white-space:nowrap;padding:6px 12px;vertical-align:top'>{row['Data']}</td>"
                        f"<td style='white-space:nowrap;padding:6px 12px;vertical-align:top'>{cel_sessao}</td>"
                        f"<td style='word-break:break-word;padding:6px 12px;vertical-align:top'>{cel_discurso_html(row)}</td>"
                        f"</tr>"
                    )
                st.markdown(
                    f"""<table style="width:100%;border-collapse:collapse;font-size:0.95em">
                    <thead><tr style="border-bottom:2px solid #ddd">
                      <th style="text-align:left;padding:6px 12px">Data</th>
                      <th style="text-align:left;padding:6px 12px">Sessão</th>
                      <th style="text-align:left;padding:6px 12px">Discurso</th>
                    </tr></thead>
                    <tbody>{linhas_html}</tbody>
                    </table>""",
                    unsafe_allow_html=True
                )

# ─── RODAPÉ INSTITUCIONAL ───────────────────────────────────────────────────────

st.divider()
st.caption(
    "ℹ️ O Painel Legislativo tem caráter informativo e educativo, e constitui uma das "
    "formas de publicação eletrônica da Câmara Municipal de Itabirito, dada sua "
    "capacidade de alcance e transparência. Os dados são extraídos automaticamente "
    "do Sistema de Apoio ao Processo Legislativo (SAPL). Em caso de divergência, "
    "ou para consulta aos textos integrais das matérias, recomenda-se sempre a "
    "verificação direta no SAPL."
)
