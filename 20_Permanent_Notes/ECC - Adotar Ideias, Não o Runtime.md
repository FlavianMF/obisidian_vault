---
title: "ECC (affaan-m/ECC): adotar ideias, não o runtime"
type: decision
tags: [agentic-ai, claude-code, harness, hooks, skills, dotfiles, second-brain-sync]
created: 2026-09-30
provenance: dotfiles
seen_in: [dotfiles]
confidence: medium
scope: global
verified: 2026-09-30 via leitura do repo affaan-m/ECC v2.2.2 na pesquisa do setup de harness
---

# ECC (affaan-m/ECC): adotar ideias, não o runtime

**Decisão:** do [ECC](https://github.com/affaan-m/ECC) (v2.2.2, MIT) entram só peças
escolhidas, **reescritas** no `~/dotfiles`. Não se instala plugin, hooks nem rules do
ECC. O pacote é tomado como catálogo de ideias para [[claude-code]], não como runtime.

## Contexto

- **Tamanho:** 293 skills e 94 commands. Instalar tudo é o caso extremo de
  [[Skill Monolítica Gasta o Contexto Antes de a Tarefa Começar]]: o custo aparece antes
  da tarefa, e boa parte não se aplica.
- **O perfil `standard` de hooks atrapalha o fluxo real:** o GateGuard intercepta ações
  rotineiras, há bloqueio de escrita de `.md` (que quebra a escrita de notas e docs de
  projeto), e as rules forçam delegar para agents `ecc:*`, competindo com as skills e
  agents já em uso. É a mesma classe de conflito de
  [[Skills de Design se Contradizem Entre Si, Dentro e Fora do Pacote]].

## Alternativa rejeitada: continuous-learning v2 ("instincts")

Avaliada e descartada:

- grava só **tool calls**, não os prompts, então perde o porquê de cada ação;
- roda um **observer Haiku em background**, custo contínuo por sessão;
- a **redação de segredos é fraca** para um log que persiste em disco;
- tem **bugs abertos** no upstream.

## Adotado (reescrito no dotfiles)

1. deny list de permissões (`~/.ssh`, `~/.aws`, `.env*`, `secrets/`, `curl | bash`, `ssh`/`scp`/`nc`);
2. statusline (modelo, cwd, branch, git, % de contexto, badge do caveman);
3. hook `Stop` de format/typecheck em lote, opt-in por projeto;
4. dica de compactação estratégica (~50 tool calls, por `session_id`);
5. rules aparadas (performance, security, git) dentro do `AGENTS.md`;
6. `contexts/{dev,review,research}.md` com aliases;
7. auditoria AgentShield em `make audit`.

## Ideias portadas para o second-brain

O que o instincts queria (aprendizado que se acumula entre sessões) já é o papel do
vault — faltavam sinais de confiança e de ciclo de vida:

- frontmatter `confidence`, `seen_in`, `verified`, `scope`
  ([[00_META/Frontmatter-Schema]]), com promoção manual quando `seen_in` tem 2+ projetos;
- `session_hint.sh`: o hook SessionStart imprime até 5 notas relevantes ao repo;
- nudge no `Stop`: lembra de destilar pro vault quando houve edits e nenhum `vault_sync.py`.

Ver [[Skill - Sincronização de Conhecimento Recursiva]] e
[[Documentação Desatualizada é Bug, Não Dívida]] (o `--stale-report` é o lado
automático do carimbo `verified`).

## 🔗 Conexões

- [[worldflowai everything-claude-code é Re-upload Sem Licença e Congelado]] — o mirror
  que **não** é a fonte.
- [[Uma Fonte de Regra, N Harnesses Compilados]] — por que as peças adotadas moram numa
  fonte única (`AGENTS.md`) servindo Claude Code, Codex e OpenCode.
- [[Hook Escreve Estado, Renderizador Lê Tudo Num Passe]] — mesma forma da statusline.
- [[Regra Gradual é Ignorada pelo Agente, Regra Binária é Obedecida]] — critério para
  aparar as rules.
