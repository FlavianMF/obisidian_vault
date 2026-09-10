---
title: Sem Log de Atribuição Por Trilha, Desenho Paralelo Não Prova Eficácia Causal
type: pattern
tags: [research-design, methodology, mbse, llm-council, verification-validation]
created: 2026-09-10
provenance: residencia_00
---

# 🎯 Sem Log de Atribuição Por Trilha, Desenho Paralelo Não Prova Eficácia Causal

Quando um estudo roda **dois métodos em paralelo com sobreposição proposital** (ex.:
Project Model Canvas + ARCADIA cobrindo os mesmos blocos, de propósito, para
checagem cruzada — ver [[Project Model Canvas vs ARCADIA - Mapeamento]]) e a
alegação de pesquisa é "método X é eficaz" ou "X supera Y", o desenho **não
consegue sustentar essa alegação** sem um log explícito de atribuição — não importa
quão bem executado seja o resto do desenho.

## ⚠️ O problema

Sem braço de controle (não existe grupo rodando só o método A vs. só o B) e sem
registro de qual achado veio de qual trilha, é impossível isolar a contribuição
causal de cada método. Rodar 8 estudos de caso todos com o mesmo método, sem
controle, **não comprova eficácia — descreve implementação**. Um desenho
metodologicamente elegante (sobreposição proposital, checagem cruzada) sem esse log
vira, na prática, "teatro acadêmico disfarçado de rigor" — a elegância conceitual
mascara a ausência de evidência causal.

Achado de um `llm-council` (persona First Principles Thinker) rodado para avaliar a
abordagem PMC‖ARCADIA de uma residência técnica; confirmado por 4 dos 5 revisores
como o ponto mais consequente do conselho — mais que os riscos operacionais de
campo.

## ✅ A correção, de baixo custo

Duas mudanças resolvem, sem redesenhar o estudo:

1. **Registrar por achado, no momento da captura, qual trilha pegou o quê** — uma
   coluna a mais no template/formulário de campo já em uso (ex.: "achado que o PMC
   pegou e o ARCADIA não teria pego" / "achado que o ARCADIA pegou e o PMC não teria
   pego" / "achado que os dois pegaram — checagem cruzada confirmada"). Custo baixo,
   transforma alegação infalseável em defensável.
2. **Reformular a alegação da pesquisa**: de "comprova eficácia causal do método X"
   para "viabilidade/aplicabilidade do método X neste contexto real" — mantendo o
   log de atribuição como evidência de onde cada método agregou valor. As duas
   coisas podem ser verdade ao mesmo tempo: um estudo de caso múltiplo bem
   documentado, sem desenho causal estrito, ainda tem valor — só não é o mesmo valor
   que "eficácia comprovada".

## 🔗 Conexões
- [[Project Model Canvas vs ARCADIA - Mapeamento]]
- [[Corpus Multiempresa Só Vira Dataset Reaproveitável Com Consentimento Explícito]]
- [[V-Model (Vee Model)]]
