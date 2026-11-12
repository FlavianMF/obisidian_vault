---
title: "CLI traycer: mensagem que começa com --- vira flag"
type: permanent
created: 2026-11-10T14:57:08
moc: "Design de Interface com Agente"
tags: [cli, traycer, flags, frontmatter]
source_inbox: "5c48891b-cli-traycer-mensagem-que-comeca-com-vira-flag.md"
tier: "L2"
score: 0.711
---

# CLI traycer: mensagem que começa com --- vira flag

Em 'traycer agent send --message TEXTO', um prompt com frontmatter (---) é lido como opção. Passe valores como --message=TEXTO. O CLI exige TRAYCER_EPIC_ID e TRAYCER_AGENT_ID de um agente real, e 'traycer monitor' falha em env -i.

# CLI traycer: mensagem que começa com --- vira flag

## Contexto
O comando `traycer agent send --message TEXTO` apresenta um comportamento inesperado onde um prompt com frontmatter (---) é interpretado como uma flag. Isso pode levar a erros ou mal-entendidos na execução do comando.

## Detalhes
- **Comando Invocado**: `traycer agent send --message TEXTO`
- **Problema**: O prompt com frontmatter (---) é lido como uma flag, o que resulta em um comportamento inesperado.
- **Solução Sugerida**: Passe valores como `--message=TEXTO` para evitar a confusão com frontmatter.
- **Requisitos**: O CLI exige `TRAYCER_EPIC_ID` e `TRAYCER_AGENT_ID` de um agente real.
- **Falha**: O comando `traycer monitor` falha em `env -i`.

## Próximos Passos
1. Documentar o comportamento inesperado para evitar futuros erros.
2. Atualizar a documentação do CLI para refletir a correção sugerida.
3. Testar o comando `traycer agent send --message=TEXTO` para garantir que o problema foi resolvido.
4. Investigar a causa da falha em `traycer monitor` e corrigir, se necessário.

## Conexões
- [[Design de Interface com Agente]]
