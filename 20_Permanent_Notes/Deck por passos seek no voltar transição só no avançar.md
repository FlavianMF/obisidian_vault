---
title: "Deck por passos: seek no voltar, transição só no avançar"
type: permanent
created: 2026-11-10T14:32:55
moc: "Design de Interface com Agente"
tags: [flv, presentation, transitions]
source_inbox: "959a9785-deck-por-passos-seek-no-voltar-transicao-so-no-avancar.md"
tier: "L1"
score: 0.78
---

# Deck por passos: seek no voltar, transição só no avançar

Em slides HTML com passos declarativos (data-at/exit/on), aplique uma classe .seek que zera transições (inclusive ::after) por um quadro ao voltar ou pular para o fim; o avançar anima e o voltar cai no estado de repouso exato. prefers-reduced-motion usa a mesma regra.

# Deck por passos: seek no voltar, transição só no avançar

## Contexto
O padrão descreve uma abordagem para criar apresentações HTML com transições declarativas e controladas. A ideia é usar classes CSS específicas para controlar as transições ao avançar e ao voltar em um deck de slides.

## Detalhes
- **Classe .seek**: Aplica-se a um quadro específico para zera as transições, tanto no estado normal quanto no estado `::after`.
- **Transições ao avançar**: As transições são animadas conforme o usuário avança para o próximo slide.
- **Transições ao voltar**: As transições são desativadas, retornando o quadro ao estado de repouso exato.
- **prefers-reduced-motion**: O padrão deve ser compatível com preferências de redução de movimento, aplicando as mesmas regras.

## Próximos passos
1. Implementar a classe `.seek` em um quadro específico.
2. Testar a transição ao avançar e ao voltar.
3. Verificar a compatibilidade com `prefers-reduced-motion`.
4. Documentar o padrão para uso em projetos futuros.

## Conexões
- [[Design de Interface com Agente]]
