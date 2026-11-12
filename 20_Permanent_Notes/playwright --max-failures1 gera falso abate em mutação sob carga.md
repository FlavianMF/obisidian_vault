---
title: "playwright --max-failures=1 gera falso abate em mutação sob carga"
type: permanent
created: 2026-11-10T14:59:38
moc: "Design de Interface com Agente"
tags: [mutation testing, playwright, C2, CPU saturation]
source_inbox: "19ac5ec3-playwright-max-failures-1-gera-falso-abate-em-mutacao-sob-ca.md"
tier: "L2"
score: 0.739
---

# playwright --max-failures=1 gera falso abate em mutação sob carga

No C2 (mutation testing com Playwright), --max-failures=1 sob CPU saturada abateu 4 de 4 mutações por um spec alheio instável (bleed.spec.js, passa sozinho). Prefira rodar o spec alvo da regra primeiro (8x mais rápido) e o suite completo só se a mutação sobreviver.

# playwright --max-failures=1 gera falso abate em mutação sob carga

## Contexto
No C2, durante testes de mutação com Playwright, foi observado um comportamento inesperado. Quando o parâmetro `--max-failures=1` é utilizado e a CPU está saturada, o Playwright abateu 4 de 4 mutações por um spec alheio que passa sozinho.

## Detalhes
- **Projeto**: analise
- **Fonte**: agent
- **Contagem**: 1
- **Sessões**: 1
- **IDs de Sessão**: [623385d8-76a1-4f2a-9389-b605738ee6eb]

## Próximos passos
- Verificar se o problema persiste em ambientes de CPU menos saturados.
- Confirmar se o spec alheio (bleed.spec.js) é realmente instável ou se há outro motivo para o abate falso.
- Implementar uma estratégia para rodar primeiro o spec alvo da regra (8x mais rápido) e só o suite completo se a mutação sobreviver.

## Conexões
- [[Design de Interface com Agente]]
