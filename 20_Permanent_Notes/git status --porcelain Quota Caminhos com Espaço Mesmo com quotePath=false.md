---
title: git status --porcelain Quota Caminhos com Espaço Mesmo com quotePath=false
type: trap
tags: [git, shell, scripting, unicode, second-brain-sync, automation]
created: 2026-09-11
provenance: projetos_ita
project: projetos_ita
---

# git status --porcelain Quota Caminhos com Espaço Mesmo com quotePath=false

## Contexto

O `vault_sync.py` do `second-brain-sync` recusa rodar se o vault tiver arquivos sujos
não declarados em `--note` — guardrail correto. Sincronizando 8 notas novas de uma vez,
foram **quatro tentativas falhas** até acertar a lista de caminhos, porque os nomes das
notas têm espaços *e* acentos (`Página com Screenshots...`, `...Não Há Screenshot.md`).

Sequência de erros, cada um mascarando o próximo:

1. **Digitar os caminhos à mão** — uma nota não casou. Provável divergência de
   normalização Unicode entre o que foi digitado e o que está em disco.
2. **`git status --porcelain` + `sed 's/^?? //'`** — pior: agora quase nenhuma casou.
   Por padrão `core.quotePath=true`, então `ã` vem escapado como `\303\243` *dentro*
   do texto, e o caminho passado ao script continha a barra invertida literal.
3. **`-c core.quotePath=false`** — resolveu o escape, mas os caminhos **continuam entre
   aspas duplas**, porque contêm espaço. Strip só do prefixo `?? ` deixa a aspa no
   começo e no fim.
4. **Array em `zsh` com process substitution** (`while read ... done < <(...)`) —
   resultou em array vazio silenciosamente, sem erro.

## Armadilha

Duas camadas independentes de quoting no `--porcelain`:

- **Escape de bytes não-ASCII** → controlado por `core.quotePath`
- **Aspas envolvendo o caminho** → disparado por caractere especial, **incluindo
  espaço**, e *não* desligado por `core.quotePath=false`

Desligar o primeiro e esquecer o segundo produz caminhos quase certos — que falham de
um jeito confuso, porque a maioria dos arquivos (os sem acento nem espaço) passa.

## Padrão

Parsear em Python, não em shell, e tratar as duas camadas:

```python
out = subprocess.run(["git","-c","core.quotePath=false","status","--porcelain"],
                     capture_output=True, text=True).stdout
paths = []
for line in out.splitlines():
    p = line[3:]                                   # tira o "?? " / " M "
    if p.startswith('"') and p.endswith('"'):
        p = p[1:-1]                                # tira as aspas de caminho com espaço
    paths.append(p)
```

Melhor ainda quando disponível: `git status --porcelain -z`, que usa `NUL` como
separador e **não quota nada** — elimina as duas camadas de uma vez.

Evitar montar array de argumentos com acento/espaço em shell: passar direto de Python
para `subprocess.run([...])` não tem quoting nenhum no meio.

## Quando aplicar

Qualquer script que consuma saída de `git status`, `git diff --name-only` ou
`git ls-files` num repositório cujos caminhos tenham espaço ou não-ASCII — o que é a
regra, não a exceção, num vault Obsidian em português.

## 🔗 Conexões
- [[Submodule HTTPS Remote Herda Conta gh Errada]]
- [[Padrão de Documentação Agêntica Local]]
