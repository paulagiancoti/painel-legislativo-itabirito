# 🏛️ Painel Legislativo — Câmara Municipal de Itabirito

Painel interativo de acompanhamento da atividade legislativa da Câmara Municipal de Itabirito (MG), desenvolvido com Python e Streamlit.

🔗 **Acesso:** [painel-legislativo-itabirito.streamlit.app](https://painel-legislativo-itabirito.streamlit.app)

---

## Sobre o projeto

O Painel Legislativo tem caráter informativo e educativo, e constitui uma das formas de publicação eletrônica da Câmara Municipal de Itabirito, dada sua capacidade de alcance e transparência. Os dados são extraídos automaticamente do [SAPL — Sistema de Apoio ao Processo Legislativo](https://sapl.itabirito.mg.leg.br).

Em caso de divergência, ou para consulta aos textos integrais das matérias, recomenda-se a verificação direta no SAPL.

---

## Funcionalidades

- **Ranking de matérias** por vereador com link direto ao SAPL
- **Taxa de aprovação de PLOs** (Projetos de Lei Ordinária) por parlamentar
- **Projetos por assunto** — gráfico de barras e mapa de calor comparativo
- **Em Destaque** — cards individuais com foto, estatísticas e assuntos de atuação
- **Detalhe do vereador** — ao selecionar um vereador, exibe matérias, PLOs aprovados e assuntos
- **Filtros combinados** — Assunto, Vereador, Tipo de matéria e Tema visual
- **Links clicáveis** nos gráficos — abrem a pesquisa no SAPL já filtrada por autor, assunto e ano
- **Temas visuais** — Claro, Escuro e Institucional (azul da identidade visual da Câmara)
- **Atualização automática** diária via GitHub Actions

---

## Tecnologias

| Ferramenta | Uso |
|---|---|
| Python 3 | Linguagem principal |
| Streamlit | Framework do painel web |
| Pandas | Manipulação dos dados |
| Plotly | Gráficos interativos |
| Requests | Coleta de dados via API SAPL |
| GitHub Actions | Atualização automática diária |
| Render | Hospedagem (embed no site da Câmara) |
| Streamlit Cloud | Hospedagem (versão pública direta) |

---

## Estrutura do repositório

```
painel-legislativo-itabirito/
├── app.py                      # Painel principal (Streamlit)
├── atualizar_dados.py          # Coleta diária: matérias, normas, assuntos
├── coletar_dados_iniciais.py   # Coleta única: vereadores, autores, mesa
├── requirements.txt            # Dependências Python
├── COMO_PUBLICAR.md            # Guia completo de publicação e manutenção
├── .streamlit/
│   └── config.toml             # Configuração de tema
├── .github/
│   └── workflows/
│       └── atualizar.yml       # GitHub Actions — atualização automática
└── dados/
    ├── vereadores.json
    ├── autores.json
    ├── mesa_diretora.json
    ├── materias.json           # Matérias de 2026 (exibição)
    ├── materias_historico.json # Matérias 2025+2026 (cruzamento com normas)
    ├── normas.json
    ├── assuntos.json
    └── materiaassuntos.json
```

---

## Fonte dos dados

Todos os dados são extraídos da API pública do SAPL de Itabirito:

```
https://sapl.itabirito.mg.leg.br/api/
```

Os dados são atualizados automaticamente todo dia às **03:00 (horário de Brasília)** via GitHub Actions. Em caso de falha na coleta automática, os dados anteriores são preservados (o script não sobrescreve arquivos com resultado vazio).

---

## Regras de negócio

- **PLO → PLS → PLS2:** mesmo número = mesmo projeto. PLS e PLS2 são substitutivos e não contam como projetos separados nos comparativos.
- **Élio da Mata** (Chefe do Executivo) é excluído dos comparativos entre vereadores.
- **Mesa Diretora** aparece como nota informativa, não somada individualmente.
- **Co-autorias** são expandidas em linhas; a contagem usa `nunique()` por `materia_id`.
- O cruzamento de normas usa `materias_historico.json` para capturar PLOs de 2025 aprovados como leis em 2026.

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

# 5. Rode o painel
python -m streamlit run app.py
```

---

## Manutenção

Para publicar uma atualização de código: edite o arquivo desejado e faça commit — o Render e o Streamlit Cloud atualizam automaticamente.

Para atualizar os dados manualmente fora do horário agendado, consulte o arquivo **[COMO_PUBLICAR.md](COMO_PUBLICAR.md)**.

---

*Desenvolvido para a Câmara Municipal de Itabirito (MG) · 2026*
