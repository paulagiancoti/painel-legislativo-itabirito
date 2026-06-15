# Painel Legislativo — Itabirito — Guia de Publicação

Este guia parte do zero: você tem os arquivos do projeto e quer o painel
online, atualizado automaticamente, sem depender do seu computador.

## Arquivos necessários

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
└── dados/                  ← criado pelos scripts de coleta
```

---

## PASSO 1 — Coletar os dados (uma única vez, no seu PC)

Abra o terminal na pasta do projeto e ative o ambiente virtual:

```
python -m venv .venv
& ".venv\Scripts\Activate.ps1"
```

Se aparecer erro de política de execução, rode antes:
```
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Com o `(.venv)` aparecendo no terminal, instale as dependências e colete os dados:

```
pip install streamlit pandas plotly requests openpyxl
python coletar_dados_iniciais.py
python atualizar_dados.py
```

Isso cria a pasta `dados/` com todos os JSONs. Confira se
`dados/vereadores.json` tem só os 15 vereadores ativos.

> **Atenção:** sempre que precisar atualizar os dados manualmente,
> ative o `.venv` primeiro (`& ".venv\Scripts\Activate.ps1"`) e depois
> rode `python atualizar_dados.py`. Se der `ModuleNotFoundError`, é sinal
> que o ambiente não está ativado.

---

## PASSO 2 — Criar conta no GitHub

Se ainda não tiver: https://github.com → "Sign up" (gratuito).

---

## PASSO 3 — Criar o repositório

1. Clique em **"New repository"**
2. Nome: `painel-legislativo-itabirito`
3. Marque **"Public"**
4. **NÃO** marque "Add a README"
5. Clique em **"Create repository"**

---

## PASSO 4 — Subir os arquivos (via GitHub Desktop)

O upload pelo navegador não funciona bem com pastas ocultas (`.streamlit`, `.github`).
Use o **GitHub Desktop** (https://desktop.github.com):

1. Instale e faça login com sua conta GitHub
2. **File → Clone repository** → selecione `painel-legislativo-itabirito` → escolha uma pasta local
3. Copie todos os arquivos do projeto para dentro da pasta clonada
   - Inclua as pastas `.streamlit/`, `.github/` e `dados/`
   - **Não copie** a pasta `.venv`
4. No GitHub Desktop, escreva uma mensagem ("Versão inicial") e clique em **"Commit to main"**
5. Clique em **"Push origin"**

> **Dica:** para ver as pastas ocultas no Windows Explorer, vá em
> **Exibir → Itens ocultos**.

---

## PASSO 5 — Publicar no Render (hospedagem principal)

O Render hospeda o painel em um servidor real, permitindo uso em iframe no site da Câmara.

1. Acesse https://render.com → "Get Started for Free" → entre com GitHub
2. Clique em **"New +"** → **"Web Service"**
3. Conecte o repositório `painel-legislativo-itabirito`
4. Preencha:
   - **Name:** `painel-legislativo-itabirito`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
   - **Instance Type:** Free
5. Clique em **"Create Web Service"**

Após 3-5 minutos, a URL estará disponível:
```
https://painel-legislativo-itabirito.onrender.com
```

**Essa é a URL para colocar no "Adicionar Window" do site da Câmara:**
```
https://painel-legislativo-itabirito.onrender.com/?embed=true
```

---

## PASSO 6 — Publicar no Streamlit Cloud (backup / versão completa)

O Streamlit Cloud oferece uma versão com melhor desempenho, acessível por link direto.

1. Acesse https://share.streamlit.io → "Sign up" → "Continue with GitHub"
2. Clique em **"New app"**
3. Selecione o repositório, branch `main`, arquivo `app.py`
4. Clique em **"Deploy"**

URL gerada:
```
https://painel-legislativo-itabirito.streamlit.app
```

O título do painel tem um link ↗ que redireciona para esta URL (versão mais rápida).

---

## PASSO 7 — Configurar o "Adicionar Window" no site da Câmara

No portal Interlegis/Plone, ao adicionar o Window:

- **URL:** `https://painel-legislativo-itabirito.onrender.com/?embed=true`
- **Page Width:** 
- **Page Height:** `1800`
- Marcar **"Hide Metadata?"**

> O Streamlit Cloud não pode ser usado em iframe diretamente (bloqueia por política
> de segurança). Por isso o Render é usado como hospedagem do iframe.

---

## PASSO 8 — Manter os serviços acordados (cron-job.org)

Ambos os serviços hibernam por inatividade:
- **Render (gratuito):** hiberna após ~15 minutos sem acesso
- **Streamlit Cloud (gratuito):** hiberna após ~12 horas sem acesso

Para evitar isso, configure pings automáticos em https://cron-job.org (gratuito):

1. Crie uma conta em https://cron-job.org
2. Crie o primeiro job:
   - **URL:** `https://painel-legislativo-itabirito.onrender.com`
   - **Intervalo:** a cada **14 minutos**
3. Crie o segundo job:
   - **URL:** `https://painel-legislativo-itabirito.streamlit.app`
   - **Intervalo:** a cada **6 horas**

> **Atenção:** um ping HTTP simples não acorda o Streamlit Cloud — ele precisa
> de uma visita real no navegador. Os acessos diários dos usuários no site da
> Câmara durante o horário comercial são suficientes para mantê-lo ativo.
> O ping via cron-job serve principalmente para o Render.

---

## PASSO 9 — Atualização automática dos dados (GitHub Actions)

O arquivo `.github/workflows/atualizar.yml` roda automaticamente todo dia
às **03:00 da manhã (horário de Brasília)**, baixa os dados do SAPL e
comita os JSONs atualizados no repositório. O Render e o Streamlit
detectam a mudança e recarregam o app.

Para verificar se está funcionando:
1. No repositório GitHub → aba **"Actions"**
2. O workflow **"Atualizar dados SAPL"** deve aparecer com ✅ verde

Se aparecer ❌ vermelho, clique no workflow para ver o erro.

### Atualização manual dos dados

Se precisar atualizar fora do horário automático:

**Opção 1 — Pelo GitHub (mais fácil):**
1. Repositório → aba **"Actions"** → **"Atualizar dados SAPL"**
2. Botão **"Run workflow"** → **"Run workflow"**
3. Aguarde ~5 minutos e verifique se os JSONs em `dados/` foram atualizados

**Opção 2 — Pelo seu PC (mais confiável se o Actions falhar):**
1. Ative o ambiente: `& ".venv\Scripts\Activate.ps1"`
2. Rode: `python atualizar_dados.py`
3. Abra o **GitHub Desktop**, faça commit dos arquivos `dados/*.json` atualizados e Push

> **Problema conhecido:** o GitHub Actions pode falhar na coleta se o servidor
> do SAPL bloquear os IPs do GitHub. Nesse caso, a Opção 2 é a mais confiável.
> O script não sobrescreve os dados se a coleta vier vazia — os dados anteriores
> ficam preservados.

---

## Como tudo se conecta

```
GitHub Actions (todo dia, 03h)
   |  roda atualizar_dados.py
   |  baixa dados novos do SAPL
   |  comita os JSONs atualizados
        |
Render e Streamlit Cloud detectam a mudança
   |  recarregam o app automaticamente
   |  painel exibe dados atualizados (cache renova a cada 1h)
        |
Site da Câmara (iframe via Window do Plone)
   |  exibe o Render embedado com ?embed=true
   |  título clicável leva ao Streamlit (versão mais rápida)
        |
cron-job.org pinga o Render a cada 14min
   |  mantém o servidor acordado 24/7
```

---

## Manutenção futura

- **Atualizar o código** (`app.py`): edite no GitHub (ícone de lápis) ou
  suba nova versão via GitHub Desktop. O Render e Streamlit atualizam sozinhos.
- **Dados desatualizados:** verifique a aba "Actions" do GitHub — erro em
  vermelho indica falha na coleta. Rode a atualização manual pelo PC.
- **Mudar o horário da atualização automática:** edite a linha `cron` em
  `.github/workflows/atualizar.yml`. Formato: `minuto hora * * *` em UTC
  (Brasília = UTC-3, então 03h Brasília = 06h UTC = `0 6 * * *`).
- **Painel lento no site:** o Render pode estar hibernado. Verifique se o
  cron-job.org está ativo e pingando corretamente.
- **Painel não abre no site:** verifique se a URL no Window do Plone tem
  `?embed=true` e se o Page Height está em pixels (ex: `2500px`), não em `%`.
