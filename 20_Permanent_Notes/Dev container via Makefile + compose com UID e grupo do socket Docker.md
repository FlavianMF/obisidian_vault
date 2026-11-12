---
title: Dev container via Makefile + compose com UID e grupo do socket Docker
type: pattern
tags: [devcontainer, makefile, docker, compose, uid, gid]
created: 2026-11-10
provenance: outlet_promo
seen_in: [outlet_promo]
confidence: low
scope: global
verified: 2026-11-10 via candidato do agente em outlet_promo, não reproduzido na revisão
---

# Dev container via Makefile + compose com UID e grupo do socket Docker

O Makefile calcula as variáveis do host e o compose as consome. Assim o container escreve arquivos com o UID do usuário e acessa o socket do Docker do host sem `root`.

## Padrão
O Makefile exporta quatro variáveis:
- `PROJECT_DIR`: diretório do projeto.
- `HOST_UID` e `HOST_GID`: UID e GID do usuário do host.
- `DOCKER_GID`: GID do socket, obtido com `stat -c %g /var/run/docker.sock`.

O `docker-compose.yml` usa essas variáveis assim:
- `${VAR:?msg}` falha cedo, com mensagem clara, quando alguém roda o compose sem o Makefile.
- `HOST_UID` e `HOST_GID` entram como build args da imagem.
- `group_add` recebe `DOCKER_GID`, para o usuário não-root falar com o socket.
- `network_mode: host` dá acesso direto à rede do host.
- Os caches ficam em volumes nomeados.
- As ferramentas da imagem são fixadas por versão e checksum.

## Armadilha
Não chame a variável de `UID`. Ela é `readonly` em bash e zsh, e a atribuição falha. Use `HOST_UID`.

## Relacionados
- [[Docker-out-of-Docker (DooD)]]: decisão de montar o socket do host, com os riscos de segurança.
- [[Supabase CLI em container exige repo no mesmo caminho do host]]: o mesmo setup exige `${PROJECT_DIR}:${PROJECT_DIR}` como mount.
- [[Ambiente de Desenvolvimento de Agentes em Containers]]
- [[Volumes Docker por etapa (node_modules e .next) enchem o disco]]: custo dos volumes nomeados quando se criam por etapa.

## Pendente
Falta validar em outros hosts e versões do Docker. Esta nota nasceu de um único projeto.
