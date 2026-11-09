---
title: Playbook - Sincronização de Hosts Traycer e Workspaces em VPS
type: meta
tags: [traycer, devops, playbook, vps, outlet_promo, automation]
created: 2026-11-03
provenance: traycer-obisidian-vault-visual
seen_in: [srv1184210, loq-wsl2-flv]
verified: 2026-11-03
confidence: high
---

# Playbook - Sincronização de Hosts Traycer e Workspaces em VPS

Guia prático operacional para provisionar e manter um ambiente Traycer Host em servidores Linux remotos (VPS), garantindo continuidade operacional de agentes em segundo plano.

---

## 1. Contexto e Ambiente

* **Host Local:** `loq-wsl2-flv` (WSL2 Ubuntu 24.04).
* **Host Remoto (VPS):** `srv1184210` (Ubuntu 24.04 via alias SSH `ssh vps`).
* **Conta de Autenticação:** `flavianmelquiades@gmail.com`.
* **Workspace Foco:** `/home/flv/projetos_apps/outlet_promo`.

---

## 2. O Script de Automação: `sync-to-vps.sh`

O script está versionado localmente em `/home/flv/sync-to-vps.sh`.

### 2.1. Como Executar
```bash
# Execução padrão contra o alias 'vps':
/home/flv/sync-to-vps.sh

# Simulação sem alterações (Dry-Run):
/home/flv/sync-to-vps.sh --dry-run

# Execução contra outro host específico:
/home/flv/sync-to-vps.sh usuario@meu-outro-ip
```

### 2.2. O que o script realiza em cada etapa:
1. **Conectividade:** Testa ping e autenticação SSH com timeout de segurança.
2. **Traycer CLI:** Carrega o NVM da VPS, instala `@traycerai/cli` caso ausente e cria link simbólico em `~/.local/bin/traycer`.
3. **Guia de Agentes (`agent-selection-guide.md`):** Transforma dinamicamente o arquivo local via Python para remover menções a `llama-server`, atribuir `claude haiku (low)` a operações git e remover rotinas de economia de energia (`pc-ctl schedule-sleep`).
4. **Credenciais de Harness:** Envia `~/.claude/.credentials.json` com `chmod 600`.
5. **Repositório Git (`outlet_promo`):** Executa `git fetch origin`, faz checkout de `develop` e atualiza para o commit mais recente (`origin/develop`).
6. **Health Check do Host:** Valida a presença de credencial do Host e o estado do serviço systemd.

---

## 3. Armadilhas Encontradas e Soluções (Troubleshooting)

### A. Erro `PATH_POLICY_REFUSED` em Execução Remota
* **Causa:** O Traycer Host remoto restringe a execução de comandos via Relay (`traycer_run_remote_command`) apenas a caminhos registrados como workspace, worktrees gerenciados ou o scratch da task.
* **Solução:** Adicionar o repositório em `~/.traycer/recent-workspaces-v2.json` e reiniciar o host com `traycer host restart` ou abrir o workspace no app Traycer Desktop conectado à VPS.

### B. Alerta `HOST_CREDENTIAL_MISSING` após `traycer login`
* **Causa:** O primeiro login na CLI autentica a ferramenta, mas o daemon do Host precisa de uma concessão específica de "host credential".
* **Solução:** Rodar `traycer login` enquanto o host está rodando. Ele utiliza o fluxo OAuth Device Authorization (`https://traycer.ai/device?user_code=...`) e ao ser aprovado imprime: `Signed in. Host authorized.`

### C. Serviço derrubado ao desconectar do SSH
* **Causa:** Por padrão, o systemd encerra sessões de usuário (`systemd --user`) quando todas as conexões do usuário terminam.
* **Solução:** Ativar linger no Linux da VPS:
  ```bash
  sudo loginctl enable-linger $USER
  ```
  Isso mantém o `ai.traycer.host.service` ativo indefinidamente.

---

## 4. Verificação Rápida de Sanidade na VPS

```bash
# Verificar status do serviço
ssh vps "systemctl --user is-active ai.traycer.host"

# Checar processo do host e supervisor
ssh vps "traycer host status"

# Checar agentes em execução
ssh vps "ps aux | grep -E 'traycer|claude' | grep -v grep"
```
