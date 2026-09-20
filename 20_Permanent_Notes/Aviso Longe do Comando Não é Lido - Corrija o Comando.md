---
title: Aviso Longe do Comando Não é Lido — Corrija o Comando
type: pattern
tags: [documentation, agentic-ai, dev-workflow, playbook, onboarding, technical-writing]
created: 2026-09-20
provenance: orbita-platform
project: orbita-platform
---

# Aviso Longe do Comando Não é Lido — Corrija o Comando

## O padrão

Quando um comando de exemplo na documentação fica obsoleto, o reflexo é
**adicionar um aviso**: "a imagem X não existe mais, substitua por Y nos
comandos acima". É barato, não reescreve história e parece seguro.

Não funciona. O aviso e o comando que ele corrige competem por atenção em
lugares diferentes do documento, e quem está executando lê o comando — é para
isso que abriu o arquivo. Se o aviso estiver 40 linhas adiante, no último
terço de uma seção longa, ele será lido **depois** de o comando já ter
falhado, se for lido.

Caso real: um Playbook de projeto avisava, no fim da §1, que as imagens Docker
citadas nos sete comandos daquela mesma seção tinham morrido numa renomeação
do repositório. Seis etapas depois, uma sessão nova rediscobriu o problema do
zero — rodou o comando quebrado, investigou a falha, reproduziu contra a
branch principal para provar que não era regressão — e só então achou o aviso.
Custo: uma investigação inteira, para uma informação que já estava no arquivo
que a sessão tinha lido.

## A regra

**Corrija o comando. O aviso, no máximo, sobrevive para o que não cabe no
comando.**

No caso real, o desdobramento certo foi:

- os sete `docker run` passaram a citar a imagem correta **literalmente** —
  nada a substituir, nada a lembrar;
- o bullet remanescente ficou só com a parte que **nenhum comando de exemplo
  consegue carregar**: a explicação de *por que* aquela imagem exige zerar
  certas variáveis de ambiente antes de rodar a suíte.

O teste para decidir: *o leitor consegue copiar e colar e dar certo?* Se sim,
o aviso é supérfluo. Se não, o aviso precisa estar **colado ao comando**, não
em outra seção.

## Por que a tentação existe

Editar o comando parece arriscado ("e se o nome antigo ainda servir em algum
contexto?") e o aviso parece conservador. É o contrário: o comando errado é
que é o risco, porque é ele que vai ser executado. Notas **históricas** — que
descrevem o que era verdade numa data — podem e devem manter o nome antigo;
documentação **operacional**, que existe para ser executada, não.

Relacionado: [[O Catálogo de Armadilhas Para de Crescer Antes do Aprendizado Parar]],
[[Playbook de Projeto - Erros Já Cometidos Como Artefato]],
[[Notas de Análise Envelhecem em Dias - Reverificar no Código Antes de Apresentar]],
[[Imagem de Deploy Carrega ENV que Quebra Teste de Valor Default]].
