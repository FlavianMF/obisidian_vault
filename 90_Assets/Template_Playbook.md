---
title: Template_Playbook
type: template
tags: [template, documentation, traps, agentic-ai]
created: 2026-09-11
provenance: orbita-platform
---

# Template — Playbook (`docs/projeto/Playbook-de-Desenvolvimento.md`)

Nasce vazio, na primeira etapa, e cresce sempre. Existe em **todos os níveis**, inclusive no
nível 1. Ver [[Playbook de Projeto - Erros Já Cometidos Como Artefato]].

```markdown
# Playbook de Desenvolvimento (Padrões Validados e Erros Já Cometidos)

<!-- Uma frase: registro operacional destilado das sessões. Tático (como fazer AQUI),
     enquanto a governança é estratégica (como operar em geral). -->

---

## 1. Ambiente, container e git
<!-- Como rodar teste sem tocar o ambiente do usuário; que volume preserva o quê; onde cada
     container está montado (confirmar, não presumir); como validar uma worktree ao vivo. -->

## 2. Testes
<!-- Armadilhas do runner e do DOM sintético; ordem de import de mock; o que o teste
     unitário NÃO pega; flakiness ambiental × regressão real. -->

## 3. Esta versão desta stack não é a que você conhece
<!-- O eixo mais valioso. Título agressivo o bastante para ser lido.
     Regra: leia o pacote instalado, não a documentação de memória. -->

## 4. Decisões de escopo
<!-- Quando perguntar em vez de adivinhar; preferir reconstruir dado do que já existe a
     criar tabela nova. -->

## 5. Segurança
<!-- As armadilhas que um teste verde não pega. -->

## 6. Documentação
<!-- A regra de manter a cadeia viva: nota por etapa, índice enxuto. -->

---
**Referências**: …
```

**Critério de entrada**: só item que custou uma sessão, com **sintoma** (inclusive quando a
falha é silenciosa) + **causa** + **comando exato** + **link para a nota da etapa** que o
produziu. Item obsoleto não é apagado, é marcado.

## 🔗 Conexões
- [[Playbook de Projeto - Erros Já Cometidos Como Artefato]]
- [[Nota de Conclusão de Etapa é Entregável, Não Relatório]]
