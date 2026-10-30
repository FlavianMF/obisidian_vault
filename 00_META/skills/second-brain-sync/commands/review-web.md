---
description: Inicia a interface web local para triagem interativa de candidatos do Second Brain (/review-web)
---

# /review-web - Revisão Web de Candidatos do Second Brain

Inicia o servidor web interativo local (`sb review web`) para triagem de candidatos acumulados na fila (`~/.local/state/second-brain/queue.jsonl`).

## Procedimento para o Harness / Agente

1. **Verificar se o servidor já está ativo:**
   Execute uma checagem rápida (ex: `curl -s http://127.0.0.1:8000/api/stats` ou `lsof -i :8000`).
   - Se responder status 200, use a instância existente.
   - Se a porta 8000 estiver ocupada por outro processo ou indisponível, use `--port 8765`.

2. **Iniciar o servidor em background (se não estiver rodando):**
   Inicie em segundo plano (processo em background ou persistent shell):
   ```bash
   python3 ~/obsidian_vault/00_META/skills/second-brain-sync/scripts/sb.py review web --port 8000
   ```
   *(O comando abre o navegador padrão automaticamente em `http://127.0.0.1:8000/`)*.

3. **Consultar estado da fila:**
   Chame `GET /api/stats` para obter as métricas da fila:
   - `pending`: total de candidatos pendentes.
   - `today_applied`: notas aprovadas na data de hoje.
   - `today_rejected`: candidatos descartados na data de hoje.

4. **Responder ao Usuário:**
   Apresente o link de acesso direto e os controles de teclado (modo *Operate*):
   - **URL Local**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
   - **Total Pendente**: `<pending>` candidatos aguardando triagem.
   - **Atalhos no Navegador**:
     - `S` - Salvar como nova nota (validação de segredos e seção negativa automática)
     - `A` - Absorver na nota existente mais similar (atualiza `seen_in` e renova `verified:`)
     - `D` - Descartar com justificativa (`Ctrl+Enter` confirma, `Esc` cancela)
     - `P` - Pular candidato (move para o final da fila)
     - `E` - Abrir Drawer de edição in-browser (com validação inline `dry_run`)
     - `Z` - Desfazer última ação (reverte commit git e restaura fila/rascunho)
     - `J` / `K` - Navegar próximo / anterior
     - Filtros no topo por **Projeto** e por **Tipo** (`trap`, `pattern`, `decision`, `concept`).
