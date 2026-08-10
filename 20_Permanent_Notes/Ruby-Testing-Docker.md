---
title: Testes de Software em Ruby on Rails com Docker
type: permanent
tags: [ruby, rails, testing, rspec, docker, dev-experience]
created: 2026-05-22
provenance: manual
---

# 🧪 Testes de Software em Ruby on Rails com Docker

Este padrão descreve como configurar e executar uma suíte de testes robusta para aplicações Ruby on Rails operando exclusivamente em ambientes containerizados ([[Docker]]).

## 🏗️ Arquitetura de Testes

Para ambientes sem Ruby local, a execução depende de [[Docker Compose]]. O container de API deve possuir as dependências de teste no `Gemfile`.

### Ferramentas Recomendadas
- **RSpec**: Padrão da indústria para BDD em Ruby.
- **FactoryBot**: Substitui fixtures por fábricas dinâmicas.
- **Database Cleaner**: Mantém a integridade do banco de teste.
- **Shoulda Matchers**: Simplifica testes de models e controllers.

## 🚀 Comandos de Execução

A execução deve ser feita via `docker compose run` para garantir que o ambiente (variáveis, banco de dados) esteja correto.

```bash
# Execução completa
docker compose run --rm api bundle exec rspec

# Preparação de banco (Migrate de teste)
docker compose run --rm api bundle exec rails db:test:prepare
```

## 📋 Padrões de Implementação

### 1. Testes Unitários (Models)
Foco em regras de negócio puras.
- Validações.
- Callbacks (usar com cautela).
- Scopes.

### 2. Testes de Integração (Requests)
Garantem que os endpoints da API respondem conforme o esperado.
- Status codes.
- Estrutura JSON.
- Segurança (Autenticação/Autorização).

### 3. Gerenciamento de Estado
Utilizar o `Database Cleaner` configurado para `transaction` na maioria dos casos e `truncation` para testes que utilizam drivers de navegador (System Tests).

## 🖇️ Conexões
- [[Engenharia de Software]]
- [[Docker-out-of-Docker (DooD)]]
- [[Sincronização de Conhecimento Recursiva]]
