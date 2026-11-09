---
title: Traycer - Arquitetura Multi-Host e Sincronização Remota Headless (VPS)
type: concept
tags: [agentic-ai, traycer, multi-host, remote-execution, vps, devops, orchestration]
created: 2026-11-03
provenance: traycer-obisidian-vault-visual
seen_in: [srv1184210, loq-wsl2-flv]
verified: 2026-11-03 via teste de relay e execução remota comprovada
confidence: high
---

# Traycer - Arquitetura Multi-Host e Sincronização Remota Headless (VPS)

Documentação do modelo de execução distribuída do **Traycer**, permitindo que agentes de IA operem de forma autônoma e coordenada entre máquinas locais (desktops/laptops/WSL2) e servidores remotos (VPS/Cloud).

Conecta-se com [[Traycer - Workspace de Agentes em Worktrees Paralelas]] e [[Local Primeiro no Traycer - Roteamento de Agentes para llama.cpp com Escalonamento]].

---

## 1. Como Funciona a Arquitetura Multi-Host

Diferente de soluções que dependem de SSH interativo contínuo, o Traycer opera em um modelo **Peer-to-Cloud-Relay**:

1. **Host Daemon (`traycer host`):**
   - Cada máquina cadastrada roda um daemon em segundo plano (`traycer-host` + supervisor de ciclo de vida).
   - O daemon estabelece conexão segura de saída via WebSocket com o *Traycer Cloud Relay* (`ws://127.0.0.1:<port>/rpc` local conectado a `authn.traycer.ai` e à nuvem).
   - **Identidade Única:** Cada host possui um `host-id` (`~/.traycer/host-id`) e um `machine-id` exclusivos.
   - ⚠️ **Importante:** Jamais fazer cópia indiscriminada (`rsync`) de toda a pasta `~/.traycer` de uma máquina para outra, pois duplicações de `host-id`, `machine-id` e sockets travam o roteamento no relay.

2. **Tasks (Epics) Unificadas:**
   - As Tasks (Epics) e seus artefatos residem na nuvem e sincronizam entre os hosts autorizados sob o mesmo usuário (`flavianmelquiades@gmail.com`).
   - Múltiplos agentes podem atuar na mesma Task rodando em hosts diferentes (ex.: um agente de arquitetura no Desktop WSL2 e um agente de execução/testes pesados na VPS).

3. **Isolamento de Workspaces e Worktrees:**
   - O Host gerencia localmente seus repositórios e branches dedicadas (via `git worktree` em `~/.traycer/worktrees/<owner>__<repo>/<branch-name>`).
   - A política de segurança (`PATH_POLICY`) do Host restringe a execução remota exclusivamente a workspaces registrados, worktrees de tarefas e ao diretório de scratch da Epic.

---

## 2. Passo a Passo de Setup em VPS Headless (Linux)

### 2.1. Pré-Requisitos na VPS
- Node.js 22.13+ (suportado via NVM ou binário nativo).
- `git`, `build-essential`.
- Persistência do systemd de usuário (Linger):
  ```bash
  sudo loginctl enable-linger $USER
  ```
  *Garante que o serviço de usuário systemd permaneça ativo mesmo após o logout do SSH.*

### 2.2. Instalação da CLI e Host
```bash
# Instalação global do pacote CLI
npm install -g @traycerai/cli

# Link no PATH de usuário
ln -sf $(which traycer) ~/.local/bin/traycer

# Autenticação via Device Flow (OAuth 2.0 Device Authorization)
traycer login
# Abrir o link fornecido no terminal e confirmar o código de ativação na web

# Inicialização e registro do serviço de background systemd
traycer host ensure
```

### 2.3. Diagnóstico e Verificação
```bash
# Status do daemon e supervisor
traycer host status

# Verificação completa de sanidade
traycer host doctor
```

---

## 3. Adaptação de Políticas de Modelos (Sem Modelos Locais na VPS)

Quando a máquina remota não possui GPU ou não executará um servidor local (`llama-server` / `ollama`), as diretrizes de `agent-selection-guide.md` devem ser ajustadas:
- **Git Operations:** O fallback com consumo mínimo de cota é `claude haiku (low)`.
- **Orquestração e Arquitetura:** `claude sonnet (medium)` ou `claude opus (high)` no pool Pro.
- **Implementação:** `claude sonnet (high)`.
- **Review:** `antigravity claude-opus-5.5 (high)` ou `gemini-3.8-flash (medium)`.

---

## 4. Script Idempotente de Sincronização

Foi homologado o script de automação em `/home/flv/sync-to-vps.sh` no WSL2, permitindo transferir com um comando:
1. Validação de alias SSH (`ssh vps`).
2. Instalação e atualização da CLI remota.
3. Adaptação automatizada de `agent-selection-guide.md` (removendo dependências do Llama e rotinas de sleep/wake específicas de desktop).
4. Sincronização de credenciais de harness (`~/.claude/.credentials.json`).
5. Sincronização e alinhamento do repositório Git do projeto (`outlet_promo` em `develop`).
