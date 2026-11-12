---
title: "Caminho relativo num YAML de fluxo quebra se resolvido pelo cwd do consumidor"
type: permanent
created: 2026-11-10T14:52:25
moc: "Design de Interface com Agente"
tags: [yaml, fluxo, caminho-relativo, cwd]
source_inbox: "497061cc-caminho-relativo-num-yaml-de-fluxo-quebra-se-resolvido-pelo.md"
tier: "L2"
score: 0.773
---

# Caminho relativo num YAML de fluxo quebra se resolvido pelo cwd do consumidor

Campo prompt (ou qualquer path) relativo num YAML lido por outro processo precisa ser resolvido contra o diretório do próprio YAML (Flow.source.parent), não contra o cwd de quem consome.

# Caminho relativo num YAML de fluxo quebra se resolvido pelo cwd do consumidor

## Contexto
Na revisão a frio do loader de agents/flows, foi identificado um problema relacionado ao tratamento de caminhos relativos em arquivos YAML. Especificamente, quando um campo como `prompt` (ou qualquer outro path) é definido como relativo num arquivo YAML, o processo responsável por ler esse arquivo deve resolver esse caminho em relação ao diretório do próprio arquivo YAML (`Flow.source.parent`), e não contra o diretório de trabalho (`cwd`) do consumidor.

## Detalhes
O problema ocorre porque, atualmente, o loader de agents/flows está resolvendo caminhos relativos contra o `cwd` do consumidor, o que pode levar a erros se o arquivo YAML e o contexto de execução não estiverem alinhados.

## Armadilhas
- **Resolução incorreta de caminhos**: Se o campo relativo for resolvido contra o `cwd` do consumidor em vez de `Flow.source.parent`, pode resultar em caminhos inválidos ou inexistentes.
- **Problemas de portabilidade**: Arquivos YAML que funcionam corretamente em um contexto específico podem falhar em outros contextos de execução, devido à resolução incorreta dos caminhos.

## Próximos passos
1. **Correção do código**: Atualizar o loader de agents/flows para resolver caminhos relativos contra `Flow.source.parent` em vez de `cwd`.
2. **Testes adicionais**: Realizar testes rigorosos para garantir que a correção não introduza novos problemas.
3. **Documentação**: Atualizar a documentação para refletir a nova resolução de caminhos.

## Conexões
- [[Design de Interface com Agente]]
