---
title: "Marca local gravada antes do comando evita corrida com a releitura de estado"
type: permanent
created: 2026-11-10T14:32:40
moc: "Design de Interface com Agente"
tags: [second-brain, triagem-noturna, pattern, feat-prd2-3-onboarding]
source_inbox: "dc522f1c-marca-local-gravada-antes-do-comando-evita-corrida-com-a-rel.md"
tier: "L1"
score: 0.755
---

# Marca local gravada antes do comando evita corrida com a releitura de estado

No Flutter, o aceite de termos dispara refreshStatus dentro de acceptTerms. Um gate que compara a marca legal.seen na transição para active mostraria o aviso de versão logo após o novo aceite. Gravar a marca antes de chamar acceptTerms elimina a corrida de forma determinística.

---
title: Marca local gravada antes do comando evita corrida com a releitura de estado
type: pattern
tags: [flutter, onboarding, state-management]
created: 2026-11-09
summary: Gravar a marca legal.seen antes de chamar acceptTerms elimina a corrida de forma determinística.
confidence: low

## Contexto
No Flutter, o aceite de termos dispara `refreshStatus` dentro de `acceptTerms`. Um gate que compara a marca legal.seen na transição para active mostraria o aviso de versão logo após o novo aceite.

## Detalhes
Gravar a marca antes de chamar `acceptTerms` elimina a corrida de forma determinística. Isso garante que a marca seja atualizada corretamente e evita problemas relacionados à releitura de estado.

## Próximos passos
- Implementar a gravação da marca local antes de chamar `acceptTerms`.
- Testar a implementação para garantir que a corrida não ocorra.
- Atualizar a documentação do projeto com as mudanças realizadas.

## Conexões
- [[Design de Interface com Agente]]
