---
title: Template_RFC
type: template
tags: [template, rfc, adr, architecture-decision]
created: 2026-09-11
provenance: orbita-platform
---

# Template — RFC temática (`docs/escopo/rfc/RFC-NNN-Titulo.md`)

Uma decisão técnica por documento. Numeração de três dígitos, sequencial e imutável.
Ver [[RFC de Produto - Anatomia e Ciclo de Status]].

```markdown
# RFC-00N — {{title}}

**Status**: Aceito · **Data**: AAAA-MM-DD · **Decisões**: D5, D7 do [RFC-000](./RFC-000-….md)
<!-- Status evolui para "Implementado (En)" ou "Implementado parcialmente (… por Dn)"
     quando a etapa fecha. Não existe draft/proposto neste método. -->
<!-- Campos opcionais: **Origem**, **Aplicação** (arquivos de config que fazem a decisão valer). -->

> **Nota de implementação (En, AAAA-MM-DD)**: …
<!-- Opcional, e só quando a implementação contrariou o texto. O texto original FICA. -->

---

## 1. Problema
<!-- O que dói hoje, em concreto. Sem solução aqui. -->

## 2. Decisão
<!-- Uma frase, depois o detalhe. -->

### 2.1 Modelo de dados (proposto)
<!-- Schema/tipos. Marcar como *proposto* enquanto a etapa não fechou. -->

### 2.2 <outra faceta do desenho>

## 3. Migração
<!-- Só quando há dado existente. Em PASSOS, com suíte de regressão verde entre cada um.
     Migração destrutiva se valida contra banco descartável; aplicar no banco real fica com
     o usuário (marcar com ⚠️). -->

## 4. Impacto no código existente
<!-- O que quebra, o que é reescrito, o que continua igual. -->

## 5. Testes / Como é verificado
<!-- Inclusive os testes negativos obrigatórios (autorização, isolamento de tenant). -->

## 6. Segurança
<!-- Seção própria quando há dado sensível. -->

## 7. Alternativas rejeitadas
<!-- OBRIGATÓRIA. O que foi considerado e por que não. É o que impede redebater em seis
     meses, e a única defesa contra alguém "melhorar" uma escolha deliberada. -->

---
**Referências**: …
```

## 🔗 Conexões
- [[RFC de Produto - Anatomia e Ciclo de Status]]
- [[Análise de Trade-off (Trade Study)]]
