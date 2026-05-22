---
title: Pitfalls no Uso de rstrip para URLs
type: pattern
tags: [python, programming, bug-trap]
created: 2026-05-22
provenance: hermes_validator
---

# Pitfalls no Uso de rstrip para URLs

## 🛑 O Problema
O método `.rstrip()` em Python **não** remove uma string fixa do final, mas sim **qualquer caractere** contido no conjunto fornecido.

### Exemplo do Erro
Ao tentar remover a extensão `.git` de uma URL de repositório:
```python
url = "https://github.com/user/Lonnalt"
url = url.rstrip(".git")
# Resultado esperado: "https://github.com/user/Lonnalt"
# Resultado real: "https://github.com/user/Lonna"
```
O caractere `t` foi removido porque ele faz parte da string `.git`.

## ✅ A Solução
Utilizar `.endswith()` com fatiamento ou, em versões modernas de Python (3.9+), usar `.removesuffix()`.

### Padrão Recomendado
```python
if url.endswith('.git'):
    url = url[:-4]
# OU (Python 3.9+)
url = url.removesuffix('.git')
```

## 🖇️ Conexões
- [[Engenharia de Sistemas Agêntica]]
- [[20_Permanent_Notes/Skill - Sincronização de Conhecimento Recursiva]]
