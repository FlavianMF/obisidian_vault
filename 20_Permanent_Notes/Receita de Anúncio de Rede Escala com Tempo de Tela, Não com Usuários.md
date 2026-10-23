---
title: Receita de Anúncio de Rede Escala com Tempo de Tela, Não com Usuários
type: concept
tags: [monetizacao, anuncios, ecpm, admob, adsense, produto]
created: 2026-10-23
provenance: outlet_promo
project: outlet_promo
seen_in: [outlet_promo]
verified: 2026-10-23 via gráficos do Appodeal eCPM Report 2025 (4º tri de 2024) e estimativa Sensor Tower do Block Blast; projeção própria, sem dado real de campanha
confidence: low
scope: global
---

# Receita de Anúncio de Rede Escala com Tempo de Tela, Não com Usuários

A receita de anúncio de rede é impressões vezes eCPM. As impressões vêm do tempo de tela e dos formatos, não do número de usuários. Um app de utilidade com sessões curtas e um nativo discreto rende duas ordens de grandeza menos por usuário que um jogo casual.

## Fórmula da projeção

```text
receita/mês = usuários ativos × sessões/semana × anúncios/sessão × 4,33 × preenchimento × eCPM / 1000
```

Liste cada fator como premissa explícita, com fonte ou "suposição".

## Números de referência (eCPM em US$, 4º tri de 2024, Appodeal)

| Região e sistema | Banner | Intersticial | Recompensado |
|---|---|---|---|
| América Latina, Android | ~0,10 | ~1,25 | ~1,75 |
| América Latina, iOS | ~0,12 | ~2,15 | ~3,35 |
| América do Norte, Android | ~0,5 | ~9,6 | ~9,0 |
| América do Norte, iOS | ~0,4 | ~10,4 | ~13,6 |

- Os dados vêm quase todos de jogos. App de utilidade tende a ficar abaixo.
- eCPM de nativo para o Brasil não foi encontrado. Ele cai entre banner e intersticial.
- Sem personalização, o Google desliga os lances nos grupos de rendimento móveis. Isso reduz a demanda.

## Caso comparado (outubro de 2026)

- **Block Blast:** cerca de US$ 127 mi de anúncio em 5 meses de 2026 (Sensor Tower), com cerca de 35 mi de DAU. Isso dá cerca de US$ 0,72 por DAU por mês. Sessões de 12 min, 2,7 por dia, tela cheia após cada derrota.
- **Sacari (outlet_promo):** 3 sessões de 30 s por semana e 1 nativo no feed. A projeção média dá cerca de US$ 0,0055 por usuário ativo semanal por mês, perto de 130 vezes menos. Com 100 mil usuários ativos semanais, isso dá cerca de R$ 3 mil por mês.
- Somar intersticial e recompensado aumentou a receita projetada em cerca de 60%. A ordem de grandeza não mudou.

## Como usar

- Calcule o ponto de equilíbrio contra o custo de engenharia e a manutenção, não só contra zero. No outlet_promo, pagar 8 a 11 dias de engenharia em 12 meses pediu cerca de 30 mil usuários ativos semanais.
- Some à conta o risco de marca e o risco jurídico. Eles não aparecem no eCPM.
- Compare com uma venda direta (B2B): um patrocínio pequeno pode igualar a rede com milhares de usuários.

## Conexões
- [[Mapear Pilha de Anúncios de App de Terceiro sem Descompilar - Exodus, app-ads.txt e Estudos de Caso]]
- [[AdSense em App Flutter Web Atrás de Login - Aprovação Improvável e Pacote Oficial Só para Jogos]]
- [[Anúncio de Rede no Brasil - Google É Controlador Independente e ECA Digital Veda Perfilamento]]
