---
title: AdSense em App Flutter Web Atrás de Login - Aprovação Improvável e Pacote Oficial Só para Jogos
type: trap
tags: [adsense, flutter-web, canvaskit, monetizacao, anuncios, supabase-auth]
created: 2026-10-23
provenance: outlet_promo
project: outlet_promo
seen_in: [outlet_promo]
verified: 2026-10-23 via docs do Google (AdSense answer/161351 e publisherpolicies answer/11112688), FAQ do Flutter Web e páginas do pub.dev; sem pedido real de aprovação
confidence: low
scope: global
---

# AdSense em App Flutter Web Atrás de Login - Aprovação Improvável e Pacote Oficial Só para Jogos

Um app Flutter Web renderizado em canvas, com o conteúdo atrás de login, dificilmente passa na revisão do AdSense. E o pacote oficial `google_adsense` não atende app que não é jogo. Descubra isso antes de reservar espaço de anúncio na UI.

## Por que a aprovação é improvável

- **Conteúdo do editor.** A política do Google exige conteúdo de valor como foco da visita. Ela proíbe anúncio em tela sem conteúdo do editor, em construção, ou usada para alerta e navegação (publisherpolicies answer/11112688).
- **Login do rastreador.** O AdSense aceita conteúdo atrás de login, mas o login do rastreador precisa devolver um cookie de sessão por POST ou GET (AdSense answer/161351). Supabase Auth com link mágico ou OAuth guarda a sessão no JavaScript do navegador, não num cookie de servidor. O modelo não encaixa (inferência).
- **Indexação.** A FAQ do Flutter Web diz que a saída do Flutter "doesn't align with what search engines need to properly index". Ela recomenda HTML à parte para conteúdo de texto.
- **Superfície pública.** A saída natural é uma página pública em HTML. Se o app proíbe script do Google antes do aceite (LGPD), essa página também fica sem o código do AdSense.

## Pacotes Flutter para AdSense (outubro de 2026)

| Pacote | Situação |
|---|---|
| `google_adsense` (`labs.flutter.dev`, 0.1.2) | "Only intended for use by web games". O H5 Games Ads exige pedido de acesso. O `AdUnitWidget` para anúncio comum é experimental, só por convite, e não aceita pedidos |
| `flutter_adsense` (1.0.0) | Enviador não verificado, 2 likes. Renderiza um `<ins>` com largura e altura fixas |
| `HtmlElementView` próprio | `HtmlElementView.fromTagName('ins')` mais `adsbygoogle.push({})` via `dart:js_interop`. Pouco código e auditável. Use `PointerInterceptor` em diálogos sobre o anúncio |

O H5 Games Ads (intersticial e recompensado na web) vale só para jogos HTML5 com conta AdSense aprovada.

## O que NÃO funcionou

Nenhum pedido de aprovação foi feito. A pesquisa descartou o pacote oficial pela própria página do pub.dev. A doc do Flutter não quantifica o custo de um platform view no CanvasKit: meça a rolagem antes de decidir.

## Conexões
- [[AdSense Só Suporta CSP Estrito com Nonce - Hosting Estático Não Gera Nonce]]
- [[Receita de Anúncio de Rede Escala com Tempo de Tela, Não com Usuários]]
- [[Anúncio de Rede no Brasil - Google É Controlador Independente e ECA Digital Veda Perfilamento]]
