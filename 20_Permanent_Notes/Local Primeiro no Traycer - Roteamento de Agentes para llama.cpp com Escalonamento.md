---
title: Local Primeiro no Traycer - Roteamento de Agentes para llama.cpp com Escalonamento
type: decision
tags: [traycer, llama-cpp, opencode, routing, local-llm, agents, wsl2]
created: 2026-10-29
provenance: dotfiles
project: dotfiles
verified: 2026-10-29 via artifact de decisão (2026-10-28) e verificação pós wsl --shutdown; smoke test NÃO executado
confidence: low
seen_in: [dotfiles]
---

# Local Primeiro no Traycer - Roteamento de Agentes para llama.cpp com Escalonamento

Decisão do usuário (2026-10-28): a inferência local dos agentes do Traycer roda no `llama.cpp` direto no WSL2, não no Ollama do Windows. Provider `llamacpp` (`127.0.0.1:8080/v1`) no opencode, modelo `gpt-oss-20b` (MXFP4, ~12 GB, 32K de contexto), `-np 1`.

- **Por quê:** `--n-cpu-moe` e `--moe-cache-mib` só existem no `llama-server`.
- **Local primeiro:** implementação de até 3 arquivos, testes, tarefas mecânicas, leitura/docs e revisão de diff até 150 linhas. **Um agente local por vez**; nuvem em paralelo.
- **Escalonar para a nuvem:** 2 falhas seguidas, loop, contexto > 80%, segredo/auth/pagamento/migração/deploy/CI, diff > 150 linhas ou > 3 arquivos, decisão de design, servidor fora por mais de 2 min. **Sempre nuvem:** orquestrador, segunda opinião, revisão de segurança, revisão final de mudança escalonada.
- **Autodesligável:** sem `llamacpp:*` em `traycer_list_harness_models`, a camada local é ignorada. Ele lista `llamacpp:gpt-oss-20b` com `reasoningEffort` low/medium/high.
- **Preflight:** `curl -fsS http://127.0.0.1:8080/health`; se falhar, `pgrep -x llama-server` antes de subir (ver [[llama-server - -ngl 99 e --fit Conflitam com --n-cpu-moe e o Health Dá 503 na Carga]]).
- **Custos aceitos:** WSL2 com 24 GB (`.wslconfig`); Windows e WSL2 disputam a VRAM (o script descarrega o Ollama antes); primeiro start baixa ~12 GB e estoura o gatilho de 2 min.
- **Shell do Traycer é privado do chat:** `traycer_stop_agent` no chat que subiu o servidor mata o `llama-server` e derruba os agentes locais dos outros. Suba num terminal seu ou numa unit `systemd --user`.
- **Revisão local usa o mesmo modelo do autor:** reduz o viés só com agente novo. Por isso a revisão final grande fica na nuvem.

## Hipóteses não medidas
- O orquestrador pode estourar 32K (prompt do Traycer + skills).
- Os limiares (150 linhas, 3 arquivos, 80%, 2 falhas) são chutes. Nenhum tok/s foi medido; o "~20 tok/s" saiu do `local.md`.
- Falta saber se o `opencode/agent/local.md` chega aos agentes opencode que o Traycer cria.

## O que NÃO funcionou
- A recomendação do review de manter a inferência no Windows (A2) foi substituída por esta decisão.
- Primeiro guia com duas regras para testes (uma local, uma nuvem) e revisão local sem filtro de tema sensível: corrigidos após o review.

## 🔗 Conexões
- [[Traycer - Workspace de Agentes em Worktrees Paralelas]]
- [[opencode com Modelo Local Único Residente em GPU de 8 GB]]
- [[CCR - Gateway Local de Modelos para Agentes de Código]]
- [[MoE em GPU de 8 GB - Offload de Experts com llama.cpp]]
