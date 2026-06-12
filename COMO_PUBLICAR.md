# Painel Legislativo — Itabirito — Guia de Publicação

Este guia parte do zero: você tem só os arquivos abaixo e quer o painel
online, atualizado automaticamente, sem depender do seu computador.

## Arquivos que você deve ter nesta pasta

```
painel_legislativo/
├── app.py
├── atualizar_dados.py
├── coletar_dados_iniciais.py
├── requirements.txt
├── .streamlit/
│   └── config.toml
├── .github/
│   └── workflows/
│       └── atualizar.yml
└── dados/                  ← será criado pelos scripts
```

---

## PASSO 1 — Coletar os dados (uma única vez, no seu PC)

Ainda no seu computador, com o ambiente virtual ativado:


```
python -m venv .venv
& ".venv\Scripts\Activate.ps1"
pip install requests
python coletar_dados_iniciais.py
python atualizar_dados.py
```

Isso cria a pasta `dados/` com todos os JSONs necessários. Confira se
`dados/vereadores.json` tem só os 15 vereadores ativos — se vier algo
diferente, me avise que ajustamos o filtro.

---

## PASSO 2 — Criar conta no GitHub

Se ainda não tiver: https://github.com → "Sign up" (gratuito).

---

## PASSO 3 — Criar o repositório

1. No GitHub, clique em **"New repository"** (botão verde, canto superior direito)
2. Nome: `painel-legislativo-itabirito` (ou o que preferir)
3. Marque **"Public"** (necessário para o plano gratuito do Streamlit Cloud)
4. **NÃO** marque "Add a README" (vamos subir os arquivos já existentes)
5. Clique em **"Create repository"**

---

## PASSO 4 — Subir os arquivos para o GitHub

Na página do repositório recém-criado, você verá um link
**"uploading an existing file"**. Clique nele.

Arraste para a área de upload **todos os arquivos e pastas**:
- `app.py`
- `atualizar_dados.py`
- `coletar_dados_iniciais.py`
- `requirements.txt`
- a pasta `.streamlit/` (com `config.toml` dentro)
- a pasta `dados/` (com todos os JSONs)
- a pasta `.github/` (com `workflows/atualizar.yml` dentro)

> **Dica:** o GitHub às vezes não aceita arrastar pastas vazias ou
> estrutura de pastas direto pelo navegador. Se tiver dificuldade,
> arraste os arquivos um por um mantendo os caminhos
> (`.streamlit/config.toml`, `.github/workflows/atualizar.yml`, etc.)
> — o GitHub recria as pastas automaticamente a partir do caminho do arquivo.

Role para baixo, escreva uma mensagem como "Versão inicial" e clique em
**"Commit changes"**.

---

## PASSO 5 — Criar conta no Streamlit Community Cloud

1. Acesse https://share.streamlit.io
2. Clique em **"Sign up"** → **"Continue with GitHub"**
3. Autorize o acesso do Streamlit ao GitHub

---

## PASSO 6 — Publicar o app (Deploy)

1. No Streamlit Cloud, clique em **"New app"**
2. **Repository:** selecione `seu-usuario/painel-legislativo-itabirito`
3. **Branch:** `main`
4. **Main file path:** `app.py`
5. Clique em **"Deploy"**

Aguarde 1-2 minutos. O Streamlit vai instalar as dependências do
`requirements.txt` e iniciar o app. Você receberá uma URL assim:

```
https://painel-legislativo-itabirito.streamlit.app
```

Essa é a URL que você usa no campo **URL** do "Adicionar Window" no site
da Câmara.

---

## PASSO 7 — Ativar a atualização automática diária

O arquivo `.github/workflows/atualizar.yml` já está configurado para
rodar todos os dias às 3h da manhã (horário de Brasília) e atualizar os
dados automaticamente. **Não precisa fazer nada** — o GitHub Actions já
vem habilitado por padrão em repositórios públicos.

Para confirmar que está ativo:
1. No repositório, clique na aba **"Actions"**
2. Você verá o workflow **"Atualizar dados SAPL"** listado
3. Se aparecer um aviso pedindo para habilitar workflows, clique no botão
   verde para habilitar

### Testar manualmente (opcional)

Na aba "Actions" → clique em "Atualizar dados SAPL" →
**"Run workflow"** → "Run workflow". Em ~1 minuto, confira se os
arquivos em `dados/` foram atualizados (aba "Code" do repositório).

---

## Como tudo se conecta

```
GitHub Actions (todo dia, 3h)
   |  roda atualizar_dados.py
   |  baixa dados novos do SAPL
   |  comita os JSONs atualizados no repositorio
        |
Streamlit Cloud detecta a mudanca no repositorio
   |  reinicia o app automaticamente
   |  painel exibe dados atualizados (cache renova a cada 1h tambem)
        |
Site da Camara (via "Window"/iframe) sempre mostra a versao mais recente
```

---

## Manutenção futura

- **Mudar o código do painel** (`app.py`): edite o arquivo no GitHub
  (clique no arquivo → ícone de lápis "Edit") ou suba uma nova versão.
  O Streamlit Cloud atualiza automaticamente.
- **Os dados não atualizam:** verifique a aba "Actions" do GitHub —
  se o workflow estiver falhando, ele mostra o erro em vermelho.
- **Mudar o horário da atualização:** edite o `cron` em
  `.github/workflows/atualizar.yml`. Formato: `minuto hora dia mes dia-semana`,
  sempre em UTC (Brasília = UTC-3).
