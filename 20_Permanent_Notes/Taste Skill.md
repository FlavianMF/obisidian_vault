---
title: Taste Skill
type: concept
tags: [taste-skill, design, frontend, claude-code, skills, agentic-ai]
created: 2026-09-20
provenance: taste-skill
verified: 2026-09-20 via instalação local (~/.agents/.skill-lock.json, 13 skills, 2026-09-20T14:57Z) + tasteskill.dev + github Leonxlnx/taste-skill
---

# Taste Skill

**A Taste Skill é um pacote de 13 skills de frontend que existem para impedir o agente de
entregar a interface média do treino dele.** Não tem binário, não tem hook, não tem
arquivo de contexto de projeto: é regra em prompt, e só. Autor: Leon Lin. MIT. Repositório
`Leonxlnx/taste-skill`, site https://www.tasteskill.dev/. Resolve o mesmo problema que
[[Impeccable]] e por um caminho oposto, o que torna as duas comparáveis e **não**
combináveis.

## Instalação e topologia

```bash
npx skills add Leonxlnx/taste-skill
```

O instalador é o CLI `skills` da Vercel, não o marketplace de plugins do Claude Code. O
payload fica em `~/.agents/skills/<nome>/SKILL.md` e o harness recebe apenas symlinks em
`~/.claude/skills/`. A fonte de verdade da instalação é `~/.agents/.skill-lock.json`:
`source`, `sourceUrl`, `skillPath` upstream e um `skillFolderHash` por skill.

**Não existe string de versão em lugar nenhum** — nem no frontmatter (que tem só `name` e
`description`), nem em `package.json`, nem em tag. O único sinal de versão é o nome
`-v1` e o hash de pasta. Saber se a instalação está atualizada exige comparar hash.

## As 13 skills

O nome exposto diverge da pasta upstream, o que atrapalha rastrear o arquivo de volta ao
repositório:

| Nome instalado | Pasta upstream | Serve para |
|---|---|---|
| `design-taste-frontend` | `skills/taste-skill/` | a v2, padrão do pacote |
| `design-taste-frontend-v1` | `skills/taste-skill-v1/` | comportamento legado |
| `gpt-taste` | `skills/gpt-tasteskill/` | variante para GPT/Codex |
| `high-end-visual-design` | `skills/soft-skill/` | direção premium, contraste suave |
| `minimalist-ui` | `skills/minimalist-skill/` | direção editorial contida |
| `industrial-brutalist-ui` | `skills/brutalist-skill/` | direção suíça/terminal |
| `redesign-existing-projects` | `skills/redesign-skill/` | auditar e melhorar UI existente |
| `stitch-design-taste` | `skills/stitch-skill/` | gerar `DESIGN.md` para o Google Stitch |
| `image-to-code` | `skills/image-to-code-skill/` | gerar referência visual e implementar |
| `imagegen-frontend-web` | `imagegen-frontend-web` | comps de site, uma imagem por seção |
| `imagegen-frontend-mobile` | `imagegen-frontend-mobile` | telas e fluxos de app |
| `brandkit` | `skills/brandkit/` | boards de identidade de marca |
| `full-output-enforcement` | `skills/output-skill/` | proibir saída truncada |

`find-skills`, que aparece ao lado delas, é da Vercel (`vercel-labs/skills`), não do pacote.

## O que a v2 mudou

`design-taste-frontend` passou de 226 para 1206 linhas. Cinco mudanças estruturais:

1. **§0 Brief Inference** — obrigação de declarar a leitura numa linha antes de gerar, e
   de fazer **uma** pergunta de clarificação, nunca uma bateria.
2. **§1 dials com tabela de inferência e nove presets** — ver
   [[Dials Numéricos Tornam Gosto de Design um Parâmetro Declarado]].
3. **§2 mapa de design systems oficiais** com regra de honestidade: instalar o pacote
   oficial, *"do not recreate its CSS by hand"*, e um sistema por projeto.
4. **§9.G, o banimento binário do travessão**, inexistente na v1 — ver
   [[Regra Gradual é Ignorada pelo Agente, Regra Binária é Obedecida]].
5. **§13 escopo fechado** e **§14 pre-flight de 62 caixas** no lugar das 7 da v1.

## Limites

Sem subsistema de acessibilidade: existem checagens pontuais de contraste WCAG AA em botão
e formulário, e nada além disso. A §12 "Block Library" é só um contrato de schema — o
diretório `blocks/` não existe em disco. E o pacote inteiro assume React/Next com
Tailwind v4.

Duas armadilhas medidas, cada uma com nota própria:
[[Skill Monolítica Gasta o Contexto Antes de a Tarefa Começar]] e
[[Skills de Design se Contradizem Entre Si, Dentro e Fora do Pacote]].

## 🔗 Conexões

- [[Impeccable]] — a alternativa instalada, com detector, hooks e contexto durável.
- [[Contrato de Direção Antes do Código]] e [[Modo do Visitante Escolhe o Conjunto de Regras]]
  — o mesmo problema resolvido por prosa e por categoria.
- [[Slop de IA é Convergência de Treino, Não Falta de Gosto]] — o catálogo de tells que as
  duas skills atacam.
