---
title: Rubrica em Prosa Vira Gabarito de Evidência
type: pattern
tags: [education, grading, rubric, agentic-ai, documentation, reproducibility]
created: 2026-09-17
provenance: correcoes_docs_tcc
project: correcoes_docs_tcc
verified: 2026-09-17 via aplicação do gabarito em 16 repositórios (ver seção final)
---

# Rubrica em Prosa Vira Gabarito de Evidência

Rubrica acadêmica é escrita em adjetivos — "documentação primorosa", "código pouco legível",
"repositório organizado". Adjetivo não se aplica duas vezes do mesmo jeito: o mesmo repositório
recebe notas diferentes dependendo do dia e da ordem de leitura. O passo que falta entre a rubrica e
a correção é um **gabarito**: um documento intermediário que traduz cada nível em evidência
localizável no repositório.

Destilado de `correcoes_docs_tcc` (correção conversacional, um repo por vez), irmão menor de
[[Validação Acadêmica Automatizada]] (pipeline em massa do [[hermes_validator]]). O que se replica
entre os dois não é a infraestrutura — é a rubrica-como-artefato e o gate humano.

## As quatro regras que fazem o gabarito funcionar

**1. Eixos de evidência vêm do enunciado, não da rubrica.** A rubrica diz o nível; o enunciado diz
o que tinha que ser entregue. Cada artefato obrigatório vira um eixo (`E1..En`) com uma coluna
"como verificar no clone". A rubrica sozinha não é verificável; o enunciado sozinho não é graduado.

**2. O nível é o menor que a evidência sustenta.** Eixo excelente não compensa eixo ausente. Sem
essa regra escrita, a média informal sobe a nota de toda entrega mediana com um detalhe brilhante.

**3. Evidência localizada ou nada.** Toda linha da avaliação cita `arquivo:linha`; toda ausência
cita a busca que a provou ("nenhum `.fzz`, `.sch`, `.kicad_sch` ou imagem de circuito na árvore").
Afirmação sem localização não sobrevive a uma contestação do aluno — e o agente é bom demais em
produzir prosa plausível sem lastro.

**4. "Se aplicável" precisa ser explícito, senão vira desconto fantasma.** Enunciado que pede
esquemático elétrico *se aplicável* exige uma regra escrita: projeto sem hardware registra `n/a`
com justificativa e **não** perde ponto. Sem isso o aluno é penalizado por não entregar o que não
lhe foi pedido, e ninguém percebe porque o desconto acontece por omissão.

## O gate humano tem uma forma específica

Não é "o professor revisa depois". É um campo de status no documento:

- A nota do agente nasce **`PROPOSTA`**.
- Vira **`CONFIRMADA`** quando o professor preenche o bloco de nota final.
- **A proposta nunca é apagada quando a nota manual diverge** — ficam as duas, lado a lado. A
  divergência *deve ser* o dado mais útil do sistema: é ela que mostraria onde o gabarito está
  errado. **Hipótese ainda não testada**: depois de 16 correções, nenhuma nota foi confirmada, e
  portanto não existe uma única divergência para ler. Ver a seção final.
- Reexecutar a correção sobre grupo já `CONFIRMADA` reporta conflito e não sobrescreve.

## O gabarito é versionado, e muda só para frente

O gabarito carrega número de versão. Mudou regra de decisão, subiu a versão — e avaliações já
confirmadas sob a versão anterior **não são renotadas**. Renotar retroativamente é reabrir nota
fechada com aluno; a divergência de critério fica registrada, não apagada. Mesmo espírito da catraca
de cobertura do [[Checklist de Bootstrap de Workflow de Desenvolvimento]]: o valor de hoje é o piso
de amanhã, e baixá-lo exige justificativa escrita.

Cada avaliação também registra o **commit avaliado** do repositório do aluno. Sem isso não há como
responder "esta nota olhou para qual estado do repo" — o aluno pode ter empurrado commits depois.

## O que 16 correções mostraram

Primeiro lote real: 16 repositórios em 1h43, todos sob a **Versão 1** do gabarito.

**A v1 sobreviveu intacta.** Nenhuma regra de decisão precisou mudar em 16 repositórios — nenhum
commit no gabarito, no procedimento ou no `CLAUDE.md` depois do commit fundador. O protocolo de bump
de versão descrito acima é, portanto, **desenho não exercido**: correto no papel, sem uma única
aplicação que o valide.

**O gate humano não fechou.** 16 de 16 notas continuam `PROPOSTA`. A parte cara do sistema — a
proposta que não se apaga, o conflito reportado em reexecução sobre nota confirmada — é **código
morto não testado**. O gargalo do fluxo não é gerar a proposta; é o humano voltar para carimbar.

**A decisão de nota real vazou para fora do gabarito.** O playbook tático do projeto desenvolveu uma
gradação de severidade que o gabarito não tem: achado que *rebaixa* nível (bate no gatilho "omite
passo essencial"), achado que *não rebaixa* e só pesa na fronteira 3 vs. 4, e achado que *não supre
eixo ausente*. Essa taxonomia decidiu notas. Ela não está em nenhuma linha da rubrica traduzida, e o
procedimento de correção nem manda ler o playbook — ver
[[O Catálogo de Armadilhas Para de Crescer Antes do Aprendizado Parar]]. **Gabarito que não absorve
a gradação de severidade delega a decisão para um documento que ninguém é obrigado a abrir.**

**A regra do "se aplicável" foi útil pelo lado que ninguém antecipou.** Zero eixos marcados `n/a`:
os 16 projetos tinham hardware, e o desconto fantasma que a regra existe para impedir nunca teve
chance de acontecer. Quem decidiu duas notas foi a *outra* metade da mesma regra — "com hardware e
sem esquemático: teto nível 2". Regra escrita contra um risco, paga por outro.

**Um eixo fez quase todo o trabalho.** Dos cinco eixos, o README passo a passo decidiu 6 das 7 notas
baixas; a distribuição resultante esvaziou o nível intermediário — ver
[[Nível Intermediário Vira Vale Quando o Topo Pede Tudo do Anterior Mais X]].

**O que sustentou a evidência localizada** foi a checagem de ligação, não de presença:
[[Toda Checagem Barata Passa - Documentação Falha na Ligação, Não na Presença]].

**Higiene que escapou:** 4 das 16 avaliações não carimbaram a versão do gabarito sob a qual foram
julgadas. Se a v2 chegar, esses quatro ficam sem rastro de critério — exatamente o que o
versionamento existe para impedir. Carimbo de versão precisa estar no **template**, não na memória
de quem escreve.

## 🔗 Conexões
- [[Validação Acadêmica Automatizada]] (o irmão em massa)
- [[hermes_validator]]
- [[Documentação Desatualizada é Bug, Não Dívida]]
- [[Checklist de Bootstrap de Workflow de Desenvolvimento]]
- [[Cadeia de Artefatos de Projeto - Intenção, RFC, Plano de Fase]]
- [[Toda Checagem Barata Passa - Documentação Falha na Ligação, Não na Presença]]
- [[Nível Intermediário Vira Vale Quando o Topo Pede Tudo do Anterior Mais X]]
- [[O Catálogo de Armadilhas Para de Crescer Antes do Aprendizado Parar]]
- [[correcoes_docs_tcc]]
