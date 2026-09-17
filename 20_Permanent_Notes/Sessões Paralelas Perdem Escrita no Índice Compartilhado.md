---
title: Sessões Paralelas Perdem Escrita no Índice Compartilhado
type: trap
tags: [agentic-ai, orchestration, concurrency, workflow, git]
created: 2026-09-17
provenance: correcoes_docs_tcc
project: correcoes_docs_tcc
verified: 2026-09-17 via git log de correcoes_docs_tcc (commits f6fabff, baac003, 9f17952, d1aa8fe)
---

# Sessões Paralelas Perdem Escrita no Índice Compartilhado

**Sintoma.** Um fluxo agêntico desenhado como conversacional e sequencial foi executado com 3 a 4
sessões simultâneas para ganhar tempo. Cada sessão escrevia os arquivos da sua unidade de trabalho e
depois acrescentava uma linha ao índice consolidado, um arquivo único. **Quatro de dezesseis linhas
não chegaram**, e precisaram de três commits de reparo depois que alguém reparou na falta.

Nenhuma sessão errou visivelmente. Nenhum comando falhou. A linha simplesmente não estava lá.

**Causa.** O passo de consolidação é o único ponto do fluxo com estado compartilhado, e é o último
passo de cada worker — ou seja, o mais exposto a sessão que termina, é interrompida ou perde a
disputa pelo arquivo. Dois agravantes reais no mesmo lote:

- Duas correções paralelas forçaram **duas linhas num commit só**, violando a convenção do próprio
  projeto ("um grupo por commit"); o corpo do commit admite: *"separar exigiria reescrever o arquivo
  duas vezes"*.
- Um formatador de Markdown reescreveu 41 linhas do índice ao reencaixar os pipes da tabela e
  **corrompeu um link** no processo. Foi descoberto por acaso, ao consolidar a unidade seguinte — não
  havia nenhuma checagem que pegasse isso.

**O que fazer.** Com fan-out por sessão, o índice compartilhado **não é passo do worker**:

1. Cada unidade escreve só os seus próprios arquivos — nada compartilhado.
2. A consolidação é um passo serial explícito no fim do lote, ou o índice é **gerado** a partir de um
   arquivo por unidade (mesma lógica dos manifests do vault: derivado, não editado à mão).
3. O lote declara o total esperado. Sem isso o fluxo não tem como detectar que faltou alguém — é
   exatamente o caso que deixou as quatro linhas passarem.
4. Se o índice for tabela Markdown formatada, tratar reformatação como mudança suspeita: diff de 41
   linhas para acrescentar uma é sinal, não ruído.

Parente direto de [[Orquestração Híbrida de Agentes]]: a parte determinística do pipeline é
justamente a que não pode morar dentro do agente paralelo.

## 🔗 Conexões
- [[Orquestração Híbrida de Agentes]]
- [[O Catálogo de Armadilhas Para de Crescer Antes do Aprendizado Parar]]
- [[correcoes_docs_tcc]]
