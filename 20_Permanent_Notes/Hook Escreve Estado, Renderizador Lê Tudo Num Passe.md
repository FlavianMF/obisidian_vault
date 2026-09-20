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

## v2: escopo por "quem tá pedindo" e um daemon que já sabia mais que eu

Depois de rodando, pedido novo: a barra devia mostrar só o que pertence à
sessão tmux atual, não o servidor inteiro — acesso a outras sessões vira
interação explícita (clique/tecla), não poluição constante.

6. **`status-format[]` é opção global, mas dá pra escopar por sessão sem
   nenhum estado compartilhado — só embutindo o token no comando do job.**
   `#(bash render.sh '#{session_name}')` faz o tmux expandir
   `#{session_name}` **por cliente conectado, antes** de disparar o job; como
   o cache de job do tmux é chaveado pela string exata do comando, duas
   sessões produzem duas strings diferentes → dois jobs cacheados/rodando
   independentes, cada um só vendo o argumento da sua própria sessão. Nenhum
   IPC, nenhum arquivo de "quem sou eu" — o próprio mecanismo de expansão de
   formato do tmux já resolve isso.

7. **Poda e filtro de exibição são dois passos diferentes, e só um dos dois
   pode ser escopado.** Se a poda (`list-panes -a` + checagem de PID) também
   fosse filtrada pela sessão de quem chamou, um pane cuja sessão tmux
   morreu vira órfão pra sempre: nenhuma sessão sobrevivente jamais "seria
   dona" dele pra podar. A poda tem que continuar olhando o servidor
   inteiro sempre; só o passo de "isso entra no `out`" é que recebe o filtro
   de sessão.

8. **`break` num loop de renderização com múltiplas categorias acumulando em
   paralelo é uma armadilha.** Ao dividir "meus panes" (contados/desenhados)
   de "panes de outra sessão" (só contados, pra um badge tipo `+N
   elsewhere`), um `break` no overflow do MEU lado corta a iteração antes de
   passar pelos arquivos de OUTRAS sessões que ainda viriam depois na ordem
   do glob — o contador do badge sai errado, silenciosamente, sem erro
   nenhum. Trocar por `continue` (com uma flag pra não re-fazer o recount
   caro em toda iteração seguinte) resolve; a lição generaliza: **um loop
   que acumula mais de uma coisa não pode `break` só porque UMA das coisas
   já satisfez sua condição de parada.**

9. **Um daemon que já existe pode estar mantendo o estado que você tá
   reinventando.** Achei (não documentado, achado por investigação direta em
   `~/.claude/jobs/<8-hex-do-session_id>/state.json`) que o daemon do Claude
   Code já mantém, ao vivo, um nome gerado pra sessão (`name`, com
   `nameSource: auto|user`) e um estado próprio mais rico que o meu modelo de
   4 estados (`working|done|blocked|failed|stopped`, mais `tempo:
   active|idle|blocked`). Antes de construir uma segunda fonte de verdade
   (ex.: inferir "falhou" a partir de padrões no transcript), vale procurar
   se o processo que você tá monitorando já expõe isso barato em algum
   arquivo — `jobs/<id>/state.json` é um `cat` só, e virou overlay
   (`blocked`/`failed`) por cima do estado primário orientado a hook, que
   continua sendo a fonte que funciona mesmo sem o daemon.

10. **Migrar formato de arquivo de estado por causa de UM campo novo
    também corrige bugs latentes em campos antigos, de graça.** O `name` do
    Claude rotineiramente tem espaço (`"knowledge base synchronization"`) —
    incompatível com o parser antigo (1 linha, split por espaço,
    `word-split` + match de prefixo `key=`). Migrar pra 1 `key=value` por
    linha (split só no primeiro `=`) resolveu o campo novo E um bug que já
    existia silenciosamente: um `cwd` com espaço (`~/My Documents/proj`)
    corrompia o parser do mesmo jeito, só nunca tinha disparado porque
    nenhum caminho real na máquina tinha espaço ainda.

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
