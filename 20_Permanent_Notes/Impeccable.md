---
title: Impeccable
type: concept
tags: [impeccable, design, frontend, claude-code, skills, agentic-ai]
created: 2026-09-20
provenance: impeccable
verified: 2026-09-20 via instalação local (SKILL.md version 4.3.1, engine 0.1.5 linux-x64) + impeccable.style/docs + github pbakaus/impeccable
---

# Impeccable

**Impeccable é uma skill de design para harnesses de IA: um vocabulário de comandos,
um contrato de contexto durável em dois arquivos (`PRODUCT.md` e `DESIGN.md`) e um
detector determinístico que roda fora do LLM.** A premissa dela é que design ruim de
agente não é falta de gosto e sim convergência de treino — todo modelo viu os mesmos
templates de SaaS — então a correção não vem de "capriche mais", vem de dar ao agente
nomes para o que ele está fazendo por reflexo. Autor: Paul Bakaus. Apache-2.0.
Repositório `pbakaus/impeccable`, site https://impeccable.style.

## Arquitetura

Quatro peças, e é a separação entre elas que importa:

1. **A skill** — um `SKILL.md` (~12 KB) com princípios, modos e a tabela de comandos,
   mais 35 arquivos em `reference/` que são os playbooks carregados sob demanda. O
   `SKILL.md` quase não contém método; ele roteia. `new-work.md` (55 KB) e `critique.md`
   (45 KB) só entram no contexto quando o comando correspondente é pedido — carregar
   tudo de uma vez custaria mais contexto do que a tarefa inteira
   ([[07_prompt_contexto_memoria|Prompt, contexto e memória]]).
2. **Quatro subagentes** instalados em `~/.claude/agents/`: `impeccable-asset-producer`,
   `impeccable-documenter`, `impeccable-finish-reviewer` e
   `impeccable-manual-edit-applier`. O finish-reviewer (15 KB) é quem fecha um build — a
   skill trata "não revisado e não documentado" como não terminado.
3. **Um binário Rust autocontido** (`scripts/bin/<plataforma>/impeccable`, baixado no
   primeiro uso, sem Node e sem API key em runtime) que implementa o detector de 61
   regras. Ver [[Detector Determinístico Fora do LLM como Piso de Qualidade]].
4. **Hooks nativos por harness**, que chamam o binário depois de cada edição de arquivo
   de UI e de novo no `Stop`. Ver [[Uma Fonte de Regra, N Harnesses Compilados]].

## Os comandos

23 comandos na tabela da 4.3.1, invocados como `/impeccable <verbo> [alvo]`:

| Categoria | Comandos |
|---|---|
| Build | `shape`, `init`, `document`, `extract` (`craft` é alias depreciado; `teach` alias de `init`) |
| Evaluate | `critique` (review de UX com score heurístico), `audit` (a11y, perf, responsivo) |
| Refine | `polish`, `bolder`, `quieter`, `distill`, `harden`, `onboard` |
| Enhance | `animate`, `colorize`, `typeset`, `layout`, `delight`, `overdrive` |
| Fix | `clarify`, `adapt`, `optimize` |
| Iterate | `live` (picker no browser sobre o dev server) |

Fora da tabela, verbos do launcher: `impeccable hooks <on\|off\|status\|ignore-*\|reset>`,
`impeccable doctor` (reporta drift entre os artefatos do projeto e o que esta versão lê),
`impeccable pin <comando>` (cria atalho `/polish` avulso), `impeccable detect`.
O site documenta ainda `generate`; ele não está na tabela desta build.

`/impeccable` sem argumento **não executa nada** — roda `impeccable signals`, lê o JSON
(tem DESIGN.md? já houve critique? o dev server está de pé? quais arquivos estão sujos?),
roda o detector nos alvos e devolve 2-3 recomendações com o comando exato para digitar.

## Os arquivos de contexto

- **`PRODUCT.md`** — verdade durável do produto, escrita uma vez por `/impeccable init`:
  plataforma, stack, usuários, propósito, posicionamento, contexto de operação,
  capacidades e restrições, compromissos de marca, evidências disponíveis, princípios,
  acessibilidade e inclusão. É o "porquê", não o "como".
- **`DESIGN.md`** — o sistema visual. Em projeto existente sai de `/impeccable document`.
  Em mundo visual novo é escrito **no finish, a partir do que foi construído** — ver
  [[Design System Documentado Depois do Build, Não Antes]].
- ***Surface brief*** — estratégia que pertence a uma rota ou artefato só, incluindo o
  [[Contrato de Direção Antes do Código]].
- **`.impeccable/config.json`** (versionado, do time) e **`.impeccable/config.local.json`**
  (gitignored, por desenvolvedor) — ignores do detector, `hook.enabled`, `hook.quiet`,
  `detector.extensions` para stacks de template (Blade, Twig, ERB, Handlebars).

`critique` persiste um snapshot com score, contagem de P0/P1 e fingerprint do conteúdo
avaliado; `polish` lê esse snapshot como backlog e o fecha quando resolvido ou obsoleto.

## Como instalar (e a armadilha que custou tempo aqui)

Rota recomendada, de dentro do projeto ou global:

```bash
npx impeccable install --yes --global --providers=claude-code --no-hooks
```

**`impeccable@4.x` exige `node >=22.18.0`.** Com um node anterior, o `npx` não falha: ele
resolve silenciosamente para `impeccable@2.3.2`, que **nem tem subcomando `install`** — o
comando "roda" e não faz nada, sem mensagem de erro útil. Se a reação for `sudo npx
impeccable install`, o sudo troca `HOME` para `/root` e a skill inteira vai parar em
`/root/.claude/skills/impeccable/` com modo `drwx------`, ilegível pelo seu usuário. Pior:
o instalador escreve no projeto um `.claude/settings.local.json` **root-owned** apontando
os hooks para `/root/...`, com guarda `[ ! -f ... ] ||`; como o teste `-f` falha para
você, os hooks viram **no-op silencioso** — instalado, aparentemente ativo, sem efeito
nenhum. Diagnóstico rápido: `ls -l ~/.claude/skills/impeccable/SKILL.md`. Se não existir,
procure em `/root`. Nunca resolva
falha de instalação com `sudo` antes de ler a exigência de versão.

Alternativa que dispensa node: `/plugin marketplace add pbakaus/impeccable`.
Atualização: `npx impeccable update`; diagnóstico de drift: `/impeccable doctor`.

## Limites

`live`, `generate` e o `detect` embutido são **web-only** — leem HTML/CSS. Em projeto
`ios`/`android`/`adaptive` (`setup.platform` em PRODUCT.md) nenhum dos três se aplica, e
os playbooks trocam para as variantes `.native.md`.

Ver também [[Modo do Visitante Escolhe o Conjunto de Regras]],
[[Verificação em Passes Limitados, Não em Loop]] e
[[Slop de IA é Convergência de Treino, Não Falta de Gosto]].
