---
title: "Hook de Stop que só conta Edit/Write falha em sessões que editam via Bash"
type: trap
tags: [claude-code, hooks, second-brain, dotfiles]
created: 2026-10-15
provenance: dotfiles
seen_in: [dotfiles]
confidence: low
scope: global
verified: 2026-10-15 via execução do hook sobre cópia do transcript (7 edições contadas, aviso emitido)
---

# Hook de Stop que só conta Edit/Write falha em sessões que editam via Bash

O hook `second-brain-stop.sh` lembra de enfileirar aprendizados quando a sessão fez
`>= SECOND_BRAIN_MIN_EDITS` edições. Contando só `Edit|Write|MultiEdit|NotebookEdit`, uma sessão
que edita por `sed -i`, `tee`, redirecionamento ou `python3 -` nunca chega ao limite, e o
aviso nunca sai.

## Como lidar
- Contar também `tool_use` de `Bash` cujo `input.command` casa uma regex de escrita
  (`sed -i`, `tee`, `>`/`>>`, `git commit|mv|rm`, `cp`, `mv`, `rm`, `install`, `chmod`,
  `patch`, `python3 -`). Faz-se isso com `jq` sobre o transcript JSONL.
- Tratar `sb.py candidate add` como "já tratado" no `grep` de supressão, senão o hook
  continua lembrando depois de a fila ter sido alimentada.
- Ao testar, o `grep` no transcript inteiro também casa texto de `tool_result` e de arquivos
  que a sessão leu (`cat` do próprio hook mencionando `vault_sync.py` bastou para suprimir o
  aviso). Para testar, filtre essas linhas da cópia do transcript, ou restrinja a busca aos
  `tool_use` do assistente.

## O que NÃO funcionou
- Subir só o texto do aviso, sem mexer na contagem: o hook seguia mudo em sessões de edição
  por Bash. A causa era o gatilho, não a mensagem.
- Regex de escrita em Bash é heurística: pode dar falso positivo (um `>` dentro de string) e
  não foi testada em separado. Aceitável porque o custo de um falso positivo é um aviso a mais.

Contexto: [[claude-code]], [[Hook Escreve Estado, Renderizador Lê Tudo Num Passe]].
