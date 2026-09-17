---
title: Projeto correcoes_docs_tcc
type: project
tags: [project, agentic-ai, education, grading, rubric, documentation]
created: 2026-09-17
provenance: correcoes_docs_tcc
status: active
path: /home/flv/projetos_pnaat/correcoes_docs_tcc
verified: 2026-09-17 via git log (30 commits) e leitura de NOTAS.md
predecessor: hermes_validator
---

# Projeto correcoes_docs_tcc

Correção da documentação final do módulo de TCC contra a rubrica oficial, **conversacional e um
repositório por vez**. O professor manda `<nome do grupo>: <link do GitHub>`; o agente clona, levanta
evidência localizada, propõe nível e nota; **o professor confirma**.

Terceiro da linhagem: [[hermes_validator]] (multiagente CrewAI, arquivado) → `validacoes_iot`
(pipeline em massa com dashboard, 77+ alunos) → este (conversacional, sem dashboard, um repo por
vez). O que se replica entre eles não é a infraestrutura — é a rubrica-como-artefato e o gate humano,
descritos em [[Rubrica em Prosa Vira Gabarito de Evidência]].

## 📌 Como funciona

| Arquivo | Papel |
|---|---|
| `docs/criterios-evidencia.md` | **O gabarito.** Rubrica em prosa traduzida em evidência verificável. Versionado |
| `docs/rubricas.md`, `docs/notas.md` | Fontes oficiais, imutáveis |
| `docs/playbook.md` | Armadilhas já encontradas, append-only |
| `.claude/commands/avaliar.md` | O procedimento: `/avaliar <grupo> <url>` |
| `grupos/<slug>/` | Saída: `resumo.md` + `avaliacao.md` |
| `NOTAS.md` | Tabela consolidada |
| `repos/` | Clones dos alunos, descartáveis, somente leitura |

Regras invioláveis: reler o gabarito antes de cada nota; evidência `arquivo:linha` ou nada; nunca
editar avaliação `CONFIRMADA`; nunca escrever dentro de `repos/`; **não executar o código do aluno**
— a avaliação é por leitura, e README que não permite reproduzir por leitura já é o achado.

## 📊 Primeiro lote — 2026-09-17

16 grupos em **1h43 de relógio** (09:32–11:15), 22 sessões de Claude Code, 3 a 4 em paralelo no pico,
~70–105k tokens de saída por grupo. Três grupos exigiram rerun depois de a primeira sessão abortar.

| Nível | Nota | n |
|---|---|---|
| 4 Avançado | 2.2 | 8 |
| 3 Adequado | 1.65 | 1 |
| 2 Básico | 1.1 | 7 |
| 1 / 0 | 0.55 / 0 | 0 |

Média proposta 1,684 de 2,2. Distribuição bimodal, com o eixo README respondendo por 6 das 7 notas
baixas — ver [[Nível Intermediário Vira Vale Quando o Topo Pede Tudo do Anterior Mais X]].

O gabarito atravessou o lote inteiro em **Versão 1**, sem uma emenda. Todo o aprendizado tático foi
para `docs/playbook.md`, que saiu de 13 para 338 linhas em oito entradas.

## 🧠 Conceitos e padrões extraídos

- [[Toda Checagem Barata Passa - Documentação Falha na Ligação, Não na Presença]] — as oito
  armadilhas do playbook são uma espécie só, e a consequência é de método.
- [[Nível Intermediário Vira Vale Quando o Topo Pede Tudo do Anterior Mais X]] — a régua de cinco
  níveis operou como porta binária.
- [[Sessões Paralelas Perdem Escrita no Índice Compartilhado]] — 4 de 16 linhas do `NOTAS.md` se
  perderam no fan-out.
- [[O Catálogo de Armadilhas Para de Crescer Antes do Aprendizado Parar]] — o playbook parou de ser
  escrito e quase nunca foi lido.
- [[Rubrica em Prosa Vira Gabarito de Evidência]] — a nota-mãe, agora com a seção de campo.

## ⚠️ Em aberto (verificado em 2026-09-17)

1. **O gate humano não fechou.** 16 de 16 notas seguem `PROPOSTA`. Toda a maquinaria de divergência
   proposta × nota manual é desenho não testado, e é a razão de ser declarada do projeto.
2. **`/avaliar` não manda ler o playbook** — onde mora a gradação de severidade que decide notas.
3. **O gabarito não absorveu essa gradação** (rebaixa × pesa só na fronteira × não supre eixo
   ausente). Candidato natural a Versão 2.
4. **`--depth 50` no clone** faz a contagem de commits do `resumo.md` medir coisas diferentes por
   grupo, e o julgamento de "dump de véspera" depende dela.
5. **Deriva de template**: 5 das 16 avaliações fugiram da estrutura; parsing automático quebra.
6. **`NOTAS.md` não declara o total esperado de grupos** — o fluxo não detecta que faltou alguém.

## Links
- [[hermes_validator]] (predecessor arquivado)
- [[Validação Acadêmica Automatizada]] (o irmão em massa)
- [[Orquestração Híbrida de Agentes]]
- [[Playbook de Projeto - Erros Já Cometidos Como Artefato]]
- [[Checklist de Bootstrap de Workflow de Desenvolvimento]]
- [[Agentic AI]]
