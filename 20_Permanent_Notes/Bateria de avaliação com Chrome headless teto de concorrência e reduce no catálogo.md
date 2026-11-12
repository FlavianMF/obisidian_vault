---
title: "Bateria de avaliação com Chrome headless: teto de concorrência e reduce no catálogo"
type: permanent
created: 2026-11-10T14:59:32
moc: "Design de Interface com Agente"
tags: [chrome-headless, pixel-diff, concorrência, reduce-catalog]
source_inbox: "ae9e61c6-bateria-de-avaliacao-com-chrome-headless-teto-de-concorrenci.md"
tier: "L1"
score: 0.749
---

# Bateria de avaliação com Chrome headless: teto de concorrência e reduce no catálogo

Pixel-diff em Chrome headless por software: paralelizar por deck dá ~1,9x, mas sem teto a disputa de CPU virou 25x (N1 46 min vs 2 min). Use teto de 4 processos, repita FAIL em série, e rode varredura só de console com reducedMotion reduce (179 s para 35 s, mesmos vereditos).

# Bateria de avaliação com Chrome headless: teto de concorrência e reduce no catálogo

## Contexto
Avaliação de performance em Chrome headless utilizando pixel-diff para comparar resultados de diferentes sessões.

## Detalhes
- **Paralelização por deck**: Aparência de ganho de ~1,9x na velocidade da varredura.
- **Teto de concorrência**: Sem teto a disputa de CPU aumentou drasticamente o tempo de execução para 25x (46 min vs 2 min).
- **Uso de teto de 4 processos**: Melhoria significativa na performance, reduzindo o tempo de execução para 179 s.
- **ReduceMotion reduce**: Redução do tempo de execução para 35 s, mantendo os mesmos vereditos.

## Próximos passos
- Validar a consistência dos resultados com diferentes tamanhos de catálogo.
- Explorar a escalabilidade da solução em ambientes de maior concorrência.

## Conexões
- [[Design de Interface com Agente]]
