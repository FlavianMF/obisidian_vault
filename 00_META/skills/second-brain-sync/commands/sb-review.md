---
description: Abre a interface web de triagem de candidatos do Second Brain (/sb-review)
---

# /sb-review - Revisão Web do Second Brain

Alias para o comando `/review-web`.

Inicia o servidor web interativo local (`sb review web`) para triagem de candidatos acumulados na fila (`~/.local/state/second-brain/queue.jsonl`).

## Procedimento para o Harness / Agente

1. **Verificar servidor ativo:** `curl -s http://127.0.0.1:8000/api/stats`
2. **Iniciar se inativo:**
   ```bash
   python3 ~/obsidian_vault/00_META/skills/second-brain-sync/scripts/sb.py review web --port 8000
   ```
3. **Responder com o link:** `http://127.0.0.1:8000/` e status da fila (`GET /api/stats`).
