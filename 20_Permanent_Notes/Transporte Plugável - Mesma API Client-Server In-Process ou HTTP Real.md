---
title: Transporte Plugável - Mesma API Client-Server In-Process ou HTTP Real
type: pattern
tags: [architecture, client-server, transport, api-design, embedding]
created: 2026-09-08
provenance: projetos_ita
project: projetos_ita
---

# Transporte Plugável - Mesma API Client-Server In-Process ou HTTP Real

Definir o contrato de servidor (rotas, tipos, schema) **uma única vez**, e
tratar o transporte como um detalhe trocável: RPC in-process (mesmo
processo, sem overhead de socket) pro caso local de um usuário só, HTTP+SSE
real quando é preciso acesso remoto, múltiplos clientes simultâneos, ou
expor a mesma sessão pra outra ferramenta.

**Por que importa**: evita duas implementações de cliente divergindo com o
tempo — uma "rápida mas só local" e outra "completa mas só remota". O
código cliente escreve contra a mesma interface (mesmos tipos, mesmo
formato de request/response) e nem precisa saber qual transporte está por
baixo.

**Como fica concretamente** (caso observado em [[opencode]]):
- O comando de CLI local sobe um *Worker* em background rodando a lógica
  real de servidor, e conecta um cliente RPC a ele.
- Se ninguém pediu rede externa (sem flag de porta/host), o cliente fala
  com o worker via um shim de `fetch`/event-source in-process — mesma
  forma de chamada, sem round-trip de rede.
- Se rede externa é pedida, o mesmo worker recebe instrução de subir um
  servidor HTTP de verdade, e o cliente muda pra HTTP genuíno + auth por
  header — sem o cliente mudar de shape.
- Os tipos de cliente (`@opencode-ai/client`) são **gerados diretamente a
  partir do package do servidor**, especificamente pra "prevenir drift de
  transporte" entre as duas variantes.

**Quando usar**: harness que precisa rodar tanto embutido num processo CLI
(baixa latência, um usuário) quanto exposto como serviço (múltiplos
clientes, acesso remoto, integração com outras ferramentas) — sem manter
dois codebases de cliente.

## 🔗 Conexões
- [[opencode]]
