---
title: Submodule HTTPS Remote Herda Conta gh Errada
type: trap
tags: [git, submodule, ssh, github-cli, second-brain-sync]
created: 2026-08-09
provenance: projetos_claude
---

# Submodule HTTPS Remote Herda Conta gh Errada

`git submodule add https://github.com/<user>/<repo>.git <path>` clona via
HTTPS. Se a máquina tem `gh` autenticado num **usuário GitHub diferente** do
dono do repo (dois usuários, ex.: conta pessoal vs. conta de outra
organização), qualquer `git push` no submodule falha com 403 — mesmo que a
chave SSH certa exista no disco — porque o credential helper do `gh` responde
antes, autenticado como a conta errada.

**Sintoma**: `remote: Permission to <owner>/<repo>.git denied to <outra-conta>.`

**Fix**: depois do `submodule add`, trocar o remoto pra SSH explicitamente:
```
git remote set-url origin git@github.com:<owner>/<repo>.git
```
E garantir a chave certa carregada no ssh-agent (`ssh-add -l`) — mas atenção:
`ssh-agent`/`ssh-add` setam variável de ambiente (`SSH_AUTH_SOCK`) que **não
persiste entre chamadas de shell separadas** em ferramentas de agente que
rodam cada comando num processo novo. `eval "$(ssh-agent -s)" && ssh-add ...`
precisa estar na **mesma invocação** do `git push` que o usa.

## 🔗 Conexões
- [[Skill - Sincronização de Conhecimento Recursiva]]
