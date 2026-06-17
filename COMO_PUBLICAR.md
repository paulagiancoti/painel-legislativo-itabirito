# Painel Legislativo — Itabirito — Guia de Publicação e Manutenção

Este guia cobre desde a publicação inicial até a manutenção completa do painel,
incluindo como realizar todas as tarefas **sem depender de um computador pessoal**,
usando apenas o navegador.

## Arquivos do projeto

```
painel-legislativo-itabirito/
├── app.py                        # Painel principal (Streamlit)
├── atualizar_dados.py            # Coleta diária: matérias, normas, assuntos
├── atualizar_fotos.py            # Coleta de fotos dos vereadores (manual, sob demanda)
├── coletar_dados_iniciais.py     # Coleta única: vereadores, autores, mesa diretora
├── requirements.txt              # Dependências Python
├── README.md                     # Descrição do projeto para o GitHub
├── COMO_PUBLICAR.md              # Este guia
├── .streamlit/
│   └── config.toml               # Configuração do Streamlit
├── .github/
│   └── workflows/
│       ├── atualizar.yml         # Atualização automática diária dos dados
│       └── atualizar_fotos.yml   # Atualização de fotos (manual)
├── static/
│   └── fotos/                    # Fotos dos vereadores (baixadas do SAPL)
└── dados/
    ├── vereadores.json
    ├── autores.json
    ├── mesa_diretora.json
    ├── materias.json
    ├── materias_historico.json
    ├── normas.json
    ├── assuntos.json
    ├── materiaassuntos.json
    └── ultima_atualizacao.json   # Timestamp da última coleta
```

---

## PUBLICAÇÃO INICIAL

### PASSO 1 — Criar conta no GitHub

https://github.com → "Sign up" (gratuito).

Certifique-se de que as **notificações de e-mail para Actions** estão ativas:
GitHub → foto de perfil → **Settings → Notifications → Actions →
marcar "Email" em "Failed workflows only"**.
Assim você recebe e-mail quando a atualização automática falhar.

---

### PASSO 2 — Criar o repositório

1. Clique em **"New repository"**
2. Nome: `painel-legislativo-itabirito`
3. Marque **"Public"**
4. **NÃO** marque "Add a README"
5. Clique em **"Create repository"**

---

### PASSO 3 — Coletar os dados pela primeira vez

Esta etapa é feita **uma única vez** para popular a pasta `dados/`.
Use um PC com Python instalado, ou o **GitHub Codespaces** (veja seção abaixo).

**No PC** (com ambiente virtual ativado):
```
python -m venv .venv
& ".venv\Scripts\Activate.ps1"
pip install requests
python coletar_dados_iniciais.py
python atualizar_dados.py
```

**No GitHub Codespaces** (sem PC, direto no navegador):
1. No repositório → botão verde **"Code"** → aba **"Codespaces"** → **"Create codespace on main"**
2. Aguarde o ambiente abrir (~1 minuto)
3. No terminal do Codespace:
```
pip install requests
python coletar_dados_iniciais.py
python atualizar_dados.py
git add dados/
git commit -m "Coleta inicial dos dados"
git push
```

Confira se `dados/vereadores.json` tem só os 15 vereadores ativos.

---

### PASSO 4 — Subir os arquivos para o GitHub

Use o **GitHub Desktop** (https://desktop.github.com) — o upload pelo
navegador não funciona bem com pastas ocultas (`.streamlit`, `.github`).

1. Instale e faça login com sua conta GitHub
2. **File → Clone repository** → selecione o repositório → escolha uma pasta local
3. Copie todos os arquivos do projeto para dentro da pasta clonada
   - Inclua `.streamlit/`, `.github/`, `dados/`, `static/`
   - **Não copie** a pasta `.venv`
4. No GitHub Desktop, escreva "Versão inicial" e clique em **"Commit to main"**
5. Clique em **"Push origin"**

> **Dica:** para ver pastas ocultas no Windows Explorer, vá em
> **Exibir → Itens ocultos**.

Se já tiver o repositório clonado, basta copiar os arquivos novos/alterados
para a pasta clonada e repetir os passos 4 e 5.

---

### PASSO 5 — Publicar no Render (hospedagem principal)

O Render hospeda o painel em servidor real, permitindo uso em iframe no site da Câmara.

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

Após 3-5 minutos a URL estará disponível:
```
https://painel-legislativo-itabirito.onrender.com
```

**URL para o "Adicionar Window" do site da Câmara:**
```
https://painel-legislativo-itabirito.onrender.com/?embed=true
```

---

### PASSO 6 — Publicar no Streamlit Cloud (versão pública direta)

1. Acesse https://share.streamlit.io → "Sign up" → "Continue with GitHub"
2. Clique em **"New app"**
3. Selecione o repositório, branch `main`, arquivo `app.py`
4. Clique em **"Deploy"**

URL gerada:
```
https://painel-legislativo-itabirito.streamlit.app
```

O título do painel tem um link ↗ que redireciona para esta URL.

---

### PASSO 7 — Configurar o "Adicionar Window" no site da Câmara

No portal Interlegis/Plone, ao adicionar o Window:

- **URL:** `https://painel-legislativo-itabirito.onrender.com/?embed=true`
- **Page Width:** `100%`
- **Page Height:** `2500px` ← sempre em pixels, nunca em %
- Marcar **"Hide Metadata?"**

> O Streamlit Cloud não pode ser usado em iframe (bloqueia por política de segurança).
> Por isso o Render é usado no site. O Streamlit é o link direto para o público.

**Descrição sugerida para a página:**
> Painel interativo com dados das proposições e atividade legislativa dos vereadores
> de Itabirito em 2026, extraídos automaticamente do SAPL. Para acesso completo e
> mais ágil, utilize o link direto: https://painel-legislativo-itabirito.streamlit.app

---

### PASSO 8 — Manter os serviços acordados (cron-job.org)

- **Render:** hiberna após ~15 minutos sem acesso
- **Streamlit Cloud:** hiberna após ~12 horas sem acesso

Configure pings automáticos em https://cron-job.org (gratuito, sem cartão):

1. Crie uma conta
2. Crie o primeiro job:
   - **URL:** `https://painel-legislativo-itabirito.onrender.com`
   - **Intervalo:** a cada **14 minutos**
3. Crie o segundo job:
   - **URL:** `https://painel-legislativo-itabirito.streamlit.app`
   - **Intervalo:** a cada **6 horas**

> Um ping HTTP simples não acorda o Streamlit Cloud de verdade.
> Os acessos diários dos usuários durante o dia são suficientes para mantê-lo ativo.
> O ping do cron-job é especialmente importante para o Render.

---

### PASSO 9 — Baixar as fotos dos vereadores

As fotos ficam hospedadas no repositório (não dependem do SAPL).
Para baixar pela primeira vez, rode o workflow manualmente:

1. GitHub → aba **"Actions"** → **"Atualizar fotos dos vereadores"**
2. Botão **"Run workflow"** → **"Run workflow"**
3. Aguarde ~1 minuto — as fotos são salvas em `static/fotos/`

---

## MANUTENÇÃO DO DIA A DIA

### Atualização automática dos dados

O workflow `atualizar.yml` roda todo dia à **1h UTC (22h Brasília da véspera)**,
baixa dados novos do SAPL e commita os JSONs atualizados. O Render e o Streamlit
detectam a mudança e recarregam automaticamente.

Verifique na aba **"Actions"** do GitHub:
- ✅ verde = funcionou
- ❌ vermelho = falhou → você receberá e-mail automático

### Atualização manual dos dados

**Pelo GitHub Actions (mais simples):**
1. GitHub → aba **"Actions"** → **"Atualizar dados SAPL"**
2. **"Run workflow"** → **"Run workflow"**
3. Aguarde ~2 minutos

**Pelo GitHub Codespaces (se o Actions falhar):**
1. Repositório → botão verde **"Code"** → aba **"Codespaces"** → **"Create codespace on main"**
2. No terminal:
```
pip install requests
python atualizar_dados.py
git add dados/
git commit -m "Atualização manual dos dados"
git push
```

### Atualizar fotos de vereadores

Quando um vereador atualizar a foto no SAPL:

1. GitHub → aba **"Actions"** → **"Atualizar fotos dos vereadores"**
2. **"Run workflow"** → **"Run workflow"**

Pronto — sem precisar de PC.

### Novo vereador ou mudança na mesa diretora

Se entrar um vereador novo ou a composição da mesa mudar,
rode o `coletar_dados_iniciais.py` pelo Codespaces:

1. Repositório → botão **"Code"** → **"Codespaces"** → **"Create codespace on main"**
2. No terminal:
```
pip install requests
python coletar_dados_iniciais.py
git add dados/vereadores.json dados/autores.json dados/mesa_diretora.json
git commit -m "Atualização de vereadores/mesa diretora"
git push
```

### Editar o código do painel

**Edições simples** (uma linha, um parâmetro):
- GitHub → clique no arquivo `app.py` → ícone de lápis → edite → "Commit changes"
- O Render e o Streamlit atualizam sozinhos em ~1 minuto

**Edições maiores:**
- Use o **GitHub Codespaces** (terminal + editor completo no navegador)
- Ou edite localmente e suba via GitHub Desktop

---

## Como tudo se conecta

```
GitHub Actions (todo dia, 22h Brasília)
   |  roda atualizar_dados.py
   |  baixa dados novos do SAPL
   |  commita os JSONs atualizados
        |
Render e Streamlit Cloud detectam a mudança
   |  recarregam o app automaticamente
   |  cache é invalidado (timestamp novo = dados novos imediatos)
        |
Site da Câmara (iframe via Window do Plone)
   |  exibe o Render com ?embed=true
   |  título clicável leva ao Streamlit
        |
cron-job.org pinga o Render a cada 14min
   |  mantém o servidor acordado 24/7

Fotos dos vereadores
   |  hospedadas em static/fotos/ no repositório
   |  não dependem do SAPL para carregar
   |  atualizadas manualmente via workflow quando necessário
```

---

## Solução de problemas comuns

| Sintoma | Causa provável | Solução |
|---|---|---|
| Painel lento no site | Render hibernado | Verificar cron-job.org |
| Painel não abre no site | URL sem `?embed=true` ou altura em `%` | Corrigir o Window no Plone |
| Dados desatualizados | Workflow falhou | Verificar Actions, rodar manualmente |
| Fotos quebradas | Workflow de fotos não rodou | Actions → "Atualizar fotos" → Run |
| Cache desatualizado | Não deve ocorrer | O timestamp invalida o cache automaticamente |
| E-mail de falha | Coleta falhou no SAPL | Dados anteriores preservados; rodar manual |
| Streamlit dormindo | Pouco tráfego | Aceitar ou configurar Playwright (avançado) |
