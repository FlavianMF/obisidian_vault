---
title: "Script Python de edição converte CRLF em LF"
type: permanent
created: 2026-11-10T14:07:27
moc: "Design de Interface com Agente"
tags: [python, script, git, diff, ipod_uart_simulator]
source_inbox: "747014d2-script-python-de-edicao-converte-crlf-em-lf.md"
tier: "L2"
score: 0.763
---

# Script Python de edição converte CRLF em LF

open().read()/write() em modo texto normaliza CRLF para LF e infla o diff (test_commands.py: 599 linhas). Confira 'git diff --stat' e 'file' antes de editar; restaure com sed -i 's/$/\\r/'.

# Script Python de edição converte CRLF em LF

## Contexto
O script Python `test_commands.py` contém 599 linhas que utilizam `open().read()` e `open().write()` em modo texto. Essas operações normalizam os caracteres de nova linha (CRLF) para LF, o que pode aumentar o tamanho do diff e dificultar a comparação entre versões.

## Detalhes
- **Arquivo**: test_commands.py
- **Linhas afetadas**: 599
- **Projeto**: ipod_uart_simulator

## Armadilhas
- **Inflação do diff**: A conversão de CRLF para LF pode aumentar significativamente o tamanho do diff, dificultando a visualização das mudanças.
- **Perda de informações**: O formato CRLF é comumente usado em sistemas Windows, enquanto LF é mais comum em Unix/Linux. A conversão pode resultar em perda de informações específicas para sistemas Windows.

## Próximos passos
- **Verificação prévia**: Antes de editar o arquivo, verifique o formato das linhas usando `git diff --stat` e `file`.
- **Restauração**: Se necessário, restaure as linhas CRLF usando o comando `sed -i 's/$/\\r/'`.

## Conexões
- [[Design de Interface com Agente]]
