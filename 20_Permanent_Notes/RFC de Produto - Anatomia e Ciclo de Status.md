---
title: RFC de Produto - Anatomia e Ciclo de Status
type: pattern
tags: [rfc, adr, architecture-decision, documentation, traceability, project-methodology]
created: 2026-09-11
provenance: orbita-platform
project: orbita-platform
---

# RFC de Produto - Anatomia e Ciclo de Status

Formato de RFC validado no `orbita-platform` (8 RFCs cobrindo uma fase inteira, da
arquitetura de subdomínios ao painel administrativo). É o artefato de *como*, enquanto o
[[PRD]] é o de *o quê* — ver [[Cadeia de Artefatos de Projeto - Intenção, RFC, Plano de Fase]].

Diferença para um ADR clássico: a RFC aqui **não é só o registro de uma decisão tomada**, é
o desenho que a etapa vai implementar. Ela é escrita antes do código e atualizada quando a
implementação a contraria.

## Numeração e localização

- Diretório único: `docs/escopo/rfc/`. Nunca espalhada.
- Nome: `RFC-NNN-Titulo-Em-Kebab-Case.md`, três dígitos, sequencial e **imutável** — número
  não se recicla nem se reordena.
- **`RFC-000` é reservada à visão da fase.** É ela que registra as decisões de produto e
  mapeia as demais.

## Metadata: linha 3, não frontmatter

Documento de projeto não usa frontmatter YAML (essa é convenção do vault, não do repo). A
metadata é a terceira linha, em negrito, separada por `·`:

```markdown
# RFC-002 — Identidade Unificada e Papéis

**Status**: Implementado (E0/E1 + blindagem de tenant revisada em E9a) · **Data**: 2026-07-17 · **Decisões**: D5, D7 do [RFC-000](./RFC-000-Visao-Fase-2-Area-Consultor.md)
```

Campos observados: `Status` e `Data` sempre; `Decisões` (quais `Dn` do RFC-000 esta RFC
detalha), `Origem` (documento de intenção, escopo, análise operacional) e `Aplicação`
(os arquivos de configuração que fazem a decisão valer — `.dependency-cruiser.cjs`,
`eslint.config.mjs`) conforme o caso.

## Vocabulário de status — fechado

`Aceito` · `Implementado (E0/E1 + revisado em E9a)` · `Implementado parcialmente (cobrança
fora de escopo por D8)`.

Não existe `draft` nem `proposto` neste método, e a ausência é deliberada: a RFC nasce de
uma sessão de curadoria com o usuário e é aprovada em bloco antes de virar arquivo. Se ela
ainda está em debate, o debate acontece na conversa, não num documento com status de
rascunho que ninguém sabe se vale.

O `Status` é **reescrito** quando a etapa que implementa a RFC fecha — citando a etapa, não
só a data. É isso que permite perguntar "onde isto foi implementado?" e ter resposta sem
`git log`.

## Correção sem reescrita

Quando a implementação contraria a RFC, o texto original **fica**. Entra um blockquote logo
abaixo da metadata:

```markdown
> **Nota de implementação (E0, 2026-07-17)**: o Next 16 depreciou `middleware.ts` em favor
> de `proxy.ts`; o mecanismo descrito abaixo vale, o nome do arquivo mudou.
```

Apagar o texto original destrói a informação mais cara do documento: por que se acreditava
naquilo. Ver [[Documentação Desatualizada é Bug, Não Dívida]] — o alvo é a nota *mentir*,
não a nota *ter história*.

## Anatomia — RFC-000 (visão da fase)

```
# RFC-000 — Visão da <Fase>: <Tema>
**Status** · **Data** · **Origem**

## 1. Contexto e Estratégia          o que a fase anterior entregou, que ator abre agora, qual é a aposta de negócio
## 2. Decisões de Produto            tabela | # | Tema | Decisão | RFC |  — D1..Dn, datadas
## 3. Mapa das RFCs da Fase          tabela | RFC | Título | Domínio |
## 4. Fora de Escopo da Fase         obrigatória
## 5. Requisitos Transversais        herdados da governança: TDD, cobertura, segurança, identidade visual
## 6. Riscos Principais              tabela | Risco | Impacto | Mitigação | — mitigação linkando a RFC/§ que a executa
**Referências**
```

A **tabela de decisões é o contrato da fase**. Cada linha tem número (`D7`), tema, a decisão
em uma frase e o link para a RFC que a detalha. Decisão revisada não some: vira
"**Revisada**: cadastro self-service com aprovação … (a decisão original era invite-only;
revisada para melhorar a operação)". Quem lê depois vê a mudança, não só o resultado.

## Anatomia — RFC temática

```
# RFC-00N — <Título>
**Status** · **Data** · **Decisões**: D5, D7 do [RFC-000]
> **Nota de implementação (En, data)**: …          (opcional, quando a realidade divergiu)

## 1. Problema                       o que dói hoje, em concreto
## 2. Decisão                        uma frase, depois o detalhe
### 2.1 Modelo de dados              schema proposto (Prisma/SQL/tipos), marcado como *proposto*
### 2.2 …
## 3. Migração                       quando há dado existente — "a parte crítica", em passos com regressão entre eles
## 4. Impacto no código existente    o que quebra, o que é reescrito
## 5. Testes / Como é verificado     inclusive os testes negativos obrigatórios
## 6. Segurança                      em app com dado sensível, seção própria
## 7. Alternativas rejeitadas        obrigatória
```

Seções opcionais conforme o domínio: `Desenho` com subseções por camada, `Fora desta
primeira entrega`, `Evolução futura`, `Rotas backend (resumo)`.

## As duas seções que ninguém quer escrever e que salvam a fase

**`Alternativas rejeitadas`** — o que foi considerado e por que não. É o que impede
redebater a mesma decisão seis meses depois, e é a única defesa contra uma sessão nova
"melhorar" uma escolha deliberada por não saber que era deliberada.

**`Migração`** — em RFC que mexe em dado existente, é a parte crítica, e vai em passos com
suíte de regressão verde **entre cada passo**, não num bloco só. Migração destrutiva se
desenvolve contra banco descartável, e a aplicação no banco real fica com o usuário.

## 🔗 Conexões
- [[Cadeia de Artefatos de Projeto - Intenção, RFC, Plano de Fase]]
- [[PRD]]
- [[Plano de Fase em Etapas Mescláveis]]
- [[Nota de Conclusão de Etapa é Entregável, Não Relatório]]
- [[Documentação Desatualizada é Bug, Não Dívida]]
- [[Análise de Trade-off (Trade Study)]]
