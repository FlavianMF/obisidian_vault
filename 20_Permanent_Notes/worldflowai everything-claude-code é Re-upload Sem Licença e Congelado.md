---
title: worldflowai/everything-claude-code é re-upload sem licença e congelado do ECC
type: trap
tags: [agentic-ai, claude-code, hooks, security, licensing, oss, supply-chain, armadilha]
created: 2026-09-30
provenance: dotfiles
seen_in: [dotfiles]
confidence: medium
scope: global
verified: 2026-09-30 via leitura do repo worldflowai/everything-claude-code e do README do upstream
---

# worldflowai/everything-claude-code é re-upload sem licença e congelado do ECC

**Armadilha:** `worldflowai/everything-claude-code` aparece em busca como se fosse o
"everything Claude Code". Não é a fonte: é um **re-upload do
[ECC](https://github.com/affaan-m/ECC) sem licença e congelado em 2026-01-23**. Quem
instala dali herda código sem permissão de uso e uma versão parada no tempo.

## O que está quebrado

Os hooks não batem com o contrato atual do [[claude-code]]:

- **matchers escritos como expressões**, não como o padrão que o harness casa, então
  o hook nunca dispara ou dispara onde não devia;
- **log em stderr**, que o harness trata como saída de erro/feedback, não como log;
- leem **env vars que não existem**: `CLAUDE_TRANSCRIPT_PATH` e `CLAUDE_SESSION_ID`. O
  harness entrega `transcript_path` e `session_id` no **JSON do stdin**.

E o upstream avisa explicitamente sobre **mirrors com malware**. Um fork congelado e sem
licença é exatamente o formato em que isso chega.

## Como detectar

- Sem `LICENSE`, último commit antigo e nenhum link de volta para o autor: tratar como
  mirror.
- Hook que lê `$CLAUDE_SESSION_ID`/`$CLAUDE_TRANSCRIPT_PATH` em vez de `jq` sobre o
  stdin está escrito para um contrato que não existe.
- Conferir o repo do autor (`affaan-m/ECC`) e a lista de mirrors que ele reconhece.

## O que fazer

Ler o **upstream** e, mesmo nele, adotar ideias reescritas, não o runtime — ver
[[ECC - Adotar Ideias, Não o Runtime]].

## 🔗 Conexões

- [[Repo Público sem o Source do Produto]] — outra forma de o repo parecer o que não é.
- [[Autoridade por Assento na Cadeia de Hooks]] — por que hook de terceiro é superfície
  de segurança, não conveniência.
