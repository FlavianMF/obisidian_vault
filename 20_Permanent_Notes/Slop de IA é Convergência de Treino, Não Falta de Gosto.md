---
title: Slop de IA é Convergência de Treino, Não Falta de Gosto
type: trap
tags: [design, frontend, agentic-ai, css, typography, armadilha]
created: 2026-09-20
provenance: impeccable
verified: 2026-09-20 via execução do detector (engine 0.1.5) sobre fixture deliberada
---

# Slop de IA é Convergência de Treino, Não Falta de Gosto

**Todo modelo treinou nos mesmos templates de SaaS, então todo modelo entrega os mesmos
tells — e pedir "capriche mais" não corrige isso, porque o problema não é esforço, é
distribuição.** A correção é nomear os defaults e detectá-los. Esta nota é o catálogo;
a ferramenta que o executa é [[Impeccable]].

## A armadilha

Sem direção pinada, o agente cai num de três mundos previsíveis, sempre:

1. fundo creme quente, serifa display de alto contraste, acento terracota ou vermelho-sinal;
2. quase-preto com um acento neon e bordas que brilham;
3. editorial de jornal: fio de cabelo, serifa display em itálico, micro-rótulos em mono
   tracked.

Nenhum dos três é ilegítimo — todos são legítimos **quando o brief pede**. O problema é
cair neles quando o eixo estava livre. O autoteste é curto e cruel: **se alguém consegue
adivinhar sua estética só pela categoria do produto — ou pela categoria mais a evitação
óbvia — o self-check falhou e se refaz.** Assunto "livraria" não licencia papel creme:
book cloth, linha, sobrecapa e guarda cobrem o espectro saturado inteiro, e creme é o
menor canto desse mundo.

Os tells recorrentes, por família:

- **Tipografia** — Inter, Roboto, Geist, Fraunces, Plus Jakarta Sans, Space Grotesk como
  primeira escolha; serifa display em itálico gigante; *eyebrow*/kicker acima de todo
  heading (esse é banimento, não default: nenhum brief o recompra); tile de ícone
  arredondado empilhado sobre o título; numeração `01 / 02 / 03` sem sequência real;
  hierarquia achatada; tracking abaixo de -0.04em; texto de interface abaixo de 11px.
- **Cor** — gradiente roxo→azul e ciano-sobre-escuro; halo radial no topo de página
  escura; texto cinza neutro sobre superfície colorida; gradient text em heading ou
  número; dark mode virando parede de neon.
- **Layout** — grade de cards idênticos (ícone + título + texto) como estrutura da página;
  card dentro de card; o template hero-metric (número gigante, rótulo pequeno, stats de
  apoio); espaçamento monótono; medida de linha longa demais.
- **Superfície** — `border-left` colorido grosso em card ou alerta; borda de 1px sob
  sombra larga e difusa (as duas definindo a mesma aresta); glass/blur como decoração;
  listras de `repeating-linear-gradient`; grade decorativa de fundo sem canvas por baixo.
- **Movimento** — ponto de status pulsando sem nada acontecendo; cursor piscando em texto
  estático; marquee automático; easing com bounce em diálogo; imagem que anima no hover.
- **Copy** — em-dash em toda frase; "supercharge", "world-class", "next-generation";
  a cadência de slogan ("Not a feature. A platform."); chamar coisas de "theater".

## Como detectar

```bash
# arquivos, diretório ou URL; stdout fica livre pro JSON, texto humano vai pro stderr
~/.claude/skills/impeccable/scripts/impeccable detect --json src/
# exit: 0 limpo · 2 achados · 1 falha de scan
```

Numa fixture deliberadamente ruim, o detector devolve o achado com o valor exato que
disparou (`[low-contrast] 2.7:1 (need 4.5:1) — text #999999 on #faf7f0`,
`[side-tab] border-left: 6px + border-radius: 32px`), o que torna a correção mecânica.
Algumas regras são **advisory**: aparecem em seção separada e nunca mudam o exit code,
para não travar automação.

## O que fazer

- **Pinar a direção antes de construir**, com a recusa explícita escrita: é o bloco THESIS
  de [[Contrato de Direção Antes do Código]].
- **Escolher a paleta em escala de página**, não como acento espalhado sobre fundo neutro:
  Restrained / Committed / Full palette / Drenched, decidida antes das cores concretas.
- **Escolher claro ou escuro pela cena física de uso** (quem, onde, sob que luz), nunca
  pela categoria.
- **Escolher a fonte como objeto do mundo do assunto.** As faces da lista acima não são
  proibidas — nomear uma exige uma razão que nenhuma outra face satisfaça, e "livro pede
  serifa" / "tech pede mono" é exatamente a associação que a lista existe para quebrar.
- **Não confundir restrição negativa com proibição de energia.** "Sem gamificação" exclui
  o device, não a exuberância.
- Rodar o detector e triar os achados conforme
  [[Detector Determinístico Fora do LLM como Piso de Qualidade]]. O que o scanner não
  pega — o piso de craft — continua sendo prompt.

## Conexões

O brief vence sempre: redirecionar um brief claro para o gosto do agente é falha, não
curadoria. Este catálogo não é neutro entre ferramentas: a [[Taste Skill]] prescreve `Geist`
como substituto de `Inter`, e aqui `Geist` é tell — ver
[[Skills de Design se Contradizem Entre Si, Dentro e Fora do Pacote]].
Ver também [[Modo do Visitante Escolhe o Conjunto de Regras]],
[[Anatomia de uma Landing de Agente - Posicionar Ferramenta de Pesquisa como Produto]] e
[[Design System Documentado Depois do Build, Não Antes]].
