---
title: PRD-002 — ECC automático para web e C e linha de status ECC/second brain
type: project
tags: [prd, ecc, claude-code, statusline, second-brain, tokens, hooks]
created: 2026-10-15
provenance: obsidian_vault
project: second_brain_memory
confidence: low
verified: 2026-10-15 via leitura dos arquivos do dotfiles por agente ecc:architect e conferência manual das divergências 1, 4 e 5
scope: project
---

# PRD-002 — ECC automático para web e C e linha de status ECC/second brain

> Rascunho de design produzido por um agente `ecc:architect` (somente leitura) a pedido do usuário em 2026-10-15 e
> revisado pela sessão principal. As decisões da seção 6 foram respondidas em 2026-10-15 (ver lá); o spike E0 foi
> executado (seção 2). Itens marcados **NÃO VERIFICADO** não foram confirmados na documentação do Claude Code nem por teste. Contexto: trilha B da
> [[RFC-001 - Memória de Agentes sobre o Second Brain com Orçamento de Tokens]] e a decisão
> [[ECC - Adotar Ideias, Não o Runtime]].

## 0. Divergências entre o pedido e os arquivos

O agente listou sete. Uma foi **refutada** na conferência e duas foram confirmadas:

1. **Confirmada.** O L1 (`prompt_hint.sh`) grava no `.seen` também em modo `shadow` (a gravação vem antes do teste de modo).
   Contar as linhas do `.seen` incluiria notas que o modelo nunca viu. A contagem exibida precisa de um arquivo próprio.
2. O L0 grava o **caminho** da nota no `.seen` (não o título), e o L1 também; o dedupe entre os dois funciona.
3. A linha do ECC no SessionStart depende do second brain: o `exit 0` do `second-brain-session-start.sh` para
   `SECOND_BRAIN_HOOKS≠1` vem antes dela, então com os hooks desligados a linha do ECC some junto.
4. **Refutada.** O agente disse que `claude/rules/c.md:9` aponta para `~/.claude/rules/ecc/cpp/`, que não existiria. Existe:
   `~/.claude/rules/ecc` é um link para `~/dotfiles/vendor/ecc/rules`, que tem os packs `cpp`, `python` e `rust` já
   carregados globalmente (por `paths:`). Isso muda a análise de C (seção 3.2).
5. **Confirmada.** `exclude_add` em `ecc-project.sh` usa `git rev-parse --absolute-git-dir`. Em worktree isso devolve
   `.git/worktrees/<w>`, e o git lê o `info/exclude` do diretório comum; o `settings.local.json` provavelmente aparece
   como não rastreado no worktree. Corrigir com `--git-common-dir` e testar.
6. `ecc-project.sh` recusa o próprio dotfiles; numa sessão aberta ali, os agentes `ecc:*` não existem.
7. O que o pedido afirmava sobre `statusLine` (`settings.json:155-159`, `padding: 0`) e a seção "ECC por projeto" do
   `AGENTS.md` confere.

## 1. Problema, objetivos e não-objetivos

**Problema.** Ligar o ECC é manual e fácil de esquecer em projetos web e C, onde o usuário o quer ligado; ligar em tudo
custa cerca de 47,5 mil tokens fixos por sessão (F0). O estado do ECC e as notas injetadas só aparecem uma vez, no texto do
SessionStart.

**Métricas**
- M1: em projetos que não são web nem C, a variação de tokens fixos fica em ≤ +50 (medida com `/context`).
- M2: acréscimo da statusline ≤ 5 ms no p95 com cache válido, sem fork novo; total ≤ 100 ms no p95 (100 execuções sobre fixture).
- M3: zero falso "ECC ligado". Sem snapshot da sessão, a linha nunca mostra "ligado" puro.
- M4: toda ligação automática imprime uma linha dizendo o que fez e como desfazer; nenhuma escrita em arquivo versionado.

**Não-objetivos.** Ligar o ECC fora de web e C; cobrir C++; ativar o L1; contar notas "abertas" pelo agente; mudar o pin do ECC;
ligar o ECC no escopo de usuário; usar `claude plugin enable`; linkar `rules/common`.

## 2. Linha de status

**Usa hoje** (`statusline.sh`): `.model.display_name`, `.workspace.current_dir`, `.context_window.remaining_percentage`, com três
forks de `jq`; não usa `session_id`. A presença de `session_id` no JSON só foi confirmada indiretamente (a statusline do
próprio ECC lê esse campo), portanto é dado de terceiros.

**Linha acima do indicador de modo (E0, verificado em 2026-10-15, Claude Code 2.1.300, tmux de 100 e 60 colunas).** A
statusline aceita várias linhas e é renderizada **abaixo da caixa de entrada e acima do indicador de modo**
(`⏵⏵ auto mode on`, `⏸ manual mode on`, que fica sempre na última linha, junto de `← 3 agents`). Portanto a **última linha
impressa pelo comando da statusline** é a que fica imediatamente acima do indicador de modo; o segmento ECC/SB deve ser a
última linha, não a primeira. Alternar o modo com Shift+Tab não mexe nas linhas da statusline. A statusline só é reexecutada
quando há evento de mensagem (digitar não basta). O comando recebe `COLUMNS` (60 num terminal de 60 colunas). O JSON de
entrada tem as chaves `context_window, cost, cwd, effort, exceeds_200k_tokens, fast_mode, model, output_style,
prompt_cache, prompt_id, rate_limits, scratchpad_dir, session_id, thinking, transcript_path, version, workspace`: há
`session_id`, e **não há campo com o modo de permissão**.

**Formato proposto:** `ECC ligado (local) · SB 3 notas` (≤ 40 colunas, sem cor se `NO_COLOR`). Estados: `ECC desligado`;
`ECC ligado* reinicie` (disco mudou depois do início da sessão); `ECC ? (disco: ligado)` (sem snapshot); `SB 0 notas`;
`SB off` (hooks desligados); `SB —` (sem arquivo).

**Custo.** Um único `jq` com `@tsv` (inclui `session_id`), no lugar de três; contagem de notas com `mapfile` sem fork; o estado
do disco fica em cache e só é recalculado se algum dos três arquivos de settings for mais novo que o cache (`-nt`, builtin).
O `session_id` é sanitizado como no SessionStart.

**Estado efetivo da sessão.** Um hook novo `ecc-session-start.sh`, separado do second brain, grava `<sid>.ecc` (0600) com
estado, escopo, packs e se o second brain estava ligado. A statusline compara o snapshot com o disco. **Verificado no E0:**
`/reload-plugins` **não** dispara SessionStart (o hook de teste rodou uma vez, na abertura, e não de novo após o reload, que
informou "Reloaded: 8 plugins · 64 skills · 26 agents · 5 hooks"). Depois de um reload, a linha não terá snapshot novo; o
texto de divergência deve dizer "reinicie ou /reload-plugins".

**"Nota linkada"**: recomendada = **injetada no contexto** (L0 sempre; L1 só em `active`). Aberta pelo agente exigiria um hook
PostToolUse por chamada (futuro opcional). Ranqueada não conta: o modelo não viu. Implementação: arquivo `<sid>.injected`
(caminhos, 0600), escrito pelo L0 e pelo L1 somente em `active`; zera em `compact`; limpeza após 7 dias.

## 3. ECC para web e C

### 3.1 Detecção (`claude/ecc-detect.sh <dir>`, < 50 ms)

Imprime `web <packs>`, `c` ou `none`, sempre com exit 0, usando `[[ -f ]]` e `find -maxdepth 2` com prune de `node_modules`,
`build*`, `dist`, `.git`, `vendor`.

- **Web:** `package.json` com `next|vite|react|vue|nuxt|@angular/core|svelte|@sveltejs/kit|astro`; ou `index.html` na raiz,
  `public/` ou `src/`; ou `tsconfig.json` com `*.tsx|*.vue|*.svelte` em até 2 níveis. Monorepo com `workspaces` ou
  `apps/*` e `packages/*` com framework conta como web. Backend Node puro (Express sem front) dá `none`.
- **C:** `CMakeLists.txt` com `LANGUAGES C` (sem `CXX`), `meson.build`, `Makefile` com `*.c`/`*.h`, ou `compile_commands.json`,
  e nenhum `*.cpp|*.cc|*.cxx` em até 2 níveis. Projeto misto C/C++ dá `none`.
- Submódulo e worktree: reaproveitar o padrão `git-common-dir` só para identificar o repo; a detecção roda na árvore de
  trabalho atual. Dotfiles e vault: sempre `none`.

### 3.2 Packs de rules (nunca `rules/common`)

`common` traz "ALWAYS use parallel Task execution", roteamento de modelo próprio, "tdd-guide PROACTIVELY" e regras de commit,
todos em conflito com o `AGENTS.md`.

- **Web:** `web` + `typescript`, mais `react` (React/Next), `vue`, `nuxt` + `vue` ou `angular` conforme o framework. Svelte e
  Astro não têm pack extra. Todos usam `paths:` e só carregam quando um arquivo casa.
- **C:** nenhum pack no projeto. O `cpp` do ECC declara `**/*.h` e `**/CMakeLists.txt` e manda preferir recursos modernos de
  C++, o que contradiz o `c.md` do usuário. **Observação da conferência (divergência 4):** os packs `cpp`, `python` e `rust`
  de `vendor/ecc/rules` já carregam globalmente por `~/.claude/rules/ecc`, e o `c.md` os cita como base. O valor adicional do
  ECC em C vem então dos agentes e skills do plugin; reavaliar se vale 47 mil tokens após duas semanas.
- Implementação: opção `--packs a,b,c` em `ecc-project.sh on`, criando um diretório de links como o `--no-common` já faz, de
  modo que o `off` e o `status` funcionem sem mudança.

### 3.3 Quando aplicar

O estado só vale em sessão nova. Opções comparadas: (a) wrapper `claude` no zsh que roda `ecc-project.sh auto "$PWD"` antes
de abrir; (b) allowlist em arquivo de config; (c) SessionStart só sugere; (d) `claude plugin enable --scope local`
(descartada: o CLI reescreve o `settings.json` symlinkado, ver
[[Claude Plugin CLI Reescreve o settings.json Symlinkado do Repo]], e não liga as rules).

**Recomendação: (a) + (b) + (c) como fallback.**
- `ecc-project.sh auto <dir>` roda o detector e escreve direto em `<dir>/.claude/settings.local.json` com `jq`; nunca chama o
  CLI de plugin.
- `claude/ecc-auto.conf` (versionado no dotfiles): `kinds=web,c`, `include=` e `exclude=` opcionais.
- O wrapper imprime uma linha, por exemplo `ECC ligado automaticamente (web: react,typescript). Desfazer: make ecc-off DIR=. ou touch .claude/ecc.off`.
- Idempotente: se a chave `ecc@ecc` já existe em `local` ou `projeto` (`true` ou `false`), não mexe em nada.
- Opt-out: `.claude/ecc.off` bloqueia o `auto`; `make ecc-off` passa a criar o marcador e `make ecc-on` a removê-lo; o marcador
  entra em `info/exclude`.
- Subpastas: **verificado no E0** que uma sessão aberta em `proj/sub/deep` carregou o `.claude/settings.local.json` da raiz
  do repositório git (`proj/`): o hook de SessionStart definido lá rodou. Logo o `auto` deve escrever na raiz do git
  (`git rev-parse --show-toplevel`; sem git, no `$PWD`), e o detector deve olhar essa raiz.

### 3.4 Regra do `AGENTS.md`

Substituir o primeiro item da seção "ECC por projeto": política permanente do usuário (2026-10-15) é ligar o ECC
automaticamente em projetos web e C pelo wrapper; o agente continua sem rodar `ecc-on`, `ecc-off` ou `auto` por conta
própria, informa e sugere quando o ECC estiver desligado num projeto web/C, e o teto de 3 agentes por rodada e o contrato de
delegação valem sobre qualquer "PROACTIVELY" de agente `ecc:*`. A automação é do usuário (wrapper), não do agente.

### 3.5 Riscos

Custo de ~47,5 mil tokens em toda sessão web/C, inclusive tarefas triviais (cerca de 3,8 milhões de leitura de cache em 80
turnos, F0); detecção errada liga o ECC onde não deve (mitigação: `none` na dúvida, linha impressa, `ecc.off`); descrições
de agentes do plugin dizem "Use PROACTIVELY" e empurram fan-out (mitigação: regra acima). **Atualização de 2026-10-15:** os hooks
do ECC deixaram de ficar no perfil `minimal`; por decisão do usuário, o ECC roda com o **perfil `strict`, sem hooks desligados e
com o observer ligado**. Em projetos web, C e Node, o M1 passa a incluir ~2 mil tokens de injeção no SessionStart e as perguntas do
GateGuard a cada primeira edição de arquivo; nos demais projetos o M1 não muda. Riscos e mitigações em
[[Reavaliação - ECC com Perfil Completo e Observer Ligado]].

## 4. Plano de desenvolvimento (etapas do tamanho de um merge)

Testes como scripts bash com `mktemp -d` em `tests/` (novo), ligados ao `make lint`/`make test`. Fixtures: next, vite+vue,
nuxt, angular, astro, monorepo com `workspaces`, backend Express, C com CMake, Makefile e meson, misto C/C++, repo vazio,
submódulo (`git submodule add` local) e worktree.

| Etapa | Conteúdo | Pronto quando | Rollback |
|---|---|---|---|
| E0 (spike) | **Feito em 2026-10-15** (seção 2 e 3.3): statusline multilinha acima do modo, `.claude/` da raiz do git vale em subpasta, `/reload-plugins` não dispara SessionStart | respostas registradas aqui | n/a |
| E1 | `ecc-detect.sh`, `exclude_add` com `--git-common-dir`, `tests/ecc_detect_test.sh` | matriz passa, < 50 ms, lint ok | reverter (nada usa ainda) |
| E2 | `--packs`, `auto`, `ecc.off`, `claude/ecc-auto.conf`, targets do Makefile, `tests/ecc_project_test.sh` | idempotência, chave `false` explícita vence, `off` não religa, settings symlinkado intacto, `git status` limpo em repo comum, submódulo e worktree | reverter |
| E3 | **Feito.** wrapper no zsh, sugestão no SessionStart, `AGENTS.md` (o `c.md` não precisou de mudança) | `claude` num fixture web liga e imprime a linha; num `none` não faz nada | remover a função do zsh |
| E4 | **Feito.** `ecc-session-start.sh` (snapshot), `.injected`, ajuste do L1 e da limpeza de 7 dias, registro do hook editando `settings.json` do repo (nunca pelo CLI) | JSON de SessionStart como fixture, shadow não grava `.injected`, 0600 | reverter os dois repos |
| E5 | **Feito.** `statusline.sh` e `tests/statusline_test.sh` | M2 e M3 passam; `sid` malicioso (`../x`) tratado | reverter |
| E6 | medir M1 em um projeto web, um C e um neutro; destilar no vault | números registrados | n/a |
| E7 | Fluxo interativo de melhoria do pack de C (decisão 1): skill ou comando que, em um projeto C, lê o código e o `c.md`/`cmake.md`/`makefile.md`, propõe acréscimos e correções às regras e só grava o que o usuário aceitar item a item | escopo e formato a fechar com o usuário antes de começar | remover a skill |
| E8 | Kind `node-backend` (decisão 3): detector e arquivo de regras próprio `claude/rules/node-backend.md`, no mesmo molde do `c.md` | `ecc-detect.sh` distingue backend de web; regras escritas e revisadas pelo usuário | reverter |

**Entregue em 2026-10-15 (dotfiles, branch `master` até `792cec3`; E3 em `feat/ecc-auto-wrapper`):**

- **E1 e E2** (`cc9e802`, `9b1310e`, `792cec3`): `claude/ecc-detect.sh`, `ecc-project.sh auto|--packs|--no-rules`, marcador
  `.claude/ecc.off`, `claude/ecc-auto.conf` (`kinds`, `include`, `exclude`), `make ecc-auto`/`make test` e 3 suítes de teste.
  Uma revisão independente achou e corrigiu: corrida entre `auto` simultâneos (agora `flock` por repo), `settings.local.json`
  inválido anunciando sucesso, `auto` fora de git, nomes de `--packs` sem validação, `kinds=none`, symlinks, `info/exclude`
  sem `\n` final e vários falsos positivos do detector. Registro: o worktree tinha o bug de `.claude/` aparecer como não
  rastreado (confirmado e corrigido com `--git-common-dir`).
- **E3** (`8008e4b`, `0380d64`, `a5bd20e`): função `claude` em `zsh/ecc-auto.zsh` (aviso em stderr, nunca bloqueia, pula
  subcomandos e `ECC_AUTO=0`), sugestão no SessionStart quando o ECC está desligado num projeto web/C/Node (respeita
  `ecc.off`) e política do `AGENTS.md`. A correção do `c.md:9` **não foi necessária**: a afirmação do agente de que
  `~/.claude/rules/ecc/cpp/` não existia estava errada (divergência 4).
- **E4** (dotfiles `ecb55c5`; vault `prompt_hint.sh`): hook `ecc-session-start.sh` (independente do second brain, corrige a
  divergência 3) imprime a linha de estado e a sugestão e grava o snapshot `<sid>.ecc` em `~/.local/state/claude-session/`
  (0600) só em `startup`/`resume`; o L0 e o L1 em modo `active` gravam `<sid>.injected` (a contagem "SB n notas"; o L1 em
  `shadow` não grava). `ecc-project.sh status` passou a resolver a raiz do git em subpastas e a responder no dotfiles.
- **E5** (dotfiles `cf9c514`): `claude/statusline.sh` imprime duas linhas e a última é `ECC ligado (local) · SB 3 notas · 1
  aberta`, com `*` e "reinicie" quando o disco mudou depois da abertura (cache por mtime), `NO_COLOR`, forma curta com
  `COLUMNS < 40` e um `jq` só. Verificado ponta a ponta num tmux com o zsh real: o wrapper ligou o ECC num projeto React
  descartável e a linha apareceu logo acima do indicador de modo (`⏵⏵ auto mode on`).
- Faltam **E6** (medição de M1), **E7** (fluxo interativo do pack de C) e **E8** (regras de Node backend). Divergência de
  formato: o asterisco vem depois do escopo (`ECC ligado (local)* reinicie`).

**Já entregue (decisão 6):** o hook `second-brain-note-opened.sh` (dotfiles, commit `502a6b2`, branch
`feat/sb-opened-notes-hook`) registra em `<sid>.opened` as notas do vault que o agente abre com `Read` (sem repetir, sem
manifests, sem subagentes, 0600), com teste em `tests/`. A E5 só precisa exibir a contagem (`SB 3 · 1 aberta`).

Agentes: `ecc:tdd-guide`, `ecc:code-reviewer` e revisor de shell só existem em sessão aberta num diretório com ECC ligado (o
dotfiles é recusado); nas outras, usar `cavecrew-*` ou um subagente geral com o mesmo contrato. Teto de 3 agentes por
rodada; E0, E3 e E6 são inline.

## 5. O que não será feito

Ligar o ECC no escopo de usuário; usar `claude plugin enable` ou `install`; linkar `rules/common`; ativar o L1; escrever em
arquivo versionado de projeto; o agente rodar `ecc-on`, `ecc-off` ou `auto` por conta própria; ler segredos ou o transcript
na statusline; instalar dependências novas (só bash, `jq` e `git`).

## 6. Decisões do usuário (2026-10-15)

1. **C liga o ECC sem pack de rules: aprovado.** Acrescentar um **fluxo interativo para melhorar o pack de C** (E7).
2. **Projeto misto C/C++: `none` até decidir: aprovado.**
3. **Backend Node sem front: não conta como web.** O usuário quer um tratamento "semelhante ao de C, mas para Node focado em
   backend": plugin ligado, sem pack de rules do ECC para web, e um arquivo de regras próprio (E8). Sub-decisão pendente: incluir
   ou não o pack `typescript` do ECC (recomendação inicial: não, para ficar igual ao C).
4. **Gatilho: opção A aprovada** (wrapper `claude` no zsh + config + sugestão no SessionStart como fallback).
5. **Ordem das linhas: aprovado**, com a correção do E0: o segmento ECC/SB deve ser a **última** linha da statusline, porque é a
   que fica acima do indicador de modo.
6. **Contar notas abertas além das injetadas: sim, feito agora** (hook `second-brain-note-opened.sh`).
