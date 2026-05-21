# Capella e os 3 Pilares - Exemplo Prático

Este guia mostra como navegar no Capella através dos 3 pilares do framework, usando o exemplo de um **Medidor de Energia Inteligente**.

---

## 🟦 Pilar 1: O Problema (Operational Analysis - OA)
**Foco**: Entender o contexto sem o produto.
- **Diagrama OEB (Operational Entity Blank)**:
  - **Atores**: Usuário (Residente), Distribuidora de Energia, Eletrodomésticos.
- **Diagrama OAIB (Operational Activity Interaction Blank)**:
  - **Atividade**: "Consumir Energia" (Eletrodoméstico), "Pagar Fatura" (Usuário), "Monitorar Carga da Rede" (Distribuidora).
- **A Dor**: O usuário não sabe qual aparelho gasta mais e a Distribuidora sofre com picos de carga não planejados.

---

## 🟩 Pilar 2: O Sistema (System Analysis - SA)
**Foco**: Definir o que a "Caixa Preta" (o produto) faz.
- **Transição**: O Capella permite transicionar as Atividades Operacionais para **System Functions**.
- **Diagrama SAB (System Architecture Blank)**:
  - **Sistema Central**: Medidor Inteligente.
  - **Funções**: "Medir Corrente/Tensão", "Calcular Consumo kWh", "Transmitir Dados via Wi-Fi", "Detectar Anomalias".
- **Fluxo**: O fluxo de dados sai do sensor (input) e vai para o "Analytics Engine" (processamento).

---

## 🟨 Pilar 3: A Solução (Logical & Physical Architecture - LA/PA)
**Foco**: Como o produto é construído (White Box).

### Nível Lógico (LA - Independente de Hardware)
- **Diagrama LAB (Logical Architecture Blank)**:
  - **Componente Lógico A**: Unidade de Aquisição (Abstração do sensor).
  - **Componente Lógico B**: Unidade de Comunicação (Abstração da rede).
  - **Vantagem**: Se você decidir trocar Wi-Fi por LoRa, a lógica de "Transmitir Dados" não muda.

### Nível Físico (PA - O Hardware Real)
- **Diagrama PAB (Physical Architecture Blank)**:
  - **PCBA**: Placa principal.
  - **Componentes**: [[ESP32]] (Microcontrolador), **ADS1115** (ADC de alta precisão), **Sensor SCT-013** (Transformador de Corrente).
  - **Firmware**: [[ESP-IDF]] com RTOS.
- **Diagrama de Interfaces (ICD)**: Detalha que o Sensor se conecta ao ADC via I2C.

---

## 🔄 Resumo do Fluxo no Capella
1. **OA**: "Usuário quer economizar" (Necessidade).
2. **SA**: "Sistema deve mostrar consumo em tempo real" (Função).
3. **LA**: "Módulo de Visualização deve processar dados" (Lógica).
4. **PA**: "O App no Celular via Firebase recebe o JSON" (Implementação).

---

## 🔗 Conexões
- [[Capella MBSE]]
- [[Framework 3 Pilares SE]]
- [[IoT]]
