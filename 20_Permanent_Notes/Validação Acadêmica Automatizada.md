---
title: Validação Acadêmica Automatizada
type: pattern
project: hermes_validator
tags: [education, automation, grading, rubric]
created: 2026-05-21
provenance: 1.0
---

# Validação Acadêmica Automatizada

Uso de [[Agentic AI|agentes]] e scripts para aplicar [[Análise de Trade-off (Trade Study)|rubricas de avaliação técnica]] em massa de forma consistente e escalável.

## Estrutura de Avaliação (Exemplo IoT)
O sistema avalia submissões baseando-se em critérios técnicos fixos:
1. **Lógica de Firmware** (30 pts): Análise de código `main.py`.
2. **Hardware/Simulação** (20 pts): Verificação de `diagram.json` (Wokwi).
3. **CI/CD** (25 pts): Presença de GitHub Actions.
4. **Documentação** (10 pts): Qualidade do [[PRD|README]].
5. **Organização** (10 pts): Estrutura de arquivos e commits.

## O Modo Híbrido (Auto + Manual)
Uma inovação importante é permitir a **intervenção humana**:
- O sistema gera uma nota automática.
- O professor revisa e pode inserir uma **nota manual** e comentários via `adicionar_notas_manuais.py`.
- A nota final prioriza o julgamento humano, mas mantém o rastro da [[Validação Acadêmica Automatizada|avaliação automática]].

**Ressalva de campo (2026-09-17).** A metade humana é a que não acontece sozinha. No projeto irmão
[[correcoes_docs_tcc]], 16 de 16 notas ficaram em `PROPOSTA` — a revisão do professor nunca foi
feita, e com isso toda a maquinaria de divergência automático × manual continua sem um único caso
para ler. O gargalo do modo híbrido não é gerar a nota; é o carimbo humano voltar.

## Links
- [[hermes_validator]]
- [[correcoes_docs_tcc]] (a aplicação conversacional, com primeiro lote medido)
- [[Orquestração Híbrida de Agentes]]
- [[Rubrica em Prosa Vira Gabarito de Evidência]] (a variante de repo único, com gate humano explícito)

## Fontes
- Projeto: `hermes_validator`
- Documentação: `FLUXOGRAMA.md`; rubrica atual em `validacoes_iot/docs/rubrica_iot.md`
  (verificado 2026-09-17 — o antigo `resultado_validacao/rubrica.md` não é mais o caminho vivo)
