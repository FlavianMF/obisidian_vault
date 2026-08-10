---
title: Agentic AI (Agentes de IA)
type: concept
tags: []
created: 2026-05-21
provenance: manual
---

# Agentic AI (Agentes de IA)

## 💡 Definição
Diferente de IAs generativas "chat-based", Agentes de IA possuem autonomia para executar tarefas, usar ferramentas, raciocinar sobre problemas e interagir com outros agentes ou sistemas para atingir um objetivo.

## 🏗️ Arquitetura de um Agente
- **Percepção**: Recebe inputs do ambiente (ex: requisitos em linguagem natural).
- **Planejamento**: Decompõe a meta em sub-tarefas.
- **Memória**: Retenção de contexto de curto e longo prazo (RAG).
- **Ações**: Uso de ferramentas (ex: gerar código [[SysML]], consultar API da NASA).

## 🛠️ Infraestrutura e Execução
Para garantir segurança e autonomia, agentes modernos utilizam:
- **Isolamento**: [[Ambiente de Desenvolvimento de Agentes em Containers]] para evitar danos ao sistema host.
- **Tool-Use Sandboxing**: [[Docker-out-of-Docker (DooD)]] para permitir que o agente crie sub-containers de execução.
- **Inferência Local**: Uso de ferramentas como [[Otimização de Recursos para LLMs em CPU|Ollama]] para independência de APIs externas.

## 🎯 Aplicação em SE
Em [[MBSE com Agentic AI]], os agentes atuam como "co-designers", validando restrições técnicas em tempo real.

## 🔗 Referências
- [[Rouse 2020]] (IA como Inteligência Aumentada)
- [[Capella AI Agent Talk]]
