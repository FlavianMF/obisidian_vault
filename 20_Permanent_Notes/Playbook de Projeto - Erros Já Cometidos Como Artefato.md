---
title: Playbook de Projeto - Erros Já Cometidos Como Artefato
type: pattern
tags: [documentation, agentic-ai, dev-workflow, traps, onboarding, project-methodology]
created: 2026-09-11
provenance: orbita-platform
project: orbita-platform
---

# Playbook de Projeto - Erros Já Cometidos Como Artefato

Um documento por projeto, em `docs/projeto/Playbook-de-Desenvolvimento.md`, com uma função
só: **uma sessão nova não repete um erro que outra sessão já pagou**. Peça 8 da
[[Cadeia de Artefatos de Projeto - Intenção, RFC, Plano de Fase]].

É o oposto do [[PRD]] e da RFC em todos os eixos: tático em vez de estratégico, transversal
em vez de por entrega, append-only em vez de estável, e escrito *depois* do erro em vez de
antes da decisão. Por isso é documento separado — misturar com a RFC faz os dois
envelhecerem juntos.

## Por que ele existe num projeto com agente

Modelo de linguagem chega em qualquer projeto com conhecimento de treinamento sobre a stack,
e esse conhecimento **está desatualizado ou é genérico demais** exatamente nos pontos que
custam caro. Três exemplos reais do `orbita-platform`, todos casos em que a memória de
treinamento estava confiantemente errada:

- `middleware.ts` foi renomeado para `proxy.ts` nesta versão do Next — a API é a mesma, o
  nome não.
- A biblioteca de UI usa a prop `render`, não `asChild`; usar `asChild` gera dois `<button>`
  aninhados e erro de hidratação **em runtime**, não erro de tipo.
- `zod` v4 trocou `required_error` por um único parâmetro `error`; o código antigo compila e
  a mensagem customizada simplesmente nunca dispara.

A regra que o playbook impõe nesses casos: **leia o pacote instalado**
(`node_modules/<lib>/dist/…`, a documentação que vem embutida), não a documentação de memória.

## Eixos

Os seis que emergiram, e valem para qualquer stack:

1. **Ambiente, container e git** — como rodar teste sem tocar o ambiente do usuário, qual
   volume preserva o quê, onde cada container está montado (`docker inspect`, porque já
   apontaram para diretórios diferentes na mesma sessão), como validar uma worktree ao vivo.
2. **Testes** — armadilhas do runner e do DOM sintético, ordem de import de mock, o que o
   teste unitário **não** pega, flakiness ambiental × regressão real.
3. **Particularidades desta versão desta stack** — o eixo mais valioso, e o único cujo
   título deve ser agressivo o bastante para ser lido: no `orbita-platform` chama-se
   *"Este Next.js Não é o Que Você Conhece"*.
4. **Decisões de escopo** — quando perguntar em vez de adivinhar; preferir reconstruir dado
   a partir do que já existe em vez de criar tabela nova.
5. **Segurança** — as armadilhas que um teste verde não pega. Filtro `undefined` em ORM não
   nega acesso, devolve tudo. Checagem de papel não é isolamento de tenant. Header de
   política de recurso imposto pelo navegador não reproduz em teste de servidor.
6. **Documentação** — a regra de manter a cadeia viva.

## Critério de entrada

Só entra item que **custou uma sessão** — não dica de estilo, não preferência. E cada item
traz:

- o **sintoma** como ele aparece (incluindo quando a falha é silenciosa: "cai no host padrão
  sem erro, só o conteúdo errado");
- a **causa**;
- o **comando exato** que reproduz ou corrige, copiável;
- o **link para a nota da etapa** onde o caso completo está (`(E5)`, `(E9b)`, `(Etapa 11)`).

Item que não passa nesse filtro polui o documento e faz ninguém ler o que importa.

## Entrada preferida: a falha silenciosa

O item mais valioso do playbook não é o erro que explode — é o que **passa**. Exemplo real:
`request.nextUrl.hostname` é populado corretamente numa requisição sintética de teste, mas
fica fixo em `"localhost"` no servidor de desenvolvimento real, não importa o `Host`
recebido. Um roteamento por host escrito sobre ele passa 100% dos testes unitários e não
roteia nada em execução real. Nenhum linter, nenhum typecheck e nenhuma suíte pega isso; só
subir uma instância descartável e chamar com o host resolvido para `127.0.0.1`.

Sempre que um item desses entra, ele vem acompanhado da **contramedida no processo**, não só
do conserto pontual: neste caso, "valide roteamento por host ao vivo antes de considerar
pronto; não confie só na suíte".

## Manutenção

- Cresce a cada etapa; item obsoleto **não é apagado, é marcado**. Quando as imagens Docker
  do projeto mudaram de nome, o item antigo ganhou um parágrafo "estas imagens não existem
  mais neste host — o padrão atual é `<novo>`; substitua nos comandos acima", porque os
  comandos ao redor continuavam corretos.
- É citado no prompt de início de sessão do `index.md`, com a instrução direta: *"não repita
  um erro que já está documentado lá"*.
- O que for **generalizável para além deste projeto** sobe para o vault como nota `trap` ou
  `pattern` no fim da sessão — é a mesma cadência de destilação da skill `second-brain-sync`.
- **Essa manutenção falha em silêncio quando não está amarrada no procedimento.** Medido em campo:
  o catálogo para de ser escrito antes de o aprendizado parar, e passa a não ser lido — ver
  [[O Catálogo de Armadilhas Para de Crescer Antes do Aprendizado Parar]].

## 🔗 Conexões
- [[O Catálogo de Armadilhas Para de Crescer Antes do Aprendizado Parar]] (como ele falha na prática)
- [[Cadeia de Artefatos de Projeto - Intenção, RFC, Plano de Fase]]
- [[Nota de Conclusão de Etapa é Entregável, Não Relatório]]
- [[Plano de Fase em Etapas Mescláveis]]
- [[Documentação Desatualizada é Bug, Não Dívida]]
- [[Padrão de Documentação Agêntica Local]]
- [[Engenharia de Sistemas Agêntica]]
