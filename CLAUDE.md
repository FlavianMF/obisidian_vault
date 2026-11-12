---
title: Governança do cofre (agentes de IA)
type: meta
tags: [meta, governanca]
created: 2026-11-10
provenance: manual
---

# Governança do cofre (agentes de IA)

Este cofre é a memória de longo prazo do usuário. Estilo e estrutura: leia `META.md`.
Schema de frontmatter: `00_META/Frontmatter-Schema.md`. Regras de linkagem: `00_META/Agent-Instruction.md`.
Este arquivo só fixa as regras inegociáveis de escrita.

## Mapa

- `00_Inbox/inbox.md`: capturas rápidas por voz (`- [ ] [dd/mm HH:MM] texto`). Outros arquivos em `00_Inbox/` são candidatos do `sb`: **não os toque**.
- `10_Literature_Notes/`: fontes externas. `20_Permanent_Notes/`: conceitos atômicos (o wiki). `30_MOCs/`: mapas de conteúdo.
- `index.md`: catálogo gerado de `20_Permanent_Notes/`. Nunca edite à mão.
- `log.md`: trilha de auditoria. `outputs/`: relatórios descartáveis.

## Regras inegociáveis

1. **Permanent Notes são imutáveis.** Nunca sobrescreva nem reescreva uma nota existente. Para enriquecer, anexe ao fim da nota uma seção `### [AAAA-MM-DD] Atualização` com o fato novo e a fonte.
2. **Conflito de fatos:** não decida sozinho. Insira antes da seção afetada um callout `> [!WARNING] Conflito de Fatos Detectado em AAAA-MM-DD` com premissa existente, nova evidência e proposta. Se o conflito tocar várias notas, grave `outputs/relatorios/AAAA-MM-DD-conflito-<assunto>.md`.
3. **Nota obsoleta:** marque `status: superseded` no frontmatter e crie a nota nova com `supersedes`. Nunca apague.
4. **Proibido apagar:** não rode `rm`, não trunque arquivo e não remova registro fora de `outputs/`.
5. **Inbox:** nunca apague nem edite o texto de uma captura. Depois de processar, troque só `- [ ]` por `- [x]` na linha.
6. **Nota nova:** frontmatter YAML completo conforme o schema, com `confidence: low` e `provenance` preenchido. Nome do arquivo igual ao título. Um conceito por nota.
7. **Links:** use `[[Nome da Nota]]` (bidirecional). Linke a primeira ocorrência de cada termo. Toda nota nova entra em pelo menos um MOC de `30_MOCs/`.
8. **Auditoria:** a cada sessão de organização, anexe ao fim de `log.md` (append-only, nunca edite linhas antigas):
   `## [AAAA-MM-DD HH:MM] organizacao | <resumo de 1 linha>` e, abaixo, uma lista das notas criadas e enriquecidas.
9. **Índice:** depois de criar ou enriquecer qualquer nota perene, rode `python3 /home/flv/projetos_router/atualizar_index.py`.
