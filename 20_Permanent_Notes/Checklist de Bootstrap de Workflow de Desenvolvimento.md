---
title: Checklist de Bootstrap de Workflow de Desenvolvimento
type: pattern
tags: [dev-workflow, ci-cd, git, worktree, versioning, testing, project-bootstrap]
created: 2026-09-08
provenance: capella_llm_window
project: capella_llm_window
verified: 2026-09-11 via leitura de docs/ do orbita-platform (RFCs, plano de fase, playbook)
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

**Refinamento medido (`orbita-platform`, Etapa 12a — origem numa worktree ainda não
mesclada)**: um piso simbólico (80%) é um número que ninguém defende e que a primeira
pressão derruba. A forma que resiste é **catraca**: o piso é o **último valor medido**, e só
sobe. Cada etapa pode acrescentar um incremento fixo (ex.: +2pp em ramificações até 90/90);
**baixar o piso exige uma nota justificando**, não uma edição de configuração. Os números
moram num arquivo de baseline versionado (`quality-baseline.json`) declarado como fonte única
— os documentos de qualidade citam o arquivo em vez de repetirem o número, que é como um
número documentado apodrece. Mesma catraca serve para duplicação de código, limites de
tamanho de arquivo e contagem de vulnerabilidades: o valor de hoje é o teto de amanhã.
Gate que não bloqueia merge ainda vale como catraca, desde que o relatório apareça no PR.

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

Variante de checkout compartilhado (`orbita-platform`): a branch de trabalho nasce junto com
a worktree e se chama `worktree-<escopo>`, uma por etapa do plano de fase; o **escopo do
commit é a etapa** (`feat(fase2-e10):`, `docs(fase2-e9b):`, `fix(etapa11):`), com sufixo
`(Qn)` quando o commit implementa a resposta da pergunta numerada `n` feita ao usuário
naquela sessão. **PR e merge ficam com o usuário**, depois de ele validar o código da
worktree rodando ao vivo. Ver [[Skill - Fluxo de Trabalho de Feature Branch]] e
[[Plano de Fase em Etapas Mescláveis]].

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

## 7. Documentação viva — nota desatualizada é bug, não dívida

Nota velha não é ausência de informação: é **informação errada com aparência de
autoridade**, e por isso pior que nota nenhuma. Quem encontra uma pasta vazia vai
procurar a verdade no código; quem encontra um documento detalhado e recente confia
nele. Incidente que originou este eixo: três apresentações construídas sobre notas de
seis dias antes, afirmando "8 de 11 propostas resolvidas" quando o `git log` mostrava
10 de 11 — duas propostas implementadas e uma release lançada no intervalo.

**Critério de conclusão** (não é zelo, é definição de pronto): a nota é parte do
entregável, não um artefato posterior. Uma tarefa não está concluída enquanto a
documentação que descreve o que você mexeu não voltar a ser verdadeira. Trabalho *extra*
é a primeira coisa cortada sob pressão; trabalho *inacabado* é terminado.

**Ao terminar cada tarefa**, antes de dizer "pronto":

1. Liste o que tocou — módulo, ferramenta, arquivo, versão, status, decisão. Essa lista
   é a entrada dos greps seguintes, e não exige julgamento nenhum.
2. Varra a documentação do projeto pelos **marcadores de afirmação de estado** — caçar as
   palavras que envelhecem, não o assunto, é o que transforma julgamento em busca:
   ```bash
   grep -rniE "pendente|não implementado|ainda não|falta|TODO|planejado|aguardando|previsto" \
     docs/ notes/ README.md CLAUDE.md
   ```
   Mais um grep pelos nomes próprios do que mudou, e atenção a contagens e versões
   ("13 tools", "v0.1.0") — essas apodrecem sem nenhuma palavra-marcador por perto.
3. Cada acerto: ainda é verdade? Se não, corrija **no mesmo ciclo** — não vira backlog.
4. Em afirmação de estado, carimbe a verificação: data + como foi checada.
5. Relate ao usuário o que foi atualizado.

**Ao final da sessão**, sincronizar com o vault global: destilar o que foi aprendido *e*
propagar lá o que a mudança invalidou.

Adaptar por stack: os caminhos do grep mudam conforme onde o projeto guarda documentação
(`docs/`, `notes/`, `adr/`, `rfcs/`, wiki no repo, docstrings de módulo). O que não muda é
a dupla "listar o que tocou → procurar quem afirma algo sobre isso". Em projeto com ADRs,
incluir o diretório de decisões — ADR que virou mentira é o caso mais caro de todos.

Ver [[Documentação Desatualizada é Bug, Não Dívida]] (princípio completo) e
[[Notas de Análise Envelhecem em Dias - Reverificar no Código Antes de Apresentar]]
(o lado da leitura: reverificar antes de usar nota como base de decisão).

## Como aplicar (Behavior 3)

1. Detectar arquivo(s) de convenção do harness já presentes no projeto (`CLAUDE.md`,
   `AGENTS.md`, `.cursorrules`, `.windsurfrules`, `.clinerules`, `GEMINI.md`).
2. Se já tiver seção de workflow reconhecível e atual, não fazer nada.
3. Senão, inspecionar o stack real do projeto (arquivo de build/manifest de versão) e
   adaptar os 7 eixos acima — nunca copiar literalmente as partes específicas do
   llm_window pra um projeto de outra stack.
4. Rascunhar a seção, **perguntar ao usuário antes de escrever** (criar/adicionar/pular),
   nunca escrever sem confirmação.
5. Criar o arquivo se não existir; se existir, inserir/atualizar só a seção delimitada,
   preservando o resto.

## 🔗 Conexões
- [[Cadeia de Artefatos de Projeto - Intenção, RFC, Plano de Fase]] (o par complementar: o que construir e em que ordem)
- [[Plano de Fase em Etapas Mescláveis]]
- [[Confirmar Qual Worktree Está Sendo Testada Antes de Diagnosticar]]
- [[Push Pra Branch Ocupada Via Branch Temporária]]
- [[Automação de Release - Tag e Build Têm Que Estar no Mesmo Job]]
- [[Tag de Release Não Volta Pra Develop Sozinha]]
- [[Documentação Desatualizada é Bug, Não Dívida]]
- [[Notas de Análise Envelhecem em Dias - Reverificar no Código Antes de Apresentar]]
