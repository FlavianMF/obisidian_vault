---
title: "BASH_MAX_OUTPUT_LENGTH salva a saída em arquivo, não trunca"
type: permanent
created: 2026-11-10T14:34:09
moc: "Design de Interface com Agente"
tags: [second-brain, triagem-noturna, pattern, artifacts]
source_inbox: "31e3ff98-bash-max-output-length-salva-a-saida-em-arquivo-nao-trunca.md"
tier: "L1"
score: 0.743
---

# BASH_MAX_OUTPUT_LENGTH salva a saída em arquivo, não trunca

Doc do Claude Code (2.1.317): saída de sucesso acima do limite (padrão 30000, máximo 150000) vira arquivo na sessão mais prévia de 2.000 caracteres e caminho; falha mostra início e fim de ~10 mil. O setting bashOutputMaxChars vence a variável. Baixar o limite é seguro: nada se perde, o agente lê o arquivo por faixa.

---
title: BASH_MAX_OUTPUT_LENGTH salva a saída em arquivo, não trunca
type: pattern
tags: [bash, output, truncation, artifacts]
created: 2026-11-09
summary: Saída de sucesso acima do limite (padrão 30000, máximo 150000) vira arquivo na sessão mais prévia de 2.000 caracteres e caminho; falha mostra início e fim de ~10 mil. O setting bashOutputMaxChars vence a variável. Baixar o limite é seguro: nada se perde, o agente lê o arquivo por faixa.
confidence: low

## Contexto
O padrão `BASH_MAX_OUTPUT_LENGTH` controla o tamanho máximo da saída em scripts Bash. Quando a saída excede este limite, o padrão é truncar a saída.

## Detalhes
- **Limite Padrão**: 30000 caracteres
- **Limite Máximo**: 150000 caracteres
- **Comportamento em Excesso**: Saída vira arquivo na sessão mais prévia de 2.000 caracteres e caminho.
- **Falha**: Mostra início e fim de ~10 mil caracteres.
- **Precedência**: O setting `bashOutputMaxChars` vence a variável.

## Próximos Passos
- Verificar se o ajuste do limite é seguro para o projeto.
- Testar a leitura do arquivo por faixa pelo agente.

## Conexões
- [[Design de Interface com Agente]]
