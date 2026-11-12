---
title: "CLAUDE_CODE_EFFORT_LEVEL anula effort de subagentes"
type: permanent
created: 2026-11-10T14:58:34
moc: "Design de Interface com Agente"
tags: [claudie, code, effort, subagentes]
source_inbox: "6e06b617-claude-code-effort-level-anula-effort-de-subagentes.md"
tier: "L2"
score: 0.789
---

# CLAUDE_CODE_EFFORT_LEVEL anula effort de subagentes

No Claude Code, a env CLAUDE_CODE_EFFORT_LEVEL vence o effort do frontmatter e o parâmetro por invocação. Para rotear esforço por subagente, não defina a env.

# CLAUDE_CODE_EFFORT_LEVEL anula effort de subagentes

## Contexto
No Claude Code, a variável de ambiente `CLAUDE_CODE_EFFORT_LEVEL` tem prioridade sobre o effort definido no frontmatter e o parâmetro por invocação. Isso pode levar a resultados inesperados se não for cuidadosamente gerenciado.

## Detalhes
- **Variável de Ambiente:** `CLAUDE_CODE_EFFORT_LEVEL`
- **Efeito:** Anula o effort do frontmatter e o parâmetro por invocação.
- **Projeto:** traycer-webnar-iot-genai-snappy-octopus-54939bc25384

## Armadilhas
- **Roteamento de Esforço:** Para rotear esforço corretamente para subagentes, evite definir a variável `CLAUDE_CODE_EFFORT_LEVEL`.

## Próximos Passos
- Verificar todas as invocações do Claude Code em projetos relacionados.
- Atualizar documentação e guias de uso para evitar esse comportamento inesperado.

## Conexões
- [[Design de Interface com Agente]]
