---
title: "ASD-STE100 in Claude: CLAUDE.md, Output Style or Skill?"
type: article
tags: [claude-code, prompt-engineering, skills]
created: 2026-10-22
provenance: obsidian_vault
authors: StashBase
year: 2026
source: https://stashbase.ai/blog/asd-ste100-claude/
verified: 2026-10-22 via leitura da página com WebFetch
confidence: low
seen_in: [obsidian_vault]
---

# ASD-STE100 in Claude: CLAUDE.md, Output Style or Skill?

## 📝 Resumo

- Compara três veículos: `CLAUDE.md` (sempre carregado, não força nada), output style (vale em toda resposta, precisa de `keep-coding-instructions: true`) e skill (carrega só quando a tarefa pede).
- Teste próprio (prosa, Claude Code 2.1.280, Opus 5.5): 16–18 palavras por frase sem instrução, 11–12 com "80% of the way", 10–11 com a norma completa. Todas as variantes mantiveram 8 de 8 fatos. As respostas não ficaram mais curtas, só as frases.
- Texto sugerido: "Explain things to me in roughly 80% ASD-STE100 style: one idea per sentence, short sentences, active voice, and one word for one meaning. Keep product, code, and domain names unchanged." 

## Confiabilidade

Teste pequeno. A tabela de fatos dela diverge do repo de Ghinda: prosa contra código.

## 🔗 Conexões

- [[ASD-STE100 Simplified Technical English]]
- [[STE-80 - Escrita Controlada para Agentes em Português]]
