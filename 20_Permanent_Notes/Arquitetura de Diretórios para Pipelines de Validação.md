---
title: Arquitetura de Diretórios para Pipelines de Validação
type: pattern
project: hermes_validator
tags: [architecture, organization, data-pipeline, best-practices]
created: 2026-05-22
provenance: 1.0
---

# 📂 Arquitetura de Diretórios para Pipelines de Validação

Este padrão define a organização estrutural para projetos que envolvem pipelines de dados intensivos, automação de scripts e geração de relatórios, visando clareza, portabilidade e escalabilidade.

## 🏛️ Estrutura Recomendada

A separação de preocupações deve ser física, segregando lógica de execução, dados persistentes e artefatos de saída:

```text
projeto/
├── 00_run_all.py       # Orquestrador mestre (Entry Point)
├── config.py           # Gestão centralizada de caminhos (Paths)
├── scripts/            # Lógica modular (Fases do pipeline)
├── data/               # Dados brutos, intermediários e bancos de dados
│   └── repos/          # Subpastas para inputs volumosos (ex: clones Git)
└── reports/            # Dashboards HTML, MDs individuais e logs de execução
```

## 🖇️ Princípios Fundamentais

### 1. Centralização de Caminhos (`config.py`)
Nunca utilize caminhos hardcoded ou `os.path.dirname(__file__)` assumindo que o script está na raiz. Use um arquivo central de configuração que defina caminhos absolutos baseados na localização da raiz do projeto.

### 2. Injeção de Contexto (`PYTHONPATH`)
Para permitir que scripts em subpastas importem a configuração global sem hacks de `sys.path` complexos, o orquestrador deve injetar a raiz no ambiente:

```python
env = os.environ.copy()
env["PYTHONPATH"] = ROOT_PATH + os.pathsep + env.get("PYTHONPATH", "")
subprocess.run([sys.executable, script_path], env=env)
```

### 3. Servidor Interativo Multidir
Ao implementar dashboards interativos que servem arquivos de múltiplas subpastas, sobrescreva o `translate_path` do servidor HTTP para mapear rotas virtuais para os diretórios físicos corretos (`reports/` para assets, `data/` para JSONs).

### 4. Dashboards Autossuficientes (Offline-first)
Para máxima portabilidade, o pipeline final deve ser capaz de embutir dados (JSON) diretamente no HTML via injeção de tags `<script>`, eliminando dependências de servidores locais ou problemas de [[CORS]].

## 🚀 Benefícios
- **Clean Root**: O diretório raiz contém apenas o que é essencial para o usuário final.
- **Portabilidade**: O projeto pode ser movido entre ambientes (Docker vs Local) sem quebrar referências.
- **Segurança**: Dados volumosos ou sensíveis ficam isolados em pastas específicas.

## Links
- [[Orquestração Híbrida de Agentes]]
- [[hermes_validator]]
- [[Pitfalls Comuns em Automação Python]]
