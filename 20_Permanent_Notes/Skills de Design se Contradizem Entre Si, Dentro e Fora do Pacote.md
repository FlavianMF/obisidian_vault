---
title: Skills de Design se Contradizem Entre Si, Dentro e Fora do Pacote
type: trap
tags: [agentic-ai, skills, design, frontend, claude-code, armadilha]
created: 2026-09-20
provenance: taste-skill
verified: 2026-09-20 via grep cruzado em ~/.agents/skills/*/SKILL.md e ~/.claude/skills/impeccable/
---

# Skills de Design se Contradizem Entre Si, Dentro e Fora do Pacote

**Um pacote de skills não é um sistema: é uma coleção escrita em momentos diferentes, e
duas skills de domínio sobreposto não negociam entre si em tempo de execução.** Carregadas
juntas, entregam ordem e contraordem sobre a mesma decisão, e quem resolve é o modelo, em
silêncio.

## A armadilha, com os casos medidos

Dentro de `Leonxlnx/taste-skill`, instalado num comando só:

- `stitch-design-taste/DESIGN.md:52` manda usar *"distinctive modern serifs like `Fraunces`
  (…) or `Instrument Serif`"*; `design-taste-frontend/SKILL.md:180` lista exatamente essas
  duas como **banidas por padrão**, chamando-as de "the two LLM-favorite display serifs".
- `gpt-taste/SKILL.md:36` marca o hero *"Cinematic Center (Highly Preferred)"*;
  `design-taste-frontend/SKILL.md:210` evita hero centralizado sempre que
  `DESIGN_VARIANCE > 4`, e o baseline é 8.
- `redesign-existing-projects` continua no pacote fazendo o trabalho que o §11 da v2 já
  absorveu inteiro.

E o caso entre pacotes, que é o mais caro na prática, porque as duas skills estão
instaladas nesta máquina ao mesmo tempo: `design-taste-frontend/SKILL.md:169` manda trocar
`Inter` por `Geist`, `Outfit` ou `Cabinet Grotesk`; [[Slop de IA é Convergência de Treino, Não Falta de Gosto]],
destilada de [[Impeccable]], lista **`Geist`** entre os tells de
primeira escolha que denunciam design de IA. A mesma fonte é a correção de uma e o sintoma
da outra.

## Como detectar

```bash
# o mesmo termo aparecendo com sinal oposto em skills diferentes
grep -rn "Fraunces\|Instrument Serif" ~/.agents/skills/*/ 
grep -rln "Geist" ~/.claude/skills/*/ ~/.agents/skills/*/
```

O conflito aparece como duas linhas que se contradizem, não como erro. Vale rodar essa
checagem para nome de fonte, padrão de hero, paleta e regra de ícone assim que um pacote
novo entra — são os eixos em que skills de design decidem por nome próprio.

## O que fazer

- **Uma skill de direção por tarefa.** Empilhar só eixos ortogonais: `full-output-enforcement`
  não disputa nada com nenhuma delas; `minimalist-ui` e `industrial-brutalist-ui` disputam
  tudo entre si.
- **Declarar qual vence antes de começar**, e dizer o motivo na resposta, em vez de
  deixar o modelo arbitrar no meio do código.
- **Registrar a decisão num lugar durável** — o `CLAUDE.md` global, no caso de skills
  instaladas por usuário — para que a arbitragem não seja refeita a cada sessão.
- Preferir a skill que traz verificação executável: entre uma que só descreve e outra que
  tem detector com exit code, a segunda erra menos por construção
  ([[Detector Determinístico Fora do LLM como Piso de Qualidade]]).

## 🔗 Conexões

- [[Taste Skill]] — o pacote onde as três contradições internas vivem.
- [[Impeccable]] — a outra skill instalada, e o outro lado do conflito do `Geist`.
- [[Skill Monolítica Gasta o Contexto Antes de a Tarefa Começar]] — a armadilha gêmea de
  instalar um pacote inteiro de uma vez.
- [[Autoridade por Assento na Cadeia de Hooks]] — o problema resolvido no harness, onde a
  precedência é explícita em vez de emergente.
