---
title: "Lixo de saída do Bash vem de leitura deliberada, não de teste ou build"
type: permanent
created: 2026-11-10T14:57:37
moc: "Design de Interface com Agente"
tags: [bash, leitura, disciplina, alavanca]
source_inbox: "6fda3ec5-lixo-de-saida-do-bash-vem-de-leitura-deliberada-nao-de-teste.md"
tier: "L3"
score: 0.787
---

# Lixo de saída do Bash vem de leitura deliberada, não de teste ou build

Em 6.468 chamadas Bash (12,4M chars), cat+sed+git+ls+grep somam 50%; 687 chamadas acima de 5k chars geram 51,7%. Cap de 10k cortaria só 8,1%. A poda foi rejeitada no RFC-002 (1,6%). A alavanca é disciplina de leitura (rg antes, Read com offset e limit, sem cat de vários artifacts), não filtro de saída.

# Lixo de saída do Bash vem de leitura deliberada, não de teste ou build

## Contexto
Em 6.468 chamadas Bash (12,4M chars), operações como `cat`, `sed`, `git`, `ls`, e `grep` somam 50% da carga total. 687 chamadas acima de 5k chars geram 51,7% do volume. Um limite de 10k caracteres cortaria apenas 8,1% da carga.

## Detalhes
A poda das chamadas foi rejeitada no RFC-002 (1,6%). A alavanca para lidar com o lixo de saída é a disciplina de leitura, utilizando comandos como `rg` (ripgrep) com offset e limit, em vez de usar `cat` para concatenar múltiplos artefatos.

## Próximos passos
- Implementar a disciplina de leitura usando `rg` com offset e limit.
- Validar a eficácia da abordagem em um ambiente de produção.

## Conexões
- [[Design de Interface com Agente]]
