# 🗳️ Modo Período Eleitoral — registro para reativação

Este arquivo guarda **tudo** o que é preciso para reativar o modo "🗳️ Período Eleitoral" do Painel Legislativo numa próxima eleição. O modo funcionou de **15/07/2026 a 18/11/2026** (eleições gerais de 2026) e foi retirado do `app.py` depois delas, deixando só o painel completo (antigo "📊 Painel padrão"), público e sem senha.

> **Atenção:** a leitura jurídica abaixo é técnica, de apoio. A decisão de ativar ou não o modo — e de quando — cabe às instâncias competentes da Câmara.

---

## 1. Por que o modo existiu

Em 2026 (eleição geral, 1º turno em 04/10/2026) havia vereador da Casa disputando a eleição. Elementos do painel que **destacam ou ranqueiam** vereadores individualmente — pódio com medalhas, gráficos ordenados por desempenho, degradê de cor sinalizando "melhor/pior", taxa de aprovação em destaque — podem ser lidos como promoção pessoal ou publicidade institucional vedada nos 3 meses anteriores à eleição (Lei 9.504/97, art. 73, VI, "b", e art. 74; princípio da impessoalidade, art. 37, §1º, da Constituição).

**Próxima ocasião provável: eleições municipais de 2028** (1º turno previsto para o 1º domingo de outubro — 01/10/2028; confirmar no calendário do TSE). Numa eleição municipal **os próprios vereadores disputam a reeleição**, então o cuidado tende a ser ainda mais necessário do que em 2026. O período de vedação começa 3 meses antes do pleito (≈ início de julho de 2028).

## 2. O que o modo fazia

Seletor **"🗳️ Visualização"** numa 6ª coluna da barra de filtros, com duas opções:

| Modo | Senha? | Conteúdo |
|---|---|---|
| 🗳️ Período Eleitoral | Não — público, 1ª opção | Versão sem rankings, pódios, degradê nem taxa de aprovação individual |
| 📊 Painel padrão | Sim (`SENHA_PADRAO`) | Painel completo, só para revisão interna |

**No Período Eleitoral:**
- Filtros: só **Vereador** ativo (Tipo e Assunto forçados a "Todos" e ocultos). O filtro de Assunto foi retirado durante o período: combinado com Vereador, gerava um comparativo lado a lado.
- Visão geral (sem vereador escolhido) — abas: **🏷️ Projetos por assunto** (sem o heatmap comparativo) → **📄 Matérias** (total por tipo + escolha opcional de um vereador) → **📢 Pronunciamentos** → **📋 Vereadores** (cards em **ordem alfabética**, sem taxa). Em 2025 a aba de assunto não aparecia.
- Detalhe do vereador: mesmas abas do painel padrão, mas a 1ª se chamava **"📋 Resumo Geral"** (em vez de "📱 Em Destaque") e **sem** a métrica "Taxa de aprovação" e sem a barra "Taxa de aprovação de PLOs" (no Resumo Geral e na aba Matérias).
- Nenhum gráfico com degradê de cor.
- Legenda: "🗳️ Visualização adaptada para o período eleitoral."

**Isolamento:** o bloco do modo terminava em `st.stop()` — o conteúdo do painel completo nunca era processado na mesma execução (não era "escondido com CSS").

**Senha e hospedagem:**
- `SENHA_PADRAO` lida por `_ler_senha()`: `st.secrets` (Streamlit Cloud) ou variável de ambiente (Render).
- **Streamlit Cloud:** secret configurado → revisão interna pelo link `painel-legislativo-itabirito.streamlit.app`.
- **Render (embed no site da Câmara): deliberadamente SEM o secret** → o Painel padrão ficava permanentemente inacessível ali; senha errada ou vazia rebaixava silenciosamente para o Período Eleitoral.

## 3. Como reativar (passo a passo)

**Caminho mais seguro — recuperar pelo Git:** a tag **`periodo-eleitoral-2026`** (criada em 18/11/2026) aponta para o commit **`7b2308f`** ("Refactor sorting logic with ordenar_ranking function", 27/10/2026) — o último `app.py` com o modo completo e funcionando. Para abrir: no GitHub, seletor de branch `main` → aba **Tags** → `periodo-eleitoral-2026` → `app.py`. Mas o `app.py` vai ter mudado até lá, então o caminho prático costuma ser **reaplicar os trechos abaixo** sobre a versão atual:

1. **Cadastrar a senha** `SENHA_PADRAO` no Streamlit Cloud (Settings → Secrets). Use uma senha **nova**. **Não** cadastrar no Render.
2. **Trecho A** — substituir o bloco de filtros atual pelo bloco original (6 colunas, seletor de modo, controle de acesso, filtros por modo).
3. **Trecho B** — colar as duas funções e o bloco do modo logo **antes** de `# ─── VISÃO GERAL ──` (no lugar do comentário "MODO PERÍODO ELEITORAL — RETIRADO"). Precisa ficar **depois** dos HELPERS (`url_sapl`, `foto_html`, `mapa_foto`, `renderizar_rodape`...), porque usa todos eles.
4. **Trechos C, D e E** — no Detalhe do Vereador, trocar o título da 1ª aba e os dois blocos de métricas pelas versões com `if modo_selecionado == "🗳️ Período Eleitoral":`.
5. Validar (`ast.parse` + `py_compile` + `pyflakes` para nomes indefinidos) e testar os dois modos, nos dois tamanhos de tela, nos 3 temas.
6. Atualizar README (seção "Modos de visualização") e RESUMO_PROJETO.md.
7. Ao fim do período: retirar de novo, como foi feito em 18/11/2026.

**Pontos para revisar na reativação (o mundo terá mudado):**
- **Anos do seletor:** o código abaixo trata `"2025"` como "ano sem assunto". Em 2028 os anos serão outros — ajustar as condições `if ano_selecionado == "2025"`.
- **`url_sapl(ano=2026, ...)` fixo** nas funções de assunto (Trecho B) — trocar por `int(ano_selecionado)` ou pelo ano correto.
- **Que elementos ranqueiam:** se o painel ganhou abas novas desde 2026 (ex: "📈 Aprovação por Assunto", que já era exclusiva do painel padrão), verificar se elas também precisam ficar fora do modo público.
- Instagram da Câmara costuma parar de postar recortes de falas durante o período — esperado, não é bug.

---

## 4. Código removido, na íntegra

> Transcrição fiel do `app.py` de antes da retirada. Única diferença: dois comentários (`#`) foram reescritos para não citar pessoas nem cargos — não afetam o funcionamento. A versão exata, byte a byte, está na tag `periodo-eleitoral-2026`.

### Trecho A — barra de filtros com seletor de modo e senha

Substitui, no `app.py` atual, desde `# ─── FILTROS (barra horizontal no topo)` até a linha antes de `with f4:` (tema). Note que o bloco original **inclui** o `with f0:` do Ano, o recorte por ano e o `with f4:` do tema, iguais aos de hoje — reaplique com cuidado para não duplicar.

```python
# ─── FILTROS (barra horizontal no topo) ────────────────────────────────────────
# "Ano" é o primeiro filtro lido — igual já acontecia com modo_selecionado —
# porque ele decide o recorte de dados que todos os outros filtros e abas vão
# usar (tipo_opcoes, lista de vereadores, cards, tabelas etc.)

f0, f1, f2, f3, f4, f5 = st.columns([0.8, 1.3, 1.15, 1.15, 0.85, 1.25])

with f0:
    ano_selecionado = st.selectbox(
        "📅 Ano", ["2026", "2025"],
        help="Em 2025 ainda não há dados de assuntos "
             "(por isso as abas de assunto não aparecem nesse ano)."
    )

# Filtra os dados multi-ano para o ano escolhido no seletor acima. Os nomes
# usados daqui pra frente (df_expandido, df_parl, df_leis, df_ass, df_resumo)
# são os mesmos de sempre — só passam a apontar para o recorte do ano
# selecionado, então o resto do arquivo não precisa saber que existe um
# seletor de ano.
df_expandido = df_expandido_multi[df_expandido_multi['ano'].astype(str) == ano_selecionado].copy()
df_parl      = df_expandido[df_expandido['e_vereador_ativo']]
df_leis      = (
    df_leis_multi[df_leis_multi['ano_plo'].astype(str) == ano_selecionado]
    if not df_leis_multi.empty else df_leis_multi
)
df_ass = (
    df_ass_multi[df_ass_multi['ano'].astype(str) == ano_selecionado]
    if not df_ass_multi.empty else df_ass_multi
)
df_resumo = calcular_resumo_vereadores(df_expandido, df_parl, df_leis, mesa, df_vereadores)

assunto_selecionado = "Todos"
tipo_opcoes = ["Todos"] + sorted([
    t for t in df_parl['tipo_descricao'].unique()
    if t not in ['Projeto de Lei Substitutivo', 'Projeto de Lei Substitutivo (2)']
])

# ╔══════════════════════════════════════════════════════════════════╗
# ║  SENHAS TEMPORÁRIAS — SUBSTITUIR POR st.secrets QUANDO POSSÍVEL  ║
# ║  Ficam expostas aqui só até dar tempo de configurar os secrets   ║
# ║  no Streamlit Cloud e no Render. TROCAR ASSIM QUE POSSÍVEL.      ║
# ╚══════════════════════════════════════════════════════════════════╝
# ╔══════════════════════════════════════════════════════════════════╗
# ║  SENHAS — lidas de st.secrets (Streamlit Cloud) ou variável de   ║
# ║  ambiente (Render). Nunca ficam escritas no código.              ║
# ║  Cadastrar em: Streamlit Cloud → Settings → Secrets              ║
# ║                Render → Environment                              ║
# ╚══════════════════════════════════════════════════════════════════╝
def _ler_senha(nome):
    try:
        return st.secrets[nome]
    except Exception:
        return os.environ.get(nome, "")

SENHA_PADRAO = _ler_senha("SENHA_PADRAO")

# Modo precisa ser lido antes dos demais filtros (mas exibido na 5ª coluna)
with f5:
    modo_selecionado = st.selectbox(
        "🗳️ Visualização", ["🗳️ Período Eleitoral", "📊 Painel padrão"],
        help="Painel temporariamente simplificado em razão do período eleitoral."
    )

# ─── CONTROLE DE ACESSO — só o Painel padrão exige senha ───────────────────────
# Sem a senha certa, o modo é rebaixado para "Período Eleitoral" — que agora é
# o modo público e seguro (substitui o antigo "Em Adaptação", aposentado).
_f3_usada_para_senha = False
if modo_selecionado == "📊 Painel padrão":
    if not st.session_state.get("auth_padrao", False):
        _f3_usada_para_senha = True
        with f3:
            _senha_padrao_in = st.text_input(
                "🔒 Senha do Painel padrão", type="password", key="senha_padrao_input"
            )
        if _senha_padrao_in and _senha_padrao_in == SENHA_PADRAO:
            st.session_state["auth_padrao"] = True
            st.rerun()
        else:
            if _senha_padrao_in:
                st.error("Senha incorreta.")
            modo_selecionado = "🗳️ Período Eleitoral"

# ─── FILTROS POR MODO ───────────────────────────────────────────────────────────
# "Período Eleitoral": sem filtro de tipo nem assunto (o filtro de Assunto foi
# retirado — combinado com Vereador, ele produzia uma espécie
# de comparativo/ranking entre vereadores, o que este modo existe para evitar).
# Só o filtro de Vereador fica ativo.
# "Painel padrão": todos os filtros normalmente.
if modo_selecionado == "🗳️ Período Eleitoral":
    tipo_selecionado     = "Todos"
    assunto_selecionado  = "Todos"
    if not _f3_usada_para_senha:
        with f3:
            st.write("")
    with f1:
        st.write("")
    with f2:
        vereadores_lista     = ["Todos"] + sorted(df_parl['autor_nome'].unique().tolist())
        vereador_selecionado = st.selectbox("👤 Vereador", vereadores_lista)
else:
    # Painel padrão — só chega aqui autenticado (senão foi rebaixado acima)
    with f3:
        tipo_selecionado = st.selectbox("📁 Tipo de matéria", tipo_opcoes)
    with f1:
        # 2025 ainda não tem vínculo de assunto cadastrado no SAPL para os
        # PLOs (praticamente zero registros) — filtro fica indisponível,
        # igual já acontece no modo Período Eleitoral.
        if ano_selecionado == "2025":
            st.caption("🏷️ Assunto — disponível só em 2026")
        elif tipo_selecionado in ["Todos", "Projeto de Lei Ordinária"]:
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
    tema = st.selectbox(
        "🎨 Contraste",
        ["🌞 Claro", "🌙 Escuro", "🏛️ Institucional"]
    )

# Nota informativa + data de atualização — numa única linha compacta
# _ts já lido no topo do arquivo como string "DD/MM/YYYY às HH:MM"
_atu = f"  ·  🔄 Última atualização dos dados: {_ts}" if _ts else ""
st.caption(f"ℹ️ PLS e PLS2 são substitutivos de PLOs e não contam como projetos separados{_atu}")

```

### Trecho B — funções exclusivas e bloco do modo (termina em `st.stop()`)

Vai logo antes de `# ─── VISÃO GERAL ──`.

```python
def renderizar_projetos_por_assunto_sem_heatmap():
    """Aba 'Projetos por assunto' sem o heatmap comparativo entre vereadores —
    reaproveitada no período eleitoral (único modo que a chama)."""
    if modo_selecionado == "🗳️ Período Eleitoral":
        # Período Eleitoral não tem mais o filtro de Assunto (retirado) e
        # por isso perdeu o "?" com o percentual de PLOs com assunto
        # cadastrado, que no Painel padrão aparece no help= do selectbox. Repõe a
        # mesma informação aqui, como um "?" ao lado do título da aba.
        _total_plos_adapt = df_parl[df_parl['tipo_sigla'] == 'PLO']['materia_id'].nunique()
        _plos_c_assunto_adapt = df_ass['materia_id'].nunique()
        _pct_adapt = round(_plos_c_assunto_adapt / _total_plos_adapt * 100, 1) if _total_plos_adapt > 0 else 0
        st.subheader(
            "🏷️ Projetos por assunto",
            help=f"Assuntos disponíveis para {_pct_adapt}% dos PLOs cadastrados"
        )
    if df_ass.empty:
        st.info("Nenhum assunto cadastrado nos dados carregados.")
    else:
        top_assuntos_pe = (
            df_ass.groupby('assunto')['materia_id'].nunique()
            .sort_values(ascending=False).head(15).index.tolist()
        )
        df_ass_top_pe = df_ass[df_ass['assunto'].isin(top_assuntos_pe)]
        df_comp_pe = (
            df_ass_top_pe.groupby('assunto')
            .agg(
                apresentados=('materia_id', 'nunique'),
                aprovados=('virou_lei', lambda x: df_ass_top_pe.loc[x.index]
                           .drop_duplicates('materia_id')['virou_lei'].sum()),
            )
            .reset_index().sort_values('apresentados', ascending=False)
        )

        def _url_ass_pe(assunto):
            aid = mapa_assunto_id.get(assunto)
            if not aid:
                return None
            return url_sapl(ano=2026, assunto_id=aid, so_parlamentar=True)

        st.markdown(
            html_barchart_grouped_h(
                df_comp_pe, 'assunto', _url_ass_pe,
                series=[('apresentados', 'apresentados'), ('aprovados', 'aprovados')],
                colors=[cor_azul, cor_verde],
            ),
            unsafe_allow_html=True
        )
        st.caption("💡 Clique em uma barra para abrir os PLOs do assunto no SAPL.")
        df_comp_pe['taxa'] = (df_comp_pe['aprovados'] / df_comp_pe['apresentados'] * 100).round(1)
        df_comp_pe.columns = ['Assunto', 'Apresentados', 'Aprovados', 'Taxa (%)']
        df_comp_pe_sorted = ordenar_ranking(df_comp_pe, 'Taxa (%)', 'Aprovados', 'Assunto')
        _autor_fil_pe = mapa_autor_id.get(vereador_selecionado) if vereador_selecionado != "Todos" else None
        _linhas_ass_pe = ""
        for _, _row in df_comp_pe_sorted.iterrows():
            _aid_t = mapa_assunto_id.get(_row['Assunto'])
            if _aid_t:
                _url_t = url_sapl(ano=2026, autor_id=_autor_fil_pe, assunto_id=_aid_t, so_parlamentar=True)
                _cel = f'<a href="{_url_t}" target="_blank" style="color:{cor_link}">{_row["Assunto"]} ↗</a>'
            else:
                _cel = _row['Assunto']
            _linhas_ass_pe += (
                f"<tr style='border-bottom:1px solid #eee'>"
                f"<td style='padding:6px 12px'>{_cel}</td>"
                f"<td style='padding:6px 12px;text-align:center'>{int(_row['Apresentados'])}</td>"
                f"<td style='padding:6px 12px;text-align:center'>{int(_row['Aprovados'])}</td>"
                f"<td style='padding:6px 12px;text-align:center'>{_row['Taxa (%)']}%</td>"
                f"</tr>"
            )
        st.markdown(
            f"""<table style="width:100%;border-collapse:collapse;font-size:0.95em">
            <thead><tr style="border-bottom:2px solid #ddd">
              <th style="text-align:left;padding:6px 12px">Assunto ↗ abre no SAPL</th>
              <th style="text-align:center;padding:6px 12px">Apresentados</th>
              <th style="text-align:center;padding:6px 12px">Aprovados</th>
              <th style="text-align:center;padding:6px 12px">Taxa (%)</th>
            </tr></thead>
            <tbody>{_linhas_ass_pe}</tbody></table>""",
            unsafe_allow_html=True
        )

def renderizar_aba_materias():
    """Aba 'Matérias': total geral por tipo + filtro interno opcional por vereador —
    reaproveitada no período eleitoral (único modo que a chama). Sem comparativo
    entre vereadores: o gráfico por vereador só aparece após escolha explícita."""
    st.markdown(f"##### Matérias apresentadas por tipo — {ano_selecionado}")
    st.caption("Somente vereadores em exercício — não inclui Executivo, Mesa Diretora ou autores externos.")
    _tipos_pe = [t for t in tipo_opcoes if t != "Todos"]
    _linhas_tipo_pe = []
    for _t in _tipos_pe:
        _qtd = df_parl[
            (~df_parl['tipo_sigla'].isin(['PLS', 'PLS2'])) &
            (df_parl['tipo_descricao'] == _t)
        ]['materia_id'].nunique()
        if _qtd > 0:
            _linhas_tipo_pe.append({'tipo': _t, 'total': _qtd})
    df_tipo_geral_pe = pd.DataFrame(_linhas_tipo_pe).sort_values('total', ascending=False)

    def _url_tipo_geral_pe(tipo_desc):
        tid = mapa_tipo_sapl_id.get(tipo_desc)
        if not tid:
            return None
        return url_sapl(ano=int(ano_selecionado), tipo_materia_id=tid, so_parlamentar=True)

    st.markdown(
        html_barchart_h(df_tipo_geral_pe, 'tipo', 'total', _url_tipo_geral_pe),
        unsafe_allow_html=True
    )
    st.caption("💡 Clique em uma barra para abrir as matérias desse tipo no SAPL.")

    st.divider()
    st.markdown("##### Ver por vereador (opcional)")
    _vereadores_pe_lista = ["—"] + sorted(df_parl['autor_nome'].unique().tolist())
    _vereador_pe = st.selectbox(
        "Escolha um vereador para ver a distribuição de matérias dele por tipo:",
        _vereadores_pe_lista, key="pick_vereador_materias_pe"
    )
    if _vereador_pe != "—":
        df_v_tipo_pe = (
            df_sem_pls[df_sem_pls['autor_nome'] == _vereador_pe]
            .groupby('tipo_descricao')['materia_id'].nunique()
            .reset_index(name='total').sort_values('total', ascending=False)
        )
        _autor_id_pe = mapa_autor_id.get(_vereador_pe)

        def _url_tipo_vereador_pe(tipo_desc):
            tid = mapa_tipo_sapl_id.get(tipo_desc)
            if not tid or not _autor_id_pe:
                return None
            return url_sapl(ano=int(ano_selecionado), autor_id=_autor_id_pe, so_parlamentar=True, tipo_materia_id=tid)

        st.markdown(f"**Matérias de {_vereador_pe} por tipo — {ano_selecionado}**")
        st.markdown(
            html_barchart_h(df_v_tipo_pe, 'tipo_descricao', 'total', _url_tipo_vereador_pe),
            unsafe_allow_html=True
        )
        st.caption(f"💡 Clique em uma barra para abrir as matérias de {_vereador_pe} desse tipo no SAPL.")

# ─── FLAG: MODO PERÍODO ELEITORAL ──────────────────────────────────────────────
# Roda só depois dos HELPERS acima (fotos, url_sapl, foto_html já existem).
# Se ativo E nenhum vereador específico estiver selecionado, renderiza o bloco
# abaixo e para com st.stop(). Quando um vereador ESTÁ selecionado, este bloco
# nem entra — o script segue direto para "DETALHE DO VEREADOR" mais abaixo,
# que já é compartilhado entre os dois modos (mesmas abas: Em Destaque, Matérias,
# PLOs aprovados, Assuntos, Relatorias, Pronunciamentos — sem duplicar código).
if modo_selecionado == "🗳️ Período Eleitoral" and vereador_selecionado == "Todos":
    st.caption("🗳️ Visualização adaptada para o período eleitoral.")

    if ano_selecionado == "2025":
        # 2025 ainda não tem assunto alimentado historicamente — só essa
        # aba fica de fora. Pronunciamentos já tem dado completo de 2025.
        _titulos_pe = ["📄 Matérias", "📢 Pronunciamentos", "📋 Vereadores"]
    else:
        _titulos_pe = ["🏷️ Projetos por assunto", "📄 Matérias", "📢 Pronunciamentos", "📋 Vereadores"]
    _abas_pe = st.tabs(_titulos_pe)
    _idx_pe = {nome: i for i, nome in enumerate(_titulos_pe)}   # indexação por nome — evita erro de posição

    # ── ABA: PROJETOS POR ASSUNTO — igual à versão padrão, sem o heatmap ───────
    if "🏷️ Projetos por assunto" in _idx_pe:
        with _abas_pe[_idx_pe["🏷️ Projetos por assunto"]]:
            renderizar_projetos_por_assunto_sem_heatmap()

    # ── ABA: MATÉRIAS — total geral por tipo + filtro interno por vereador ─────
    with _abas_pe[_idx_pe["📄 Matérias"]]:
        renderizar_aba_materias()

    # ── ABA: PRONUNCIAMENTOS — sem filtro de vereador, atende à cartilha ATRICON ─
    if "📢 Pronunciamentos" in _idx_pe:
        with _abas_pe[_idx_pe["📢 Pronunciamentos"]]:
            renderizar_pronunciamentos_geral()

    # ── ABA: VEREADORES — sempre visível, ordem alfabética, sem taxa ───────────
    with _abas_pe[_idx_pe["📋 Vereadores"]]:
        st.markdown(f"### Vereadores de Itabirito — {ano_selecionado}")

        def _num_html(valor, cor, href):
            _num = (f'<div style="font-size:26px;font-weight:700;color:{cor};'
                    f'line-height:1">{valor}</div>')
            return (f'<a href="{href}" target="_blank" style="text-decoration:none">{_num}</a>'
                    if href else _num)

        # Ordem alfabética — sem ranqueamento por valor
        df_destaque_pe = df_resumo.sort_values('autor_nome', ascending=True)
        _lista_pe = list(df_destaque_pe.iterrows())
        for row_start in range(0, len(_lista_pe), 3):
            cols_pe = st.columns(3)
            for j, (_, row) in enumerate(_lista_pe[row_start:row_start + 3]):
                nome       = row['autor_nome']
                foto       = mapa_foto.get(nome, '')
                cargo_mesa = mapa_cargo.get(nome, '')
                cargo_badge = (
                    f'<div style="font-size:10px;font-weight:600;color:{cor_laranja};'
                    f'margin-bottom:8px;letter-spacing:0.5px">⭐ {cargo_mesa}</div>'
                ) if cargo_mesa else '<div style="height:22px"></div>'

                # Foto → página do parlamentar no SAPL (sem filtros)
                parl_id   = mapa_parlamentar_id.get(nome)
                foto_href = f"{BASE_SAPL_URL}/parlamentar/{parl_id}" if parl_id else None
                foto_tag = (
                    f'<a href="{foto_href}" target="_blank" style="display:block;cursor:pointer" '
                    f'title="Ver parlamentar no SAPL">{foto_html(nome, foto, 80)}</a>'
                ) if foto_href else foto_html(nome, foto, 80)

                autor_id_c = mapa_autor_id.get(nome)
                _tid_ind   = mapa_tipo_sapl_id.get('IND')
                _tid_req   = mapa_tipo_sapl_id.get('REQ')

                _url_pl = (
                    url_sapl(ano=int(ano_selecionado), autor_id=autor_id_c, so_parlamentar=True,
                            tipo_materia_id=TIPO_MATERIA_SAPL['PLO'])
                    if autor_id_c else None
                )
                _url_ind = (
                    url_sapl(ano=int(ano_selecionado), autor_id=autor_id_c, so_parlamentar=True, tipo_materia_id=_tid_ind)
                    if autor_id_c and _tid_ind else None
                )
                _url_req = (
                    url_sapl(ano=int(ano_selecionado), autor_id=autor_id_c, so_parlamentar=True, tipo_materia_id=_tid_req)
                    if autor_id_c and _tid_req else None
                )
                # Tarja de matérias — apenas vereador + ano, sem outros filtros
                _url_mat = url_sapl(ano=int(ano_selecionado), autor_id=autor_id_c) if autor_id_c else None
                _tarja = f'{int(row["total_geral"])} matérias apresentadas'
                _tarja_html = (
                    f'<a href="{_url_mat}" target="_blank" style="text-decoration:none">'
                    f'<div class="card-secondary">{_tarja}</div></a>'
                    if _url_mat else f'<div class="card-secondary">{_tarja}</div>'
                )

                with cols_pe[j]:
                    st.markdown(
                        f'<div class="card-pop" style="border:1px solid {card_border}">'
                        f'<div style="margin-bottom:12px">{foto_tag}</div>'
                        f'<div class="card-nome">{nome}</div>{cargo_badge}'
                        f'<div style="display:flex;justify-content:space-around;margin-bottom:10px">'
                        f'<div>{_num_html(int(row["projetos_lei"]), cor_azul, _url_pl)}'
                        f'<div class="card-muted">Projetos de Lei</div></div>'
                        f'<div><div style="font-size:26px;font-weight:700;color:{cor_verde};line-height:1">'
                        f'{int(row["projetos_virou_lei"])}</div>'
                        f'<div class="card-muted">PLOs aprovados</div></div>'
                        f'</div>'
                        f'<div style="display:flex;justify-content:space-around;margin-bottom:12px">'
                        f'<div>{_num_html(int(row["indicacoes"]), cor_roxo, _url_ind)}'
                        f'<div class="card-muted">Indicações</div></div>'
                        f'<div>{_num_html(int(row["requerimentos"]), cor_laranja, _url_req)}'
                        f'<div class="card-muted">Requerimentos</div></div>'
                        f'</div>'
                        f'{_tarja_html}'
                        f'</div>',
                        unsafe_allow_html=True
                    )

    renderizar_rodape()
    st.stop()

```

### Trecho C — título da 1ª aba do Detalhe do Vereador

```python
    _titulo_pop2 = "📋 Resumo Geral" if modo_selecionado == "🗳️ Período Eleitoral" else "📱 Em Destaque"
```

### Trecho D — métricas da aba "Em Destaque/Resumo Geral" do vereador

```python
            r1, r2, r3 = st.columns(3)
            with r1:
                st.metric("📋 Total de matérias", int(dados_v['total_geral']))
            with r2:
                st.metric("📜 Projetos de Lei", int(dados_v['projetos_lei']))
            with r3:
                st.metric("✅ PLOs aprovados", int(dados_v['projetos_virou_lei']))
            if modo_selecionado == "🗳️ Período Eleitoral":
                r4, r5 = st.columns(2)
                with r4:
                    st.metric("📨 Indicações", int(dados_v['indicacoes']))
                with r5:
                    st.metric("📝 Requerimentos", int(dados_v['requerimentos']))
            else:
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
```

### Trecho E — métricas da aba "📂 Matérias" do vereador

```python
    with aba_d1:
        st.subheader(f"📋 {vereador_selecionado}")
        if modo_selecionado == "🗳️ Período Eleitoral":
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                st.metric("Total de matérias", int(dados_v['total_geral']))
            with c2:
                st.metric("Projetos de Lei", int(dados_v['projetos_lei']))
            with c3:
                st.metric("PLOs aprovados", int(dados_v['projetos_virou_lei']))
            with c4:
                st.metric("Requerimentos", int(dados_v['requerimentos']))
            with c5:
                st.metric("Indicações", int(dados_v['indicacoes']))
        else:
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
```

### Docstrings originais (só referência)

```python
def renderizar_pronunciamentos_geral():
    """Conteúdo da aba geral de pronunciamentos — reaproveitado no painel padrão
    e no modo período eleitoral (busca por sessão, sem depender de filtro de vereador)."""
    st.markdown("##### Selecione uma sessão para ver quais vereadores fizeram uso da palavra livre")
...
def renderizar_rodape():
    """Nota institucional de rodapé — reaproveitada no painel padrão e no
    período eleitoral (que termina cedo via st.stop(), sem chegar ao rodapé original)."""
    st.divider()
```

---

## 5. Texto que estava no README

> ### Modos de visualização
> O painel possui dois modos, selecionáveis no filtro "🗳️ Visualização":
> - **Modo público** (hoje rotulado "🗳️ Período Eleitoral", sem senha) — versão simplificada, sem rankings, pódios ou comparativos individuais entre parlamentares. Pensado para períodos que exigem maior neutralidade (ex. proximidade de eleições), mas o rótulo e o gatilho podem ser adaptados livremente para o contexto de cada Casa.
> - **Modo padrão** ("📊 Painel padrão", protegido por senha) — versão completa, com rankings, pódios e comparativos entre vereadores, pensada para uso interno.
>
> A senha do modo padrão é lida via `st.secrets` (Streamlit Cloud) ou variável de ambiente (outros serviços de hospedagem) — ver "Como rodar localmente" abaixo e `COMO_PUBLICAR.md`. Sem essa senha configurada, o modo padrão fica permanentemente inacessível e o painel roda sempre no modo público — útil para hospedar uma cópia pública (ex. embed no site) separada da versão de revisão interna.

E no "Como rodar localmente", passo 5:

> `# 5. (Opcional) configure a senha do modo padrão em .streamlit/secrets.toml:`
> `# SENHA_PADRAO = "sua_senha_aqui"`
> `# Sem isso, o painel roda sempre no modo público.`

---

*Registro criado em 18/11/2026, ao retirar o modo após as eleições de 2026.*
