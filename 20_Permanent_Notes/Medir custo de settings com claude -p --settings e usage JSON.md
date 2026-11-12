---
title: "Medir custo de settings com claude -p --settings e usage JSON"
type: permanent
created: 2026-11-10T14:33:25
moc: "Design de Interface com Agente"
tags: [claude, settings, performance, usage]
source_inbox: "fe334fed-medir-custo-de-settings-com-claude-p-settings-e-usage-json.md"
tier: "L2"
score: 0.766
---

# Medir custo de settings com claude -p --settings e usage JSON

Rode claude -p 'Reply OK' --model haiku --output-format json --settings '<json>' num diretório vazio. Some input, cache_creation e cache_read de .usage. O teste não edita arquivo de settings e compara perfis em segundos.

# Medir custo de settings com claude -p --settings e usage JSON

## Contexto
Este padrão descreve um método para medir o custo associado a diferentes configurações do modelo Claude usando o comando `claude -p`. O objetivo é comparar o desempenho em termos de tempo de execução entre diferentes conjuntos de settings.

## Detalhes
1. **Comando**: `claude -p 'Reply OK' --model haiku --output-format json --settings '<json>'`
   - Executa Claude com a prompt "Reply OK" usando o modelo "haiku".
   - O formato de saída é JSON.
   - `<json>` deve ser substituído pelo JSON real de configurações desejadas.

2. **Ambiente**: Realize o teste em um diretório vazio para evitar interferências com arquivos existentes.

3. **Medição**:
   - Capture os valores de `input`, `cache_creation` e `cache_read` do arquivo `.usage`.
   - Compare esses valores entre diferentes conjuntos de settings para medir o custo associado a cada configuração.

4. **Comparação**:
   - O teste não deve editar o arquivo de settings original.
   - Compara os tempos de execução em segundos para determinar qual configuração é mais eficiente.

## Próximos passos
- Implementar um script para automatizar a medição dos custos.
- Documentar os resultados e analisar as diferenças entre diferentes conjuntos de settings.
- Considerar a inclusão de mais modelos e prompts para uma análise mais abrangente.

## Conexões
- [[Design de Interface com Agente]]
