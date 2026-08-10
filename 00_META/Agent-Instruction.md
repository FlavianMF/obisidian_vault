---
title: Agentic Knowledge Bridge
type: meta
tags: [meta, agentic-ai, knowledge-base, instructions]
created: 2026-05-21
---

# 🤖 Agentic Knowledge Bridge

Esta nota serve como instrução para **outros agentes de IA** (Claude Code, Cursor, etc.) sobre como utilizar este vault como base de conhecimento para projetos de engenharia.

## 🏛️ Estrutura do Vault para Agentes
Se você é um agente operando em outro projeto, use estas regras para navegar aqui:
- **00_META/manifests/INDEX.md**: O ponto de entrada para agentes. Os MOCs em
  `30_MOCs/` usam blocos `dataview`, que só renderizam dentro do app Obsidian —
  para um agente lendo o filesystem direto, esses blocos são texto morto. Os
  manifests em `00_META/manifests/` são a versão estática e sempre atualizada
  do mesmo índice, particionada por `type` (ver [[Skill - Sincronização de
  Conhecimento Recursiva]] para como são gerados).
- **20_Permanent_Notes/**: Onde residem os padrões técnicos. Busque aqui por termos como "Docker", "OAuth", "Trade-off" ou "V-Model".
- **10_Literature_Notes/**: Base teórica e referências acadêmicas (NASA, INCOSE).

## 🖇️ Padrões de Escrita e Conectividade
Para manter o vault útil para estudo, você **deve** seguir estes padrões de linkagem:
1. **Linkagem Densa (Inline)**: Não limite links à seção "Links". Sempre que citar um termo técnico (ex: MBSE, SysML, Docker, V-Model) ao longo do texto, envolva-o em `[[wikilinks]]`. 
2. **First Mention Rule**: Linke apenas a primeira ocorrência de cada termo por nota para evitar poluição visual.
3. **Traceability**: Sempre verifique se o conceito que você está descrevendo já existe no vault e conecte-o.

## 🖇️ Padrões de Implementação (MANDATÓRIO)
Ao desenvolver software para o Flavian, você **deve** seguir estes padrões extraídos de projetos anteriores:
1. **DooD (Docker-out-of-Docker)**: Sempre que precisar de sandboxing para ferramentas, use [[Docker-out-of-Docker (DooD)]].
2. **Ciclo de Vida SE**: Siga o [[Engenharia de Sistemas Agêntica|Padrão Agêntico de SE]] (Pré-Fase A até Fase B) antes de codar.
3. **Orquestração Híbrida**: Se o projeto for de larga escala, prefira [[Orquestração Híbrida de Agentes]] (Scripts + LLM).
4. **Local Project Brain (MANDATÓRIO)**: Se a pasta `docs/` não existir no diretório raiz do projeto, você **deve criá-la imediatamente**. Popule-a com os arquivos iniciais (`PROMPT.md`, `index.md`, `PRD.md`, `architecture.md`) utilizando o conteúdo que você leu do código/README original. Siga o [[Padrão de Documentação Agêntica Local]] e utilize o template em `90_Assets/Template_Project_Prompt.md` para o `PROMPT.md`.

## 🏗️ Skills de Automação (COMPORTAMENTOS)
Além dos padrões técnicos, você deve operar utilizando estas "Skills":

1. **Git Flow Autônomo**: Siga a [[Skill - Fluxo de Trabalho de Feature Branch]]. Crie branches para novas tarefas e faça commits incrementais.
2. **Sincronização de Conhecimento**: Siga a [[Skill - Sincronização de Conhecimento Recursiva]]. Ao terminar, atualize o `docs/` local e o Vault Global. Não encerre a sessão sem garantir que o conhecimento foi destilado.
3. **Pesquisa Acadêmica**: Para temas teóricos ou inovações, siga a [[Skill - Pesquisa Acadêmica Rigorosa]]. Utilize Google Scholar, arXiv e NTRS para garantir o estado-da-arte antes de propor arquiteturas.
4. **Ingestão de Literatura**: Sempre que citar um artigo, siga a [[Skill - Ingestão de Notas de Literatura]]. Crie a nota `[[Sobrenome Ano]]` com citação completa e **link de acesso direto** (DOI/URL).

## 🔍 Como Consultar
1. **Gemini CLI Extension (PREFERENCIAL)**: Se você tiver acesso às ferramentas de extensão do Obsidian, utilize:
    - `obsidian_rag_query`: Para busca semântica em todo o vault.
    - `obsidian_read_note`: Para leitura otimizada de notas.
    - `obsidian_link_audit`: Para verificar a integridade das conexões.
2. **Manifest-First (FALLBACK — caso do Claude Code e outros agentes sem essas extensões)**:
    - Leia `00_META/manifests/INDEX.md` primeiro (pequeno, seguro ler inteiro).
    - **`grep` — nunca `Read` completo** — os arquivos `00_META/manifests/by_type/<type>*.md` pela sua palavra-chave. O glob cobre shards automaticamente se um `type` crescer além do limite de linhas por arquivo.
    - Abra (leitura completa) só as notas específicas retornadas pelo grep.
    - Nunca leia `20_Permanent_Notes/` (ou outra pasta) inteira por varredura — isso custa tokens proporcionais ao tamanho do vault, não ao que você precisa.
3. **Traceability**: Sempre verifique o [[PRD]] e os [[stakeholders]] do projeto atual para garantir que o código atenda aos requisitos originais.

---
*Nota para o Agente: Se você encontrar um novo padrão útil no projeto atual, destile-o e adicione uma nova nota em `20_Permanent_Notes/` seguindo o template padrão.*
