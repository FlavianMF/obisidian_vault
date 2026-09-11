---
title: Documentação Desatualizada é Bug, Não Dívida
type: pattern
tags: [documentation, dev-workflow, agentic-ai, second-brain, definition-of-done]
created: 2026-09-11
provenance: projetos_ita
project: projetos_ita
---

# Documentação Desatualizada é Bug, Não Dívida

## O problema

Nota velha não é ausência de informação — é **informação errada com aparência de
autoridade**. É pior que nota nenhuma: quem lê uma pasta vazia vai procurar a verdade no
código; quem lê um documento detalhado, bem escrito e recente **confia nele**.

Foi exatamente assim que quebrou: três apresentações foram construídas sobre notas de
análise de seis dias antes. O `git log` mostrou depois que P8/P9 tinham sido
implementados e a `v0.0.5` lançada nesse intervalo. O placar apresentado dizia **8 de 11**
propostas resolvidas; o real era **10 de 11**. As notas foram confiadas *porque* pareciam
boas. Ver [[Notas de Análise Envelhecem em Dias - Reverificar no Código Antes de Apresentar]]
para o lado da leitura; esta nota é o lado da escrita.

## O princípio

> **A nota é parte do entregável, não um artefato posterior.**
> Uma tarefa não está concluída enquanto a documentação que descreve o que você mexeu
> não voltar a ser verdadeira.

Isso não é zelo, é definição de pronto. A diferença importa: trabalho *extra* é a
primeira coisa cortada sob pressão de contexto ou de prazo; trabalho *inacabado* não é
cortado — é terminado.

## A cadência: duas fases, não uma

**Ao terminar cada tarefa — varrer as notas do projeto.** É onde a mentira nasce, porque
é a documentação que anda colada ao código.

**Ao final da sessão — sincronizar com o vault.** Destilar o que foi aprendido *e*
propagar o que a mudança invalidou lá dentro.

Juntar as duas numa só falha: sincronizar só no fim da sessão deixa a documentação local
envelhecer durante ela, e varrer só o projeto nunca corrige o conhecimento global.

## O procedimento

Antes de dizer "pronto":

1. **Liste o que tocou** — módulo, ferramenta, arquivo, versão, status de proposta,
   decisão. Essa lista é a entrada dos greps seguintes; não exige julgamento nenhum.
2. **Procure as afirmações que envelhecem.** O truque é não caçar o assunto, e sim os
   **marcadores linguísticos de estado** — é o que transforma julgamento em busca:

   ```bash
   grep -rniE "pendente|não implementado|ainda não|falta|TODO|planejado|aguardando|previsto" \
     docs/ notes/ README.md CLAUDE.md
   ```

   Mais um `grep` pelos nomes próprios do que mudou (nome da ferramenta, da classe, do
   arquivo), e atenção a **contagens e versões** — "13 tools", "v0.1.0", "3 de 11" são
   afirmações que apodrecem sem nenhuma palavra-marcador por perto.
3. **Cada acerto: ainda é verdade?** Se não, corrija **no mesmo ciclo de trabalho** —
   não vira item de backlog, não vira "depois eu arrumo".
4. **Carimbe a verificação** em afirmação de estado: `verified: AAAA-MM-DD via <comando>`
   no frontmatter. Isso torna a idade da afirmação **visível** — sem o carimbo, a
   obsolescência é invisível até alguém se queimar.
5. **Relate ao usuário o que foi atualizado** (e o que foi checado e continuava certo).
   Visibilidade cria responsabilidade e deixa o humano pegar a omissão.

## Meia-vida

A validade de uma nota é inversamente proporcional ao ritmo do desenvolvimento. Um
repositório com 40 commits em oito dias invalida documentação de status quase na mesma
velocidade em que a produz — nele, "seis dias atrás" já é história antiga.

## Onde isso vive (para não depender de boa intenção)

Uma nota dizendo "mantenha as notas atualizadas" não faz o comportamento acontecer: o
agente só lê o vault quando decide ler. Por isso a regra foi plantada onde é **obrigatório**
passar:

- `second-brain-sync` **Behavior 2** — dispara sozinho ao fim de tarefa/sessão.
- **Eixo 7** de [[Checklist de Bootstrap de Workflow de Desenvolvimento]] — é o que o
  Behavior 3 replica para o `CLAUDE.md`/`AGENTS.md`/`.cursorrules` de cada projeto.
- [[Agentic Knowledge Bridge|Agent-Instruction]] — alcança agentes que leem o vault direto.

## 🔗 Conexões
- [[Notas de Análise Envelhecem em Dias - Reverificar no Código Antes de Apresentar]]
- [[Checklist de Bootstrap de Workflow de Desenvolvimento]]
- [[Padrão de Documentação Agêntica Local]]
