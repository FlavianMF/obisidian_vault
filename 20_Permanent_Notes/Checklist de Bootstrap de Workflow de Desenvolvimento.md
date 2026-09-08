---
title: Checklist de Bootstrap de Workflow de Desenvolvimento
type: pattern
tags: [dev-workflow, ci-cd, git, worktree, versioning, testing, project-bootstrap]
created: 2026-09-08
provenance: capella_llm_window
project: capella_llm_window
---

# Checklist de Bootstrap de Workflow de Desenvolvimento

## Objetivo

Checklist prescritivo de disciplina de desenvolvimento, generalizado a partir do único
projeto que hoje tem o fluxo completo maduro (`capella_llm_window`:
`docs/ci-cd.md` + `docs/releasing.md`). Não é um copia-e-cola — cada eixo abaixo é o
**princípio**, com a instância Java/Tycho do llm_window como exemplo, e uma nota de como
adaptar por stack. Usado pela skill `second-brain-sync`, Behavior 3 (Project Workflow
Bootstrap), pra plantar essa disciplina num projeto novo/incompleto — sempre com
confirmação explícita do usuário antes de escrever qualquer arquivo.

## 1. Worktree obrigatório em checkout compartilhado

Quando várias sessões (agentic ou humanas) trabalham no mesmo repo ao mesmo tempo, commit
direto no checkout principal é risco de colisão silenciosa. Regra: uma branch de
feature/fix nova vira um `git worktree` dedicado (`git worktree add <path> -b
<branch>`), nunca commit direto no checkout que outras sessões podem estar usando.
Aplica a qualquer stack — é puramente git, não depende de linguagem.

Ver [[Confirmar Qual Worktree Está Sendo Testada Antes de Diagnosticar]] (armadilha
irmã: workspace de execução/teste do usuário pode estar apontando pra qualquer um dos
worktrees, não assumir que é o checkout principal) e
[[Push Pra Branch Ocupada Via Branch Temporária]].

## 2. Testes com escopo explícito, não silencioso

Documentar — não só codificar — o que é coberto e o que é deliberadamente deixado de fora,
e por quê. O llm_window cobre só lógica pura (`JsonUtil`, `ChatSession`, `SessionStore`,
etc.) e exclui explicitamente UI/rede/subprocess (`ChatView`, `MCPClient`) do
**numerador e do denominador** do gate de cobertura — sem essa exclusão explícita, a meta
de cobertura fica matematicamente inatingível sem infraestrutura de teste de UI (SWTBot),
e o gate mentiria (mediria só as classes de suporte de teste, "100%" falso).

Adaptar por stack: qualquer test runner com relatório de cobertura (`pytest --cov`,
`jest --coverage`, `go test -cover`, `cargo tarpaulin`) tem mecanismo equivalente de
excluir arquivos/diretórios do cálculo — usar isso, documentado, em vez de baixar o
threshold silenciosamente.

## 3. Relatórios de CI/CD dentro do próprio pipeline

Sem depender de SaaS externo (Codecov etc.) pra ver resultado de build:
- Resumo por run (`$GITHUB_STEP_SUMMARY` no GitHub Actions, ou equivalente da
  plataforma) com pointers pros relatórios de teste/cobertura/lint.
- Comentário automático no PR com pass/fail de teste e cobertura por diff.
- Artifact de build baixável **em todo PR/branch**, nomeado com versão+branch+hash
  (não só na release taggeada) — permite instalar/rodar um build específico sem esperar
  merge.

## 4. Fluxo de branches

`feature/*`/`fix/*` → PR → branch de integração (`develop`/`main`). Branch de integração
→ branch de release só via PR, com gate de CI verde obrigatório (proteção de branch
configurada na plataforma, não é convenção de workflow). Sem push direto em nenhuma das
duas branches protegidas.

## 5. Versionamento + release automatizada

Fonte única de verdade da versão por stack (`package.json`, `pyproject.toml`,
`pom.xml`+`MANIFEST.MF`, `Cargo.toml`, etc.) — bump manual como parte do PR de release
(não semantic-release automático, decisão consciente do llm_window: número decidido por
humano). Criação de tag automática **no mesmo job** que builda e publica — nunca dois
workflows encadeados por tag push, porque um tag empurrado com o `GITHUB_TOKEN` padrão
não dispara outro workflow (salvaguarda anti-recursão do GitHub Actions).

Ver [[Automação de Release - Tag e Build Têm Que Estar no Mesmo Job]] e
[[Tag de Release Não Volta Pra Develop Sozinha]].

## 6. Comando/flag de introspecção de versão

Expor tag/commit/branch/dirty em tempo de execução — pra sempre conseguir responder
"que exato commit gerou isto" sem adivinhar (o llm_window teve exatamente esse problema:
build Eclipse desatualizado gerando erro de compilação que parecia bug real). Instância
do llm_window: comando `/version` no próprio chat, lendo `git.properties` gerado em
build-time (`git-commit-id-maven-plugin`) com fallback pra `git` local em modo dev.
Adaptar por stack: `--version` de CLI, endpoint de healthcheck de serviço, footer de
build de app web — o mecanismo importa menos que garantir que sempre existe *algum*
jeito de perguntar isso sem abrir o histórico de commits à mão.

## Como aplicar (Behavior 3)

1. Detectar arquivo(s) de convenção do harness já presentes no projeto (`CLAUDE.md`,
   `AGENTS.md`, `.cursorrules`, `.windsurfrules`, `.clinerules`, `GEMINI.md`).
2. Se já tiver seção de workflow reconhecível e atual, não fazer nada.
3. Senão, inspecionar o stack real do projeto (arquivo de build/manifest de versão) e
   adaptar os 6 eixos acima — nunca copiar literalmente as partes específicas do
   llm_window pra um projeto de outra stack.
4. Rascunhar a seção, **perguntar ao usuário antes de escrever** (criar/adicionar/pular),
   nunca escrever sem confirmação.
5. Criar o arquivo se não existir; se existir, inserir/atualizar só a seção delimitada,
   preservando o resto.

## 🔗 Conexões
- [[Confirmar Qual Worktree Está Sendo Testada Antes de Diagnosticar]]
- [[Push Pra Branch Ocupada Via Branch Temporária]]
- [[Automação de Release - Tag e Build Têm Que Estar no Mesmo Job]]
- [[Tag de Release Não Volta Pra Develop Sozinha]]
