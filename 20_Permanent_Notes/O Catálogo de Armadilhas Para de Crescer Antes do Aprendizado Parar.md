---
title: O Catálogo de Armadilhas Para de Crescer Antes do Aprendizado Parar
type: trap
tags: [documentation, agentic-ai, dev-workflow, traps, project-methodology]
created: 2026-09-17
provenance: correcoes_docs_tcc
project: correcoes_docs_tcc
verified: 2026-09-17 via git log de docs/playbook.md e grep de citações nas 16 avaliações
---

# O Catálogo de Armadilhas Para de Crescer Antes do Aprendizado Parar

[[Playbook de Projeto - Erros Já Cometidos Como Artefato]] descreve o artefato e a cadência. Esta
nota é o que aconteceu quando ele rodou num lote real de 16 unidades de trabalho em 1h43: **o
playbook falhou pelas duas pontas, e as duas falhas foram silenciosas.**

## Ponta 1 — parou de ser escrito

Oito entradas entraram entre 09:57 e 10:43, uma por unidade corrigida, com disciplina verificável
(entrada e avaliação com o mesmo timestamp de commit, como manda a regra do "mesmo ciclo"). Depois
das 10:43: **zero**, embora a correção tenha seguido até 11:15 e mais nove unidades tenham passado.

A leitura confortável é saturação — o domínio tem um número finito de modos de falha e eles
acabaram. **A evidência derruba isso**: duas das últimas unidades trouxeram armadilhas
estruturalmente novas (variáveis de ambiente documentadas e nunca lidas pelo código; build que
quebra por grafia de header divergente em filesystem case-sensitive) e as duas ficaram registradas
**só dentro da avaliação daquela unidade**, onde ninguém procura.

A causa é estrutural, não epistêmica: **quem escreve a entrada é o mesmo que está fazendo o
trabalho**, e escrever a entrada é o passo sem consequência imediata — o primeiro a cair quando o
lote vira rotina. Aqui coincidiu com a troca do executor (as oito entradas são todas do mesmo
modelo; as nove unidades seguintes, de outro). Confundimento honesto: **não dá para separar cansaço
de lote, mudança de executor e saturação real com um lote só** — é o problema de atribuição de
[[Sem Log de Atribuição Por Trilha, Desenho Paralelo Não Prova Eficácia Causal]].

## Ponta 2 — parou de ser lido, ou nunca começou

Das 16 correções, **4** registram ter checado alguma armadilha do playbook. As outras 12 não —
inclusive unidades processadas **depois** de a entrada relevante já existir.

Causa direta e barata de consertar: o procedimento operacional mandava ler o gabarito "inteiro,
sempre, mesmo que já lido nesta sessão", e **não mencionava o playbook em lugar nenhum**. A nota do
padrão prevê exatamente isso ("é citado no prompt de início de sessão, com a instrução direta"); o
projeto não implementou, e o custo foi 12 correções cegas para o que já tinha sido pago.

## O que fazer

- **Amarrar as duas pontas no procedimento, não na intenção.** O passo que manda ler o gabarito
  manda ler o playbook. O passo que fecha a unidade pergunta: apareceu algo que não está no
  catálogo? Sem isso, as duas caem juntas e nada acusa.
- **Tratar platô como sinal de investigar, não como licença para reduzir supervisão.** A curva de
  entradas por unidade não mede a natureza do domínio; mede a disciplina de quem está executando.
  Platô com achados novos aparecendo nas unidades individuais é o sintoma exato.
- **Medir a leitura, não só a escrita.** Contar em quantas unidades o catálogo foi citado é uma
  linha de `grep` e é o único indicador de que ele está vivo.
- O catálogo que não realimenta é custo puro: paga-se o preço de escrever e não se recebe o de não
  repetir o erro.

## 🔗 Conexões
- [[Playbook de Projeto - Erros Já Cometidos Como Artefato]]
- [[Sessões Paralelas Perdem Escrita no Índice Compartilhado]]
- [[Sem Log de Atribuição Por Trilha, Desenho Paralelo Não Prova Eficácia Causal]]
- [[Documentação Desatualizada é Bug, Não Dívida]]
- [[correcoes_docs_tcc]]
