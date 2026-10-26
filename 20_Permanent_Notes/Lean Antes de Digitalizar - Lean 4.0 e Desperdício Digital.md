---
title: Lean Antes de Digitalizar - Lean 4.0 e Desperdício Digital
type: pattern
tags: [lean, industria-4.0, digital-lean, iot, pme, kaizen, metricas]
created: 2026-10-23
provenance: residencia_cariri_projects
seen_in: [residencia_cariri_projects]
verified: 2026-10-23 via pesquisa web (Tortorella & Fettermann 2018, Tortorella et al. 2019, Tsukada et al. 2024, Romero et al. 2018, Powell et al. 2021, Hammer 1990; resumos)
confidence: low
---

# Lean antes de digitalizar — Lean 4.0 e desperdício digital

**Padrão**: antes de pôr sensor, tablet ou câmera num processo, escreva o problema do
processo e tire o desperdício óbvio. A tecnologia entra para **medir e sustentar** um
processo enxuto, não para registrar mais rápido um processo ruim.

## Evidência

- **Tortorella & Fettermann (IJPR, 2018; 110 empresas brasileiras)**: práticas lean se
  associam a I4.0, e a implantação conjunta dá ganho maior.
- **Tortorella, Giglio & van Dun (IJOPM, 2019; 147 empresas brasileiras)**: adoção
  **puramente tecnológica** não gera resultado que se destaque.
- **Tsukada, Ibusuki et al. (IJLSS, 2024; 50 PMEs do Japão e do Brasil)**: gestores
  brasileiros dizem que lean é pré-requisito; processo com desperdício não fica produtivo
  só por ser digitalizado. Evidência qualitativa.
- **Powell et al. (APMS, 2021)**: "Lean first … then digitalize", com 3 PMEs.
- **Buer, Strandhagen & Chan (IJPR, 2018)**: revisão sistemática; os dois paradigmas
  compartilham controle descentralizado.
- **Romero et al. (APMS, 2018)**: cria o termo **desperdício digital**: não usar uma
  capacidade digital disponível, ou usá-la em excesso (dado coletado que ninguém olha).
- O desenho do Senai segue a mesma ordem: o piloto digital (Indústria Mais Avançada) atendeu
  só empresas que já tinham passado pelo lean. Ver
  [[Brasil Mais Produtivo - Lean em PMEs com Indicador Único por Linha]].

## CTQs de dado (para projeto de digitalização)

Quando o produto do projeto é um fluxo de dado, meça o dado:
- **Latência** do evento até o painel da gestão (p95).
- **Cobertura**: % do tempo planejado com estado conhecido; % de paradas acima de X min com
  motivo registrado.
- **Acurácia** da contagem: erro % por lote contra auditoria independente.
- Perda de mensagens e uptime do coletor.
- Tempo de apontamento por operador (medida de equilíbrio).
- **Número de ações kaizen originadas do dado**: prova de que o dado foi usado.

## O que NÃO funcionou

- **Automação sem enxugar**: Hammer (HBR, 1990) chama de "pavimentar trilhas de vaca";
  reengenharia antes de automatizar.
- **Adoção só tecnológica**: Tortorella et al. (2019) mostram que tecnologias de processo
  chegam a enfraquecer o efeito de práticas de setup quando entram sem o lean.
- **Painel sem dono**: dado digital que ninguém revisa vira desperdício digital (Romero et
  al., 2018).
- Na residência PNAAT Cariri, 5 dos 8 decks de 16/10/2026 partiram da tecnologia (tablet,
  totem, câmera, sensor) sem análise de causa. Ver
  [[Kaizen em Residência de 3 Meses - CTQ de Projeto vs CTQ de Negócio]].

## Fontes

- Tortorella & Fettermann, IJPR, 2018 — https://ideas.repec.org/a/taf/tprsxx/v56y2018i8p2975-2987.html
- Tortorella, Giglio & van Dun, IJOPM, 2019 — https://emerald.com/insight/content/doi/10.1108/IJOPM-01-2019-0005/full/html
- Tsukada et al., IJLSS 15(5), 2024 — https://emerald.com/insight/content/doi/10.1108/IJLSS-08-2023-0149/full/html
- Powell et al., "Lean First … then Digitalize", APMS, 2021 — https://dl.ifip.org/hal-04117661v1
- Buer, Strandhagen & Chan, IJPR, 2018 — https://ntnuopen.ntnu.no/ntnu-xmlui/handle/11250/2581150
- Romero et al., APMS, 2018 — https://dl.ifip.org/hal-02177854v1
- Rossini et al., IJAMT, 2019 — https://re.public.polimi.it/handle/11311/1113676
- Hammer, "Reengineering Work: Don't Automate, Obliterate", HBR, 1990 — https://folk.idi.ntnu.no/thomasos/paper/hammer_reengineering.pdf

Mapa: [[Kaizen e Melhoria Contínua]].
