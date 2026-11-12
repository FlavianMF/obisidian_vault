---
title: "Bash run_in_background com & interno notifica completed na hora"
type: permanent
created: 2026-11-10T14:59:26
moc: "Design de Interface com Agente"
tags: [bash, background, run_in_background, notification]
source_inbox: "7e806b71-bash-run-in-background-com-interno-notifica-completed-na-hor.md"
tier: "L2"
score: 0.734
---

# Bash run_in_background com & interno notifica completed na hora

Usar & dentro de um comando com run_in_background faz o harness avisar exit 0 de imediato, enquanto o processo segue vivo. Rode o comando em primeiro plano dentro do background ou espere com until-loop no log, nunca confie na notificação.

# Bash run_in_background com & interno notifica completed na hora

## Contexto
Quando se usa `&` dentro de um comando com `run_in_background`, o harness pode notificar imediatamente que o processo foi concluído, mesmo que o processo ainda esteja em execução.

## Detalhes
O uso de `&` dentro de um comando com `run_in_background` faz com que o processo seja executado em segundo plano. No entanto, o harness pode notificar imediatamente que o processo foi concluído, retornando `exit 0`. Isso pode levar a confusão, pois o processo ainda está em execução.

## Próximos passos
- Evite usar `&` dentro de comandos com `run_in_background`.
- Considere rodar o comando em primeiro plano dentro do background ou usar um loop `until` para verificar o log até que o processo termine.

## Conexões
- [[Design de Interface com Agente]]
