---
title: Mapear Pilha de Anúncios de App de Terceiro sem Descompilar - Exodus, app-ads.txt e Estudos de Caso
type: pattern
tags: [monetizacao, anuncios, pesquisa, exodus-privacy, app-ads-txt, competitive-research]
created: 2026-10-23
provenance: outlet_promo
project: outlet_promo
seen_in: [outlet_promo]
verified: 2026-10-23 via aplicação ao Block Blast (com.block.juggle): relatório Exodus 10.8.6, app-ads.txt da Hungry Studio e estudos de caso de AdMob, InMobi e DT
confidence: low
scope: global
---

# Mapear Pilha de Anúncios de App de Terceiro sem Descompilar - Exodus, app-ads.txt e Estudos de Caso

Dá para levantar a mediação, as redes e os formatos de um app concorrente só com fontes públicas. Não é preciso descompilar, contornar proteção nem interceptar tráfego. Cada fonte responde uma pergunta diferente. Combine as fontes e marque a confiança de cada uma.

## Fontes, na ordem

1. **Exodus Privacy** (`reports.exodus-privacy.eu.org/en/reports/<pacote>/latest/`): análise estática do APK com os SDKs e as permissões. Mostra mediação e adaptadores. Exemplo: "AppLovin (MAX and SparkLabs)" mais adaptadores de quase todas as redes de lances do MAX indica MAX como mediação. Presença de código não prova uso.
2. **`app-ads.txt` do desenvolvedor** (`https://<site-do-dev>/app-ads.txt`): linhas `DIRECT` mostram contas próprias em cada rede. O arquivo cobre todos os apps do desenvolvedor, não um app só.
3. **Página da loja:** compras no app com preço local, rótulo de privacidade ("dados usados para rastrear") e classificação etária.
4. **Estudos de caso das redes** (AdMob, InMobi, DT Exchange, Moloco, PubMatic): datas de entrada de formato e citações de executivos. São autodeclarados pelo fornecedor.
5. **Estimativas de mercado** (Sensor Tower, AppMagic, Appfigures): downloads, DAU e receita. Fontes divergem muito. Mostre todas, lado a lado.
6. **Observação manual:** a única fonte para frequência real (carência, intervalo, teto). Escreva um protocolo com dois aparelhos, gravação de tela e planilha por evento.

## Truques práticos

- O WebFetch do Exodus pode devolver lixo. Use `curl` para um diretório isolado e extraia o texto do HTML com Python `-I`.
- PDF de relatório de eCPM costuma trazer os gráficos como JPEG. Extraia os streams `/DCTDecode` com um script stdlib e leia a imagem.
- Grave tudo que baixar num diretório próprio, separado dos scripts.

## O que NÃO funcionou

- AppBrain e a página da Google Play responderam 403 ou vieram truncadas pelo WebFetch.
- O texto dos PDFs da Appodeal e da TopOn não saiu por decompressão simples. Só as imagens dos gráficos deram os números.
- Nenhuma fonte pública trouxe carência, intervalo mínimo ou teto diário de intersticial. Uma análise de terceiros diz que as regras do Block Blast chegam do servidor e mudam por usuário. Por isso, a cadência fica para a observação manual.
- Análises que fizeram engenharia reversa entram só como fonte secundária, com confiança baixa.

## Conexões
- [[Receita de Anúncio de Rede Escala com Tempo de Tela, Não com Usuários]]
- [[Screenshot de UI Comprime Melhor com Quantização de Cores que com JPEG]]
