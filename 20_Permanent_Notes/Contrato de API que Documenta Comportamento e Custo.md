---
title: Contrato de API que Documenta Comportamento e Custo
type: pattern
tags: [api-design, documentation, contract, typescript, llm]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

# Contrato de API que Documenta Comportamento e Custo

Um arquivo de declarações de tipos pode carregar muito mais que assinaturas: **a semântica de
execução e o custo econômico de usar a API errado**. Quando carrega, ele substitui boa parte
da documentação e fica no único lugar que quem vai usar realmente lê — o autocompletar.

O `claude-code.d.ts` do [[claude-code]] (10.772 linhas, 432 tipos) é o exemplo. Além dos
tipos, o docstring de cada evento diz:

- **O que é pinado e o que é reescrevível.** Em `turn.step`: *"Um hook reescreve `model` ou
  `effort` na descida; o resto é pinado"*. Em `tool.check`: *"Os três são a identidade da
  pergunta e são pinados: um hook decide sobre esta chamada, ele não a muda"*.
- **A ordem e quem vence.** *"A última palavra subindo a cadeia é a decisão."*
  *"Os hooks de managed settings rodam primeiro: o deny deles é o resultado da chamada."*
- **O que acontece quando o hook falha.** *"Um hook que falha deixa passar."*
  *"Um plugin quebrado nunca bloqueia um prompt."*
- **O custo de uma resposta instável** — o caso mais notável:

  > Seções são cacheadas por nome pela duração da sessão até `$.ui.invalidate("prompt.section")`:
  > **uma resposta instável gasta o cache de prompt do modelo a cada chamada.**

  Quem for escrever um hook de `prompt.section` lê isso no momento exato em que a decisão de
  colocar um timestamp na seção seria tomada. Nenhuma página de "boas práticas" alcança esse
  ponto.
- **Exemplos executáveis de uma linha**, no `@example` de quase todo evento:
  `on("tool.check", { tool: "Read" }, () => ({ decision: "allow" }))`.

**Por que isso importa para um harness:** quem escreve extensão não lê a documentação toda; lê
o tipo. Semântica que só existe num guia separado é semântica que será violada. E num sistema
onde código de terceiro roda no caminho quente de uma chamada de LLM, "violar a semântica"
significa dinheiro e latência, não só um bug.

**Como aplicar:** ao definir a superfície do harness, escrever no docstring de cada operação
(a) o que é imutável, (b) quem decide em caso de conflito, (c) o que acontece na falha,
(d) o que é cacheado e o que invalida, (e) um exemplo de uma linha. Se o contrato é gerado da
build (como aqui, pelo comando `/plugin-types`), ele não diverge.

**Limite honesto:** o mesmo arquivo avisa *"EARLY ACCESS: esta superfície pode mudar entre
releases sem aviso"*, e de fato a API inteira está atrás da flag
`CLAUDE_CODE_ENABLE_FUNCTION_HOOKS=1` e **não aparece em nenhuma das 5.768 entradas do
changelog** — ver [[Repo Público sem o Source do Produto]]. Contrato bom não é o mesmo que
contrato estável.
