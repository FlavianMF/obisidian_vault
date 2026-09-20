---
title: Dials Numéricos Tornam Gosto de Design um Parâmetro Declarado
type: pattern
tags: [design, frontend, agentic-ai, prompt-engineering, brief, parametrizacao]
created: 2026-09-20
provenance: taste-skill
verified: 2026-09-20 via leitura de ~/.agents/skills/design-taste-frontend/SKILL.md (1206 linhas)
---

# Dials Numéricos Tornam Gosto de Design um Parâmetro Declarado

**Quando a direção de um artefato tem eixos independentes e ordenáveis, declará-los como
inteiros nomeados vale mais do que descrevê-los em adjetivo: o número vira condição que
outras regras conseguem citar, e vira valor auditável no fim.** É o mecanismo central da
[[Taste Skill]], e resolve o mesmo problema que o [[Contrato de Direção Antes do Código]]
resolve em prosa — os dois se somam, não competem.

Três eixos, escala 1 a 10, baseline `8 / 6 / 4`:

| Dial | Do 1 ao 10 |
|---|---|
| `DESIGN_VARIANCE` | simetria perfeita → assimetria, quebra de grade, composição fora do eixo |
| `MOTION_INTENSITY` | estático → scroll-trigger, hover magnético, física |
| `VISUAL_DENSITY` | galeria de arte → cockpit de dados |

Os valores não são escolhidos no gosto: saem de uma tabela de sinais do brief
(`minimalista / Linear` → 5-6 / 3-4 / 2-3; `agência / Awwwards` → 9-10 / 8-10 / 3-4;
`setor público / regulado` → 3-4 / 2-3 / 4-5) e de uma matriz de nove presets por caso
de uso.

## Por que o número e não o adjetivo

- **Outras regras conseguem citá-lo.** *"Hero centralizado é evitado quando
  `DESIGN_VARIANCE > 4`"* (`SKILL.md:210`) só é uma regra checável porque o dial é um
  valor declarado. Adjetivo não entra em condicional.
- **Trava de honestidade.** *"Motion claimed, motion shown"* (`:359`): se
  `MOTION_INTENSITY > 4`, a página tem de se mover de verdade; se não dá para entregar
  movimento no escopo disponível, **baixa o dial para 3** em vez de fingir. O parâmetro
  não pode ser decoração da resposta.
- **Expressa delta, não só estado.** O preset `Redesign - preserve` é
  `match / match+1 / match` (`:74`): o dial descreve a distância em relação ao que já
  existe, coisa que "modernizar um pouco" não consegue dizer.
- **Nome estável é parte do contrato.** `:78` proíbe apelidar: nada de `LAYOUT_VARIANCE`
  ou `ANIM_LEVEL`. Referência cruzada só funciona sobre identificador fixo.

## Generaliza

Serve a qualquer build aberto conduzido por agente em que a direção tenha dimensões
ortogonais: agressividade de refatoração, verbosidade de documentação, rigor de teste.
A pergunta de projeto é *quais são os dois ou três eixos em que este trabalho pode variar
de forma independente?* — e, achados, vale declarar o valor de cada um na resposta antes
de produzir, porque é isso que torna a escolha comparável entre projetos.

Limite honesto: eixo numérico só cabe onde há ordem. [[Modo do Visitante Escolhe o Conjunto de Regras]] trata do caso
categórico, em que a escolha é de conjunto e não de
grau, e não deve ser espremida numa escala.

## 🔗 Conexões

- [[Contrato de Direção Antes do Código]] — a variante em prosa, com condição de saída.
- [[Análise de Trade-off (Trade Study)]] — peso e sensibilidade sobre eixos declarados.
- [[Regra Gradual é Ignorada pelo Agente, Regra Binária é Obedecida]] — por que o dial
  precisa aparecer em regras contáveis para valer alguma coisa.
- [[Slop de IA é Convergência de Treino, Não Falta de Gosto]] — o que acontece quando
  nenhum eixo é pinado.
