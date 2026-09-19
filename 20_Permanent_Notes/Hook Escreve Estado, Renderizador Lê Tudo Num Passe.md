---
title: Hook Escreve Estado, Renderizador Lê Tudo Num Passe
type: pattern
tags: [tmux, claude-code, hooks, status-line, shell]
created: 2026-09-18
provenance: tmux-claude-monitor
---

# Hook Escreve Estado, Renderizador Lê Tudo Num Passe

Pra monitorar em tempo real algo que roda fora do seu controle direto (aqui:
várias sessões Claude Code paralelas, cada uma num pane tmux), a arquitetura
que funciona sem polling nem parsing de transcript é: **cada evento de vida
do processo escreve/atualiza um arquivo de estado pequeno; um renderizador
externo, rodando no seu próprio timer, lê todos os arquivos de estado num
único passe e desenha a UI**. Nenhum dos dois lados chama o outro.

Concretamente, em [[tmux-claude-monitor]]: os hooks clássicos do Claude Code
(`SessionStart`, `UserPromptSubmit`, `PreToolUse`, `Notification`, `Stop`,
`SessionEnd`) escrevem uma linha `chave=valor` por pane em
`~/.local/state/<app>/panes/pane-<id>.state`; `render.sh`, chamado a cada
segundo via `#(...)` na `status-format[1]` do tmux, faz um único
`list-panes -a` pra saber quais panes existem, lê cada arquivo, poda os que
sobraram (`rm`) e monta a string de saída. **Escrever nunca é bloqueado por
ler, ler nunca dispara escrever.**

## Armadilhas descobertas testando ao vivo (não óbvias, custam tempo se não
souber de antemão)

1. **`tmux list-panes -a -F '#{pane_id}'` separa por newline, não por
   espaço.** Um check de pertencimento tipo `case $live_panes in *" $pane
   "*)` só funciona se você fizer `| tr '\n' ' '` na saída primeiro — do
   contrário TODO pane é considerado "não existe mais" e tudo que você
   escreve é podado no segundo seguinte. Sintoma: script funciona isolado
   (`bash render.sh` com fixtures manuais só se você não testar o prune),
   mas apaga tudo assim que testado de ponta a ponta.

2. **`status-left`/`status-right`/`status-format[]` passam a string inteira
   por `strftime(3)`.** Isso vale pro texto literal do seu config E pro
   output de qualquer `#(comando)` embutido — confirmado empiricamente:
   `tmux display-message -p 'x%6y'` imprime `x   %6y` (corrompido, os 3
   espaços vêm de `%6` sendo lido como diretiva strftime com largura 6),
   enquanto `'x%%6y'` imprime `x%6y` correto. Só o resultado de uma
   substituição `#{...}` (variável nativa do tmux) escapa dessa segunda
   passada — texto literal e stdout de job (`#(...)`) não escapam. Como um
   pane id do tmux É literalmente `%<dígitos>`, qualquer script que
   alimenta uma `status-format`/`status-left`/`status-right` com pane ids
   (ou qualquer texto com `%` seguido de dígito) tem que fazer
   `texto="${texto//%/%%}"` na string inteira antes de devolver. Sem isso o
   bug é sutil: não quebra a sintaxe, só corrompe visualmente o que aparece
   na barra.

3. **`tmux display-message -p` não é ambiente válido pra testar
   `#(comando)`.** Jobs (`#()`) rodam assíncronos e o cache de resultado é
   por contexto de redraw contínuo (status line real, redesenhada por
   `status-interval`); uma chamada avulsa de `display-message` nunca
   "esquenta" esse cache, então sempre volta vazio pra esse pedaço,
   independente de quantas vezes repetir. Prova que o job realmente roda
   ao vivo: gravar no log de mensagens do tmux (`tmux show-messages`) e
   confirmar que os comandos internos do seu próprio script (ex.:
   `show-options`, `list-panes`) aparecem lá, timestampados, repetindo a
   cada intervalo — evidência indireta, mas conclusiva, sem precisar
   printar a tela real.

4. **`range=user|X` só devolve `X` em `mouse_status_range` pro SEU range.**
   Pros ranges nativos (`range=session|X`, `range=window|X`, `range=pane|X`)
   o tmux devolve a palavra fixa `"session"`/`"window"`/`"pane"`, não o `X`.
   Isso é o que permite sobrescrever `MouseDown1Status` global e ainda
   distinguir "clicou no meu indicador" de "clicou na lista de janelas
   nativa" sem quebrar o comportamento default — checando se
   `#{mouse_status_range}` é uma dessas 3 palavras fixas (senão, é seu `X`).

5. **Liveness por PID (`[ -d /proc/$pid ]`), não por evento de término.**
   Um hook `SessionEnd` cobre o caso feliz, mas `kill -9` no processo nunca
   dispara hook nenhum. Gravar o PID do processo real (subindo a árvore de
   `$PPID` via `/proc/<pid>/comm` até achar `claude`/`node`) e checar
   `/proc/$pid` no renderizador a cada passe é o que faz a entrada sumir da
   UI mesmo quando o processo morre sem avisar ninguém.

## Generaliza pra além de tmux

O par "hook grava fato pontual → arquivo texto simples, um por
entidade monitorada" / "renderizador varre tudo, poda o que não existe
mais, redesenha do zero" serve pra qualquer barra de status/dashboard
alimentada por eventos de um processo que você não controla (CI,
daemon, outro agente) — desde que o renderizador tenha como perguntar
"essa entidade ainda existe de verdade?" por fora do próprio arquivo de
estado (aqui: `tmux list-panes` + `/proc`), pra não confiar cegamente em
um evento de término que pode nunca chegar.

Ver também [[Autoridade por Assento na Cadeia de Hooks]].
