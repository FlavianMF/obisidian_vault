---
title: Cadeia de Artefatos Aplicada a Projeto de Conteúdo e Marca
type: pattern
tags: [project-methodology, conteudo, marca, prd, rfc, plano-de-fase, consultoria]
created: 2026-09-14
provenance: projetos_insta
project: projetos_insta
---

# Cadeia de Artefatos Aplicada a Projeto de Conteúdo e Marca

A [[Cadeia de Artefatos de Projeto - Intenção, RFC, Plano de Fase]] nasceu em projeto de
software (`orbita-platform`) e parecia presa a ele: worktree, suíte de testes, migração de
banco. Aplicada em `projetos_insta` — lançamento de um perfil profissional de Engenharia de
Sistemas do zero — a cadeia funcionou inteira, com **duas traduções** e nenhuma perda.

## O que traduz

| Peça de software | Equivalente em projeto de conteúdo |
|---|---|
| Entidade de domínio | Átomo de conteúdo, publicação, pilar, canal, lead, oferta |
| Caso de uso `UCn` | Jornada do público: ser encontrado na busca, salvar, pedir a isca, agendar |
| Requisito com teste automatizado | **Requisito com aceite observável**: "aparece no top 10 da busca in-app até o dia 60" |
| Etapa mesclável `En` | Entrega fechável sozinha: perfil no ar, 30 dias publicados, isca ligada |
| Teste de regressão | Registro datado de métrica por publicação |
| Teste negativo | Restrição ética: "nenhuma publicação usa material sob NDA" |

## As duas coisas que mudam

1. **"Aceite" deixa de ser suíte verde e vira observação datada.** Isso é mais frágil, e
   por isso o aceite precisa ser escrito em forma reprovável — número, prazo, ou o teste do
   estranho ("alguém de fora lê a bio e explica o que você faz"). Aceite vago em projeto de
   conteúdo é o mesmo que etapa sem teste: fecha por cansaço.
2. **A restrição dominante é tempo humano, não complexidade técnica.** O desenho inteiro da
   operação (batch quinzenal, átomo único com N saídas, ordem de corte decidida a frio antes
   da pressão chegar) existe por causa disso. Em software a etapa é dimensionada pelo que é
   mesclável; aqui, pelo que cabe numa sessão de produção.

## Por que vale o custo

O mesmo ganho do caso original: sessão nova — agente ou a própria pessoa três meses depois —
reconstrói o estado lendo `docs/index.md`, sem arqueologia. Num projeto de marca isso importa
ainda mais que em código, porque não existe `git log` de "por que decidi falar com esse
público": a decisão só existe se estiver escrita e datada como `Dn`.

Corolário prático: **decisão de posicionamento é decisão de arquitetura**. Registrar
"ICP em camadas: alcance / oferta / validação" como `D3` datado é o que permite, 90 dias
depois, revisar com dado em vez de recomeçar com achismo — exatamente o que o
[[Framework 3 Pilares SE]] prega para produto, aplicado ao próprio negócio.

## Conexões
- [[Cadeia de Artefatos de Projeto - Intenção, RFC, Plano de Fase]]
- [[PRD]]
- [[Plano de Fase em Etapas Mescláveis]]
- [[Playbook de Projeto - Erros Já Cometidos Como Artefato]]
- [[Framework 3 Pilares SE]]
- [[Palestra_SE_Business]]
