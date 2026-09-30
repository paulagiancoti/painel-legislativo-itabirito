# 🏛️ Painel Legislativo — Câmara Municipal de Itabirito

Painel interativo de acompanhamento da atividade legislativa da Câmara Municipal de Itabirito (MG), desenvolvido com Python e Streamlit.

🔗 **Acesso:** [painel-legislativo-itabirito.streamlit.app](https://painel-legislativo-itabirito.streamlit.app)

---

## Sobre o projeto

O Painel Legislativo tem caráter informativo e educativo, e constitui uma das formas de publicação eletrônica da Câmara Municipal de Itabirito, dada sua capacidade de alcance e transparência. Os dados são extraídos automaticamente do [SAPL — Sistema de Apoio ao Processo Legislativo](https://sapl.itabirito.mg.leg.br).

Em caso de divergência, ou para consulta aos textos integrais das matérias, recomenda-se a verificação direta no SAPL.

---

## Funcionalidades

### Modos de visualização
O painel possui dois modos, selecionáveis no filtro "🗳️ Visualização":
- **Modo público** (hoje rotulado "🗳️ Período Eleitoral", sem senha) — versão simplificada, sem rankings, pódios ou comparativos individuais entre parlamentares. Pensado para períodos que exigem maior neutralidade (ex. proximidade de eleições), mas o rótulo e o gatilho podem ser adaptados livremente para o contexto de cada Casa.
- **Modo padrão** ("📊 Painel padrão", protegido por senha) — versão completa, com rankings, pódios e comparativos entre vereadores, pensada para uso interno.

A senha do modo padrão é lida via `st.secrets` (Streamlit Cloud) ou variável de ambiente (outros serviços de hospedagem) — ver "Como rodar localmente" abaixo e `COMO_PUBLICAR.md`. Sem essa senha configurada, o modo padrão fica permanentemente inacessível e o painel roda sempre no modo público — útil para hospedar uma cópia pública (ex. embed no site) separada da versão de revisão interna.

### Seletor de ano
Os dados podem ser consultados por ano (hoje **2026** e **2025**). Em 2025 as abas de assunto não aparecem, porque não há classificação por assunto para as matérias daquele ano.

### Visão geral (todos os vereadores)
- **Ranking de matérias** por vereador com link direto ao SAPL
- **Taxa de aprovação de PLOs** (Projetos de Lei Ordinária) com tabela clicável por parlamentar
- **Projetos por assunto** — gráfico de barras, tabela com links e mapa de calor comparativo
- **Aprovação por Assunto** — taxa de aprovação recalculada só com os assuntos que o cidadão escolher
- **Em Destaque** — cards individuais com foto, estatísticas e assuntos de atuação
- **Pronunciamentos** — lista de sessões com oradores e considerações finais da Presidência, com links para o SAPL, para a sessão completa no YouTube e para o recorte de cada fala no Instagram da Câmara

### Perfil do vereador
- **Matérias** — tabela filtrável por tipo
- **PLOs aprovados** — projetos que viraram lei, com informação sobre substitutivos
- **Assuntos** — gráfico de atuação com links diretos ao SAPL
- **Relatorias** — filtro por tipo de matéria e comissão, com links ao SAPL
- **Pronunciamentos** — histórico de sessões com links para a sessão no YouTube e para o recorte da fala no Instagram

### Recursos gerais
- **Filtros combinados** — Ano, Assunto, Vereador, Tipo de matéria, Contraste (tema visual) e Visualização (modo)
- **Links clicáveis** nos gráficos e tabelas — abrem a pesquisa no SAPL já filtrada
- **Seletores dropdown** abaixo dos gráficos para navegação direta no celular
- **Temas visuais** — Claro, Escuro e Institucional (cores da identidade visual da Câmara)
- **Atualização automática** duas vezes ao dia via GitHub Actions

---

## Tecnologias

| Ferramenta | Uso |
|---|---|
| Python 3 | Linguagem principal |
| Streamlit | Framework do painel web |
| Pandas | Manipulação dos dados |
| Plotly | Gráficos interativos |
| Requests | Coleta de dados via API SAPL |
| GitHub Actions | Atualização automática (2x ao dia) |
| Render | Hospedagem (embed no site da Câmara) |
| Streamlit Cloud | Hospedagem (versão pública direta) |

> **Nota:** o `requirements.txt` fixa `pyarrow<25.0.0` para evitar uma instabilidade conhecida (segmentation fault na inicialização) em alguns ambientes de hospedagem gerenciada.

---

## Estrutura do repositório

```
painel-legislativo-itabirito/
├── app.py                        # Painel principal (Streamlit)
├── atualizar_dados.py            # Coleta automática: matérias, normas, assuntos e vínculos, relatorias, oradores, sessões
├── coletar_dados_iniciais.py     # Coleta única: vereadores, autores, mesa, assuntos, comissões, tipos
├── coletar_pontual.py            # Coleta manual: baixa novamente todos os oradores
├── atualizar_fotos.py            # Coleta manual de fotos dos vereadores
├── requirements.txt              # Dependências Python
├── COMO_PUBLICAR.md              # Guia completo de publicação e manutenção
├── .streamlit/
│   └── config.toml               # Configuração de tema
├── .github/
│   └── workflows/
│       ├── atualizar.yml         # GitHub Actions — atualização automática (2x ao dia)
│       ├── coletar_pontual.yml   # GitHub Actions — recoleta manual dos oradores
│       └── atualizar_fotos.yml   # GitHub Actions — atualização manual de fotos
└── dados/
    ├── vereadores.json
    ├── autores.json
    ├── mesa_diretora.json
    ├── materias.json             # Matérias de 2026 (exibição)
    ├── materias_historico.json   # Histórico de matérias (seletor de ano e cruzamento com normas)
    ├── normas.json
    ├── assuntos.json             # Lista de assuntos (atualizada a cada coleta)
    ├── materiaassuntos.json      # Vínculos matéria↔assunto (atualizado a cada coleta)
    ├── relatorias.json
    ├── oradores.json             # Oradores das sessões, com link do recorte no Instagram
    ├── sessoes.json
    ├── comissoes.json            # Criado manualmente (API indisponível)
    ├── tipomaterias.json
    └── pronunciamentos_extras.json  # Considerações finais da Presidência (manual)
```

---

## Fonte dos dados

Todos os dados são extraídos do SAPL de Itabirito — da API pública e da pesquisa pública de matérias (usada para autoria e para os assuntos das matérias):

```
https://sapl.itabirito.mg.leg.br/api/
https://sapl.itabirito.mg.leg.br/materia/pesquisar-materia
```

Os dados são atualizados automaticamente duas vezes ao dia, por volta das **11h e 22h (horário de Brasília)**, via GitHub Actions — o horário exato pode atrasar, pois o agendamento do GitHub não é garantido. Em caso de falha na coleta automática, os dados anteriores são preservados: o script não sobrescreve arquivos com resultado vazio ou incompleto.

Os links dos recortes de pronunciamentos no Instagram são cadastrados manualmente no SAPL pela equipe da Câmara.

---

## Regras de negócio

- **PLO → PLS → PLS2:** mesmo número = mesmo projeto. PLS e PLS2 são substitutivos e não contam como projetos separados nos comparativos.
- **Élio da Mata** (Chefe do Executivo) é excluído dos comparativos entre vereadores.
- **Mesa Diretora** aparece como nota informativa, não somada individualmente.
- **Co-autorias** são expandidas em linhas; a contagem usa `nunique()` por `materia_id`.
- O cruzamento de normas usa `materias_historico.json` para capturar PLOs de 2025 aprovados como leis em 2026.
- As métricas de aprovação contabilizam apenas os PLOs do ano selecionado.

---

## Como rodar localmente

```bash
# 1. Clone o repositório
git clone https://github.com/paulagiancoti/painel-legislativo-itabirito.git
cd painel-legislativo-itabirito

# 2. Crie e ative o ambiente virtual (Windows)
python -m venv .venv
& ".venv\Scripts\Activate.ps1"

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Colete os dados (primeira vez)
python coletar_dados_iniciais.py
python atualizar_dados.py

# 5. (Opcional) configure a senha do modo padrão em .streamlit/secrets.toml:
# SENHA_PADRAO = "sua_senha_aqui"
# Sem isso, o painel roda sempre no modo público.

# 6. Rode o painel
python -m streamlit run app.py
```

---

## Manutenção

Para publicar uma atualização de código: edite o arquivo desejado e faça commit — o Render e o Streamlit Cloud atualizam automaticamente.

Para atualizar os dados manualmente fora do horário agendado, consulte o arquivo **[COMO_PUBLICAR.md](COMO_PUBLICAR.md)**.

Se links de pronunciamentos antigos forem corrigidos no SAPL, rode manualmente o workflow **"Coletar oradores (pontual)"** para que o painel receba as correções.

---

## Créditos

Os dados exibidos neste painel são extraídos do **SAPL — Sistema de Apoio ao Processo Legislativo**, desenvolvido e mantido pelo [Interlegis](https://github.com/interlegis/sapl). O SAPL é um software livre utilizado por câmaras municipais em todo o Brasil.

O painel foi desenvolvido em parceria com **[Claude](https://claude.ai)** (Anthropic) — o código, a arquitetura e as soluções técnicas foram construídos de forma colaborativa ao longo de múltiplas sessões de trabalho.

---

*Desenvolvido para a Câmara Municipal de Itabirito (MG) · 2026*
