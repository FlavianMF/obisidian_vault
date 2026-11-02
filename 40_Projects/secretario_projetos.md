---
title: Projeto Secretário de Projetos e Dashboard
type: project
tags: [project, agentic-ai, traycer, second-brain, dashboard, tailscale]
created: 2026-11-02
provenance: dotfiles
confidence: low
verified: 2026-11-02 via leitura de sb.py, web_service.py e traycer CLI
status: active
scope: project
fase: planejamento
prioridade: P1
proximo_passo: Rodar a Sprint 01 (spike do ambiente)
bloqueio:
traycer_task: e1da89de-b22a-4569-b86c-52fa24ae8538
---

# Projeto Secretário de Projetos e Dashboard

Nota-ponteiro. O plano completo vive no épico Traycer `e1da89de`, artifact `secretario-projetos-plano` (14 sprints).

## Objetivo

Controlar as sessões Traycer à distância e manter sempre um projeto em desenvolvimento. O vault guarda o status de 5 a 8 projetos curados. Uma sessão "Secretário" lê o status, sugere o trabalho e despacha depois da aprovação.

## Decisões

- Dados: o manifesto `00_META/projects/manifest.yaml` é a lista curada. A nota de cada projeto guarda só campos humanos: `status`, `fase`, `prioridade`, `proximo_passo`, `bloqueio`, `traycer_task`.
- O coletor `sb projects scan` grava só `~/.local/state/second-brain/projects.json`. O `vault_sync.py` continua o único escritor do vault.
- `status` mantém o enum do schema. A "situação" do dashboard é derivada.
- Autenticação: `tailscale serve` em HTTPS, app em loopback, token de 32 bytes. Bearer para CLI e voz. Cookie `HttpOnly` `SameSite=Strict` para o celular.
- Privacidade: o `sb doctor` checa segredo, PII (e-mail, telefone, CPF, CNPJ), allowlist de chaves, nomes de variável e a `jev-denylist`.
- Trava: `sb projects gate` é determinístico e falha fechado. Ele exige quota livre de 30% ou mais, no máximo 2 implementadores e snapshot de atividade recente.
- Quota sem MCP: `traycer agent profile-rate-limits <harness> --profile ambient`.

## Armadilhas encontradas no planejamento

- O schema reserva `path`. O caminho do repo se chama `checkout`.
- Agentes ativos em todas as Tasks só aparecem via MCP (`traycer_list_tasks`). O Secretário grava o snapshot.
- Botão no celular não envia header customizado. Por isso o navegador usa cookie.

## Dependências

- `pc-ctl schedule-sleep` (Autobuild Sprint 07) para dormir com quota esgotada.
