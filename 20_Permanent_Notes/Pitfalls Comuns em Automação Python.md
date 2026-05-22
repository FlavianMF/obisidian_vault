---
title: Pitfalls Comuns em Automação Python
type: pattern
tags: [python, programming, bug-trap]
created: 2026-05-22
provenance: hermes_validator
---

# 🛑 Pitfalls Comuns em Automação Python

## 1. Comportamento Inesperado de `rstrip`
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

### ✅ A Solução
Utilizar `.endswith()` com fatiamento ou, em versões modernas de Python (3.9+), usar `.removesuffix()`.

---

## 2. Caminhos Relativos em Scripts Movidos
Ao reorganizar projetos movendo scripts para subpastas (ex: `scripts/`), o uso de `os.path.dirname(os.path.abspath(__file__))` para localizar arquivos de dados falha se o script assume que os dados estão no mesmo nível.

### Exemplo do Erro
```python
# Script em /scripts/ tentando ler /data/arquivo.json
base_path = os.path.dirname(os.path.abspath(__file__))
with open(f"{base_path}/arquivo.json") as f: # FileNotFoundError
```

### ✅ A Solução
Implementar uma [[Arquitetura de Diretórios para Pipelines de Validação]] com um `config.py` centralizado na raiz e utilizar caminhos absolutos baseados no diretório mestre.

## 🖇️ Conexões
- [[Engenharia de Sistemas Agêntica]]
- [[Arquitetura de Diretórios para Pipelines de Validação]]

