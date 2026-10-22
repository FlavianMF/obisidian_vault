---
title: "llm-experiments/simplified-technical-english"
type: article
tags: [llm, eval, prompt-engineering, controlled-language]
created: 2026-10-22
provenance: obsidian_vault
authors: Lucian Ghinda
year: 2026
source: https://github.com/lucianghinda/llm-experiments/tree/main/simplified-technical-english
verified: 2026-10-22 via leitura da página com WebFetch
confidence: low
seen_in: [obsidian_vault]
---

# llm-experiments/simplified-technical-english

## 📝 Resumo

- Dados brutos, prompts e scripts (`measure.rb`, `coverage.rb`, `ADJUDICATION.md`). Rodadas em 4 e 20 ago 2026, 92 execuções.
- Alvos: 4 trechos de Ruby. Seis fatos por alvo, 24 por condição. Pontuação por regex e depois por leitura humana.
- Cláusulas: controle; `in Simple Technical English`; `in ASD-STE100 Simplified Technical English`; e na rodada 3 `Use ASD-STE100 Simplified Technical English (STE) when it doesn't detract from meaning.`
- **Claude, fatos lidos à mão (de 24):** controle 24, Simple TE 24, ASD-STE100 17. Na rodada 3: ASD inline 23, **ASD com cláusula de escape 24**, ASD no fim sem escape 21.
- **Codex, fatos lidos à mão, rodada 3:** controle 17, ASD inline 13, ASD com escape 18.
- Pelo regex, ASD-STE100 manteve 14 e 11 de 24 (é a origem do "46,8% perdido"). O regex subestima as variantes com estilo.
- Palavras por frase: nenhum controle ficou abaixo de 16,3, e nenhuma execução com estilo passou de 10,7 (rodadas 1–2).
- O que importa é a redação da cláusula de escape, não a posição dela.

## Confiabilidade

É a fonte com dados brutos. Duas execuções por célula não dão intervalo de confiança.

## 🔗 Conexões

- [[ASD-STE100 Simplified Technical English]]
- [[STE-80 - Escrita Controlada para Agentes em Português]]
