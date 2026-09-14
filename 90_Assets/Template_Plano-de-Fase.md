---
title: Template_Plano-de-Fase
type: template
tags: [template, project-planning, acceptance-criteria, worktree]
created: 2026-09-11
provenance: orbita-platform
---

# Template — Plano de Fase (`docs/projeto/Plano-<Fase>.md`)

Transforma RFCs aprovadas em ordem de execução. Ver [[Plano de Fase em Etapas Mescláveis]].

~~~~markdown
# Plano de Ação — Fase N: {{title}}

**Data**: AAAA-MM-DD · **Base**: RFCs [000](…)–[00N](…) · **Governança**: [Playbook](./Playbook-de-Desenvolvimento.md), [Diretrizes de Testes](../qualidade/Diretrizes-Testes.md)

<!-- Parágrafo: quantas etapas, a régua fixa de merge (suíte verde + typecheck limpo),
     o que é fundação e o que é produto. -->

---

## Visão das etapas e dependências

```
E0 Fundações ──► E1 <…> ──► E2 <…> ──► E3 <…> ──► E4 <…>
 (infra)                                  │
                                          ├────────► E5 <…>
                                          └────────► E6 <…>
                                                        │
                                          E7 Encerramento ◄─┘
```
<!-- O diagrama vale mais que a lista: mostra o que é paralelizável entre sessões. -->

## E0 — <título: fundação, sem mudança visível para o usuário final>

**RFCs**: [001](…), [002](…) · **Depende**: — · Nota de conclusão: <preencher ao fechar> · Worktree: `worktree-<escopo>`

1. <entrega, não tarefa>
2. <entrega>

**Aceite**: <em forma de teste negativo — o que TEM que falhar>
**Atenção (Playbook)**: <a armadilha conhecida que esta etapa vai encontrar>

## E1 — <título> 
<!-- Mesma estrutura. De 2 a 4 entregas por etapa; mais que isso, fatie.
     Ao fechar: acrescentar "✅ Concluído (data)" no heading e o link da nota de conclusão. -->

## En — Encerramento
<!-- Etapa de verdade, com escopo próprio: segurança (hardening, isolamento, segredos),
     qualidade (validação na borda, lint como gate, cobertura agregada) e fecho (build de
     produção, backup/reset, seed de demonstração). É sistematicamente subestimada. -->

## Estratégia de testes (transversal)

## Riscos operacionais desta sequência
| Risco | Mitigação |
|-------|-----------|

## Próximos Passos
<!-- Log append-only: item concluído fica ~~riscado~~ COM o resultado anexado (contagem de
     testes, cobertura, nome da migration, número do PR). Nada é apagado. -->

---
**Referências**: …
~~~~

### Fatiar sob demanda

O gatilho é o **tamanho do diff que o usuário vai validar**, não a complexidade técnica.
`E8` vira `E8a`/`E8b`, com o motivo e a ordem registrados no plano. Nunca renumerar etapas
já publicadas — sufixo de letra preserva os links.

## 🔗 Conexões
- [[Plano de Fase em Etapas Mescláveis]]
- [[Cadeia de Artefatos de Projeto - Intenção, RFC, Plano de Fase]]
- [[Checklist de Bootstrap de Workflow de Desenvolvimento]]
