---
title: Nota de Conclusão de Etapa é Entregável, Não Relatório
type: pattern
tags: [documentation, definition-of-done, dev-workflow, traceability, project-methodology]
created: 2026-09-11
provenance: orbita-platform
project: orbita-platform
---

# Nota de Conclusão de Etapa é Entregável, Não Relatório

Cada etapa do plano de fase ([[Plano de Fase em Etapas Mescláveis]]) fecha com uma nota em
`docs/projeto/`. Ela não é relatório de progresso para o usuário ler uma vez: é o documento
que a **próxima sessão** vai ler para não refazer descoberta já paga. Peça 7 da
[[Cadeia de Artefatos de Projeto - Intenção, RFC, Plano de Fase]].

Critério de conclusão, não zelo: a etapa não está pronta enquanto a nota não existe. Trabalho
*extra* é a primeira coisa cortada sob pressão; trabalho *inacabado* é terminado
([[Documentação Desatualizada é Bug, Não Dívida]]).

## Forma

```markdown
# Fase 2 — E5: Recomendações e Planos de Alocação

**Data**: 2026-07-23 · **RFC**: [RFC-004 §4](../escopo/rfc/RFC-004-…md) · **Plano**: [Plano-Fase-2 — E5](./Plano-Fase-2-Consultores.md#e5--recomendações…) · **Worktree**: `worktree-fase2-e5-recomendacoes` (aguardando validação/merge do usuário)

Parágrafo-resumo: o que a etapa entregou e o que deliberadamente não entregou.

---

## 1. Decisões confirmadas com o usuário nesta sessão
## 2. Modelo de dados
## 3. Backend
## 4. Frontend
## 5. Achado: <título descritivo do que quebrou e por quê>
## 6. Padrão novo: <título do que passou a valer daqui pra frente>
## 7. Segurança
## 8. Verificação
## 9. Fora do escopo desta etapa
## Próximos Passos
**Referências**: …
```

A metadata da linha 3 é o que dá rastreabilidade em quatro direções de uma vez: para trás
(**RFC, com precisão de seção** — `RFC-004 §4`, não "RFC-004"), para o plano (**por âncora
de heading**), para o código (**nome da worktree**) e para o estado (`mesclado em develop` ou
`aguardando validação/merge do usuário`).

## As quatro seções que não podem faltar

**`Decisões confirmadas com o usuário nesta sessão`** — toda vez que o agente perguntou e o
usuário escolheu. É o que impede a sessão seguinte "corrigir" uma escolha deliberada. Quando
a pergunta foi numerada na conversa, o commit correspondente leva o sufixo `(Qn)`.

**`Achado:` / `Padrão novo:`** — com **título descritivo**, nunca nota de rodapé. Exemplos
reais: `## 2. Achado: middleware.ts está depreciado nesta versão do Next`,
`## 4. Padrão novo: Postgres descartável para migrations em worktree`. Todo achado sobe para
o playbook **no mesmo ciclo**, com sintoma, causa e o comando que reproduz
([[Playbook de Projeto - Erros Já Cometidos Como Artefato]]) — a nota guarda o caso completo,
o playbook guarda a regra e linka de volta.

**`Verificação`** — o que foi realmente rodado, com número: contagem de testes por pacote,
cobertura de linhas e de ramificações, typecheck, `npm audit`, e o que foi verificado **ao
vivo** em vez de só em teste unitário. Distinguir os dois importa: no `orbita-platform`,
roteamento por host passou 100% dos testes unitários e não roteava nada em execução real.

**`Fora do escopo desta etapa`** — o que foi encontrado e deliberadamente não corrigido.
Sem essa seção, o achado vira dívida invisível ou vira scope creep silencioso.

## `⚠️` marca o que fica com o usuário

Pré-requisito manual, credencial a criar, variável a configurar, migration a aplicar no banco
real. O agente não executa ação irreversível sobre dado real; ele escreve o roteiro e marca.

## Regra de índice

Etapa concluída ganha **uma linha** no `index.md`, com o emoji de status (`✅` mesclado,
`🟡` aguardando validação) e o resumo em uma frase. O índice continua enxuto — é índice, não
conteúdo. O detalhe mora na nota.

## 🔗 Conexões
- [[Cadeia de Artefatos de Projeto - Intenção, RFC, Plano de Fase]]
- [[Plano de Fase em Etapas Mescláveis]]
- [[Playbook de Projeto - Erros Já Cometidos Como Artefato]]
- [[RFC de Produto - Anatomia e Ciclo de Status]]
- [[Documentação Desatualizada é Bug, Não Dívida]]
- [[Notas de Análise Envelhecem em Dias - Reverificar no Código Antes de Apresentar]]
