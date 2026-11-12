---
title: "Hook PostToolUse some em silêncio quando o subcomando do sb.py não existe"
type: permanent
created: 2026-11-10T14:09:49
moc: "Design de Interface com Agente"
tags: [second-brain, triagem-noturna, trap, traycer-dotfiles-chipper-platypus-46ef31bf4e13]
source_inbox: "925ce88b-hook-posttooluse-some-em-silencio-quando-o-subcomando-do-sb.md"
tier: "L2"
score: 0.728
---

# Hook PostToolUse some em silêncio quando o subcomando do sb.py não existe

sb-prune.sh está ligado em settings.json (Bash|Grep|Glob), mas o sb.py da master do vault não tem o subcomando prune. O hook roda com 2>/dev/null e sai 0, então não poda nada e gasta um processo por chamada. Confira com sb.py <subcomando> --help antes de ligar um hook que o chama.

---
title: Hook PostToolUse some em silêncio quando o subcomando do sb.py não existe
type: trap
tags: [bash, grep, glob, hook, sb.py, prune]
created: 2026-11-09
summary: sb-prune.sh está ligado em settings.json, mas o sb.py da master do vault não tem o subcomando prune. O hook roda com 2>/dev/null e sai 0, então não poda nada e gasta um processo por chamada.
confidence: low

## Contexto
O hook `PostToolUse some` está configurado para ser executado em `settings.json`. Este hook é suposto chamar o subcomando `prune` do script `sb.py`.

## Detalhes
- **Script**: `sb-prune.sh`
- **Configuração**: Ligado em `settings.json`
- **Problema**: O `sb.py` da master do vault não possui o subcomando `prune`.
- **Efeito**: O hook roda com `2>/dev/null`, o que supostamente silencia erros, mas ainda gasta um processo por chamada.

## Próximos passos
1. Verifique se o subcomando `prune` está disponível no `sb.py` da master do vault.
2. Se não estiver disponível, considere remover ou desativar o hook `PostToolUse some`.
3. Se o subcomando for necessário, atualize o `sb.py` para incluir o subcomando `prune`.

## Conexões
- [[Design de Interface com Agente]]
