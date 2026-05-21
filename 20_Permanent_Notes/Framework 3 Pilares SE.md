# Detalhamento do Framework: Os 3 Pilares do Produto de Elite

Este documento detalha o passo a passo técnico para aplicar o rigor da Engenharia de Sistemas (NASA/MBSE) no desenvolvimento comercial de produtos e serviços.

---

## 🟦 Pilar 1: O Problema (Análise Operacional)
**Objetivo**: Entender o ecossistema antes de desenhar o produto.
**Pergunta-chave**: "O que o mundo precisa, independente da tecnologia?"

1. **Mapeamento de Atores**: Identifique todos os humanos e sistemas externos que interagem com o problema.
   - *Exemplo*: Usuário final, Operador de manutenção, Rede elétrica, Clima.
2. **Definição de Atividades Operacionais**: Liste o que esses atores fazem hoje para resolver (ou sofrer) o problema.
   - *Ação*: Criar um diagrama de atividades "As-Is" (Como é agora).
3. **Identificação de Pain Points (Dores)**: Onde o processo atual quebra? Onde há desperdício de tempo ou dinheiro?
4. **Cenários de Uso (ConOps)**: Escreva narrativas de como seria o "dia perfeito" desses atores com uma solução ideal.

---

## 🟩 Pilar 2: O Sistema (Análise de Sistema/Requisitos)
**Objetivo**: Definir "O QUE" o sistema deve fazer, sem dizer "COMO".
**Pergunta-chave**: "Quais funções o produto deve ter para resolver o Pilar 1?"

1. **Definição da Fronteira do Sistema**: O que está dentro da caixa (seu produto) e o que está fora (o mundo).
2. **Derivação de Funções do Sistema**: Transforme as Atividades Operacionais em Funções Técnicas.
   - *Exemplo*: Se o ator "Monitora Carga", o sistema deve "Medir Corrente" e "Alertar Sobrecarga".
3. **Especificação de Requisitos (L1)**: Documente restrições de performance, segurança e custo.
   - *Regra*: Todo requisito deve estar conectado a uma dor do Pilar 1 (Rastreabilidade).
4. **Análise de Estados e Modos**: Como o produto se comporta ao ligar? Em falha? Em modo de economia?

---

## 🟨 Pilar 3: A Solução (Arquitetura e Implementação)
**Objetivo**: Definir "COMO" construir a solução de forma eficiente.
**Pergunta-chave**: "Qual a melhor engenharia para realizar as funções do Pilar 2?"

1. **Arquitetura Lógica**: Agrupe as funções em "blocos conceituais" antes de escolher o hardware.
   - *Vantagem*: Permite trocar o fornecedor de chip ou sensor sem perder a lógica do projeto.
2. **Arquitetura Física**: Escolha dos componentes, materiais e tecnologias.
   - *Ação*: Definir MCU (ESP32?), Sensores, Protocolos (MQTT/LoRa).
3. **Definição de Interfaces (ICDs)**: Como os componentes se comunicam. Crucial para evitar erros de integração.
4. **Prototipagem e Validação**: Construir o MVP para validar se a "Solução" realmente resolve o "Problema" inicial.

---

## 🔗 Conexões
- [[Capella na Pré-Fase A]] (Ferramenta para o Pilar 1)
- [[MBSE]]
- [[Palestra_SE_Business]]
- [[Capella e os 3 Pilares - Exemplo Prático]]
- 