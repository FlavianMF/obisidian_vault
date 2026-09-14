---
title: Template_Prompt-de-Sessao
type: template
tags: [template, agentic-ai, onboarding, governance, session-prompt]
created: 2026-09-11
provenance: orbita-platform
---

# Template — Prompt de Início de Sessão (topo do `docs/index.md`)

Bloco que recarrega a governança inteira do projeto em qualquer sessão nova — agente ou
humano. Fica **no topo do índice**, não num arquivo separado que ninguém abre. Derivado das
8 regras do `orbita-platform`; adaptar por stack, preservando a ordem (contexto → governança
→ isolamento → qualidade → entrega → escopo → risco do domínio).

```markdown
## 🤖 Prompt de Início de Sessão

Você está continuando o desenvolvimento de **{{title}}**. Antes de qualquer código:

1. Leia `docs/index.md` por completo e as notas linkadas em `docs/projeto/` para entender o
   estado atual do produto e do que já foi construído.
2. Siga a governança de [<arquivo de governança>](…) e o **[Playbook de Desenvolvimento](./projeto/Playbook-de-Desenvolvimento.md)**
   — ele registra padrões já validados e erros já cometidos em sessões anteriores.
   **Não repita um erro que já está documentado lá.**
3. Trabalhe sempre em `git worktree` isolado; nunca edite o checkout compartilhado
   diretamente. <regra de execução do projeto: container, venv, toolchain — comandos exatos
   no Playbook>.
4. TDD sempre: escreva o teste antes da implementação. <piso de cobertura e onde ele está
   definido>.
5. Todo o trabalho — commits inclusive — fica na worktree isolada.
6. Ao concluir uma funcionalidade: rode a suíte completa + typecheck, sincronize `docs/` com
   uma nota nova em `docs/projeto/` (links densos, seção "Próximos Passos"). **Não mescle e
   não reinicie serviços ao vivo** — avise que a worktree está pronta para validação e deixe
   o merge com o usuário.
7. Para decisões de escopo ambíguas e de alto impacto, pergunte com **2–3 opções concretas**
   antes de implementar — não adivinhe e refaça depois.
8. <o risco dominante deste domínio como requisito de primeira classe — ex.: "esta é uma
   aplicação financeira: trate segurança da informação como requisito de primeira classe em
   toda decisão (validação de entrada, isolamento de tenant, segredos, dependências novas)">.
```

Repetir o bloco logo abaixo como *blockquote* deixa ele legível na renderização do índice
além de copiável do bloco de código — é o que o `orbita-platform` faz.

## 🔗 Conexões
- [[Cadeia de Artefatos de Projeto - Intenção, RFC, Plano de Fase]]
- [[Playbook de Projeto - Erros Já Cometidos Como Artefato]]
- [[Checklist de Bootstrap de Workflow de Desenvolvimento]]
