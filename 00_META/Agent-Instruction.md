---
title: Agentic Knowledge Bridge
type: meta
tags: [meta, agentic-ai, knowledge-base, instructions]
created: 2026-05-21
provenance: manual
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
4. **Local Project Brain (MANDATÓRIO)**: Se a pasta `docs/` não existir no diretório raiz do projeto, você **deve criá-la** — perguntando antes de escrever. Popule-a com `PROMPT.md` (template em `90_Assets/Template_Project_Prompt.md`), `index.md`, `PRD.md` e o playbook, seguindo o [[Padrão de Documentação Agêntica Local]].
5. **Cadeia de Artefatos (definição de produto)**: para qualquer projeto que passe de um script, siga a [[Cadeia de Artefatos de Projeto - Intenção, RFC, Plano de Fase]] — intenção do usuário → escopo/[[PRD]] → RFC-000 e RFCs ([[RFC de Produto - Anatomia e Ciclo de Status]]) → [[Plano de Fase em Etapas Mescláveis]] → [[Nota de Conclusão de Etapa é Entregável, Não Relatório]] → [[Playbook de Projeto - Erros Já Cometidos Como Artefato]]. O nível (1, 2 ou 3) é escolhido e declarado antes do primeiro documento. Esqueletos em `90_Assets/Template_*.md`. Decisão técnica vai numa RFC com alternativa rejeitada, **não** num `architecture.md` guarda-chuva.

## 🏗️ Skills de Automação (COMPORTAMENTOS)
Além dos padrões técnicos, você deve operar utilizando estas "Skills":

1. **Git Flow Autônomo**: Siga a [[Skill - Fluxo de Trabalho de Feature Branch]]. Crie branches para novas tarefas e faça commits incrementais.
2. **Sincronização de Conhecimento**: Siga a [[Skill - Sincronização de Conhecimento Recursiva]]. Duas cadências, não uma:
    - **Ao terminar cada tarefa**, varra a documentação do projeto atrás do que a sua mudança acabou de tornar **falso** (`grep` pelos marcadores `pendente|não implementado|ainda não|falta|TODO|planejado`, mais os nomes próprios do que mudou, mais contagens e versões) e corrija no mesmo ciclo. **Nota desatualizada é bug, não dívida** — ela mente com a autoridade de um documento, e por isso é pior que nota nenhuma. Uma tarefa não está concluída enquanto a documentação que descreve o que você mexeu não voltar a ser verdadeira.
    - **Ao final da sessão**, destile o novo para o Vault Global e propague lá a mesma invalidação. Não encerre a sessão sem as duas coisas.

    Detalhe completo em [[Documentação Desatualizada é Bug, Não Dívida]]; o lado da leitura (reverificar antes de usar nota como base de decisão) em [[Notas de Análise Envelhecem em Dias - Reverificar no Código Antes de Apresentar]].
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
3. **Traceability**: Sempre verifique o [[PRD]] e as RFCs do projeto atual para garantir que o código atenda aos requisitos originais e não contrarie decisão já registrada.

---
*Nota para o Agente: Se você encontrar um novo padrão útil no projeto atual, destile-o e adicione uma nova nota em `20_Permanent_Notes/` seguindo o template padrão.*
