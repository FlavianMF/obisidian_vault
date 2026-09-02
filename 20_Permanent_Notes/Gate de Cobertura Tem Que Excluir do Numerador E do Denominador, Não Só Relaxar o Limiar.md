---
title: Gate de Cobertura Tem Que Excluir do Numerador E do Denominador, Não Só Relaxar o Limiar
type: pattern
tags: [ci-cd, testing, code-coverage, quality-gates]
created: 2026-09-02
provenance: capella_llm_window
project: capella_llm_window
---

# Gate de Cobertura Tem Que Excluir do Numerador E do Denominador, Não Só Relaxar o Limiar

## Problema

Parte de um codebase costuma ser estruturalmente difícil/caro de testar
unitariamente (UI, chamadas de rede, subprocess, wrappers finos de SDK
externo). Um gate de cobertura (ex. "90% de linhas cobertas ou falha o
build") que inclui essas classes no cálculo tem duas saídas ruins:
baixar o limiar global pra acomodar (perde o sinal pro resto do código,
que deveria ter cobertura alta de verdade), ou deixar passar mesmo sem
cobrir (defeats the purpose do gate).

## Padrão

Excluir as classes estruturalmente não-testáveis **tanto do numerador
quanto do denominador** do cálculo de cobertura — não just "permitido
ficar baixo", remover completamente da conta. O gate passa a medir só o
que realmente é razoável exigir 90%+ (lógica pura, sem I/O externo
direto).

**Detalhe que importa**: a mesma lista de exclusão precisa alimentar
**dois** lugares — o gate que bloqueia merge (`check`/`fail-under`/
equivalente da ferramenta) E o relatório legível por humano (comentário
de PR, badge, HTML). Se as duas listas divergem (ex.: exclusão só
configurada no gate, relatório usa o rollup sem filtro), o comentário de
PR pode mostrar um número tipo "49% falhando" — assustador, mas
inteiramente artefato de medir o código errado — enquanto o gate de
verdade, com a lista certa, passa tranquilo. Isso confunde quem revisa o
PR e corrói a confiança no gate ("passou mas o comentário diz que
falhou?").

## Quando aplicar

Qualquer ferramenta de cobertura (Jacoco, Istanbul/nyc, coverage.py,
`cargo-tarpaulin`, `go test -cover`) que suporte lista de exclusão por
padrão de arquivo/classe/pacote. Ao configurar um gate de cobertura pela
primeira vez, ou ao ver um gate "sempre verde só porque o limiar é baixo
demais": identificar as classes que não deveriam contar (não "não
conseguimos testar ainda", mas "estruturalmente não faz sentido testar
unitariamente aqui"), excluir das duas execuções (gate + relatório) com
a mesma lista, documentar o motivo da exclusão junto da configuração.

Exemplo real: `jacoco-maven-plugin` em `capella_llm_window` —
`<excludes>` definido uma vez no nível do plugin (`plugins/org.capella.ai.chat.tests/pom.xml`),
herdado tanto pela execução `report` quanto pela `check`, com comentário
explicando exatamente esse raciocínio.

## 🔗 Conexões
- [[Automação de Release - Tag e Build Têm Que Estar no Mesmo Job]]
- [[Escopo de Trigger de CI - push Só nas Branches Protegidas, pull_request Cobre o Resto]]
