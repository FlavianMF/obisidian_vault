---
title: Modo do Visitante Escolhe o Conjunto de Regras
type: pattern
tags: [design, ux, product-design, frontend, agentic-ai]
created: 2026-09-20
provenance: impeccable
---

# Modo do Visitante Escolhe o Conjunto de Regras

**A pergunta que decide as regras de uma tela não é "que tipo de produto é este?", é "o
que significa sucesso para quem chegou nesta superfície?".** [[Impeccable]] chama isso de
*mode* e reconhece quatro:

- **Persuade** — o visitante decide e age; o design **é** o produto. Landing, campanha,
  pricing. Ganhar atenção e ação é o trabalho; imagem real entra quando o brief pede.
- **Operate** — o visitante completa uma tarefa. App, dashboard, editor, admin, settings.
  Escaneabilidade, consistência, expectativa nativa da plataforma e a cena real de uso
  valem mais que expressão. A marca vive em detalhe preciso.
- **Read** — o visitante entende alguma coisa. Docs, artigo, guia, changelog. Estruturar
  para compreensão primeiro, depois tornar a leitura um lugar em que se queira ficar.
- **Experience** — o visitante está dentro da obra. Portfólio, galeria, showcase. O
  artefato lidera desde o primeiro viewport; a interface recua.

## A parte que se erra

**O modo vem da superfície pedida, não do produto que a hospeda.** A landing page de uma
ferramenta de desenvolvedor continua sendo Persuade, mesmo que o produto inteiro seja
Operate. A documentação de uma grife de moda continua sendo Read, mesmo que a marca seja
puro Experience. O índice da documentação é Read, não Persuade, por mais que ele "venda" a
doc. Errar aqui é como se importa a paleta de energia da landing para dentro do dashboard,
ou a sobriedade do dashboard para dentro da landing.

Consequência operacional: o modo é persistido **no brief daquela superfície**, nunca no
arquivo global de verdade do produto. Uma mesma base de código carrega os quatro ao mesmo
tempo, e isso não é inconsistência.

## Por que importa para agente

Sem o modo, o agente aplica uma média de todas as regras que aprendeu, e a média é
exatamente o [[Slop de IA é Convergência de Treino, Não Falta de Gosto]]. Com o modo,
regras que se contradizem deixam de se contradizer: "hierarquia ousada" é obrigação em
Persuade e ruído em Operate; "densidade de informação" é virtude em Operate e barreira em
Read. O modo transforma um conjunto de conselhos genéricos em um conjunto aplicável.

## Generaliza

O padrão é anterior a design: **derive o rulebook do critério de sucesso do usuário
naquela superfície, e persista o critério junto da superfície.** Vale para texto (um README
não é um post de blog não é um changelog), para API (endpoint de leitura em lote não é
endpoint de escrita transacional) e para relatório. Ver
[[Contrato de Direção Antes do Código]], que é onde o modo escolhido vira decisão escrita,
e [[Campo de Settings Só Deve Ser Editável Se Aplicar de Verdade]], um caso de Operate
levado a sério.
