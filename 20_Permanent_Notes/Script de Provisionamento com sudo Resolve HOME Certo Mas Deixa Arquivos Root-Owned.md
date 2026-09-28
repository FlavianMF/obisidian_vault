---
title: Script de Provisionamento com sudo Resolve $HOME Certo Mas Deixa Arquivos Root-Owned
type: trap
tags: [linux, sudo, provisioning, dotfiles, permissions, multi-user, nvm]
created: 2026-09-28
provenance: aijail
---

# Script de Provisionamento com sudo Resolve $HOME Certo Mas Deixa Arquivos Root-Owned

Um script de dotfiles/provisionamento pensado pra rodar como `sudo ./install.sh`
frequentemente detecta corretamente o usuário real via `$SUDO_USER` e redireciona
`$HOME` pra ele (pra não symlinkar tudo dentro de `/root`). Isso resolve **o
caminho** certo, mas não resolve **o dono**: o processo inteiro continua com
`EUID=0`, então todo `mkdir`, `git clone`, `ln -sf` feito depois cria arquivos
`root:root` — mesmo estando fisicamente dentro de `/home/<usuário-real>`.

**Sintoma**: conta nova não consegue escrever em `~/.config`, `~/.claude`,
`~/.oh-my-zsh` etc. (`Permission denied`), mesmo tendo sudo full. Mais
traiçoeiro ainda: alguns `ln -sf` do próprio script (ex.: symlink de tema do
oh-my-zsh) falham *silenciosamente* na hora da instalação, porque o diretório
destino (`custom/themes/`) já estava root-owned quando o comando rodou — o erro
não aparece, só aparece muito depois como "theme not found" no shell.

**Fix**: no fim do script, ou depois de cada bloco que grava em `$HOME`, ou
`chown -R "$SUDO_USER":"$SUDO_USER"` sobre tudo que foi criado ali, ou (melhor)
trocar as operações de arquivo que deveriam pertencer ao usuário real por
`sudo -u "$SUDO_USER" <comando>` em vez de deixar o script inteiro rodar como
root do início ao fim. Resolver `$SUDO_USER`/`REAL_HOME` só no início não basta
sozinho.

**Corolário direto (mesma família de bug)**: não depender de um Node
instalado via apt (owned by root em `/usr/local/lib/node_modules`) nem do nvm
de *outra* conta pra rodar `npm install -g`. Cada conta de usuário deveria ter
seu próprio nvm (`curl ... | bash` como aquele usuário, não como root) — aí o
prefix do npm fica dentro do próprio `$HOME`, sem exigir sudo e sem repetir o
mesmo problema de ownership pra qualquer pacote global que o usuário instalar
depois.

## ✅ Resolvido em dotfiles (2026-09-28)

`~/dotfiles/install.sh` aplica a opção "envolver por operação":

- `run_as_user()` = `sudo -u "$SUDO_USER" -H env HOME="$HOME" PATH="$PATH" "$@"` (direto se não há `SUDO_USER`). Todo `mkdir`/`git clone`/`ln`/`cp`/`curl | sh` em `$HOME` passa por ele; apt, `/opt` e `/usr/local` continuam como root. `sudo` não chama função de shell, então helpers como `create_config_link` chamam `run_as_user` internamente, comando a comando.
- **Reparo tem que rodar no COMEÇO**, não só no fim. Conta já contaminada faz o próprio `run_as_user mkdir` falhar com `Permission denied` e o script morre no meio (pegadinha achada no teste em container). `repair_ownership` = `find "$HOME" -xdev -user root -print0` + `chown -h`, idempotente; roda de novo no fim como varredura.
- Claude Code via instalador nativo (`curl -fsSL https://claude.ai/install.sh | bash` como usuário real) grava em `~/.local/bin` e `~/.claude`, sem npm global e sem Node — some o corolário do nvm.
- **Homebrew recusa rodar como root** e exige `/home/linuxbrew` gravável: criar o diretório como root, `chown` para `$SUDO_USER`, e rodar o instalador via `run_as_user` com `NONINTERACTIVE=1`. Root puro (sem `SUDO_USER`) deve pular com warn.

## 🔗 Conexões
- [[Checklist de Bootstrap de Workflow de Desenvolvimento]]
