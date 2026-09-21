---
title: Trilha do Professor Pode Divergir da Trilha do Projeto na Planilha de Times
type: trap
tags: [pnaat, residencia, planilha, alocação, mbse]
created: 2026-09-21
provenance: residencia_00
project: residencia_00
---

Ao popular o dossiê da primeira empresa da residência PNAAT Cariri (Juá Produtos
de Limpeza, `docs/empresas/empresa-01-jua.md`), a sheet `Times` de
`empresas_residencia.xlsx` mostrou o professor alocado (Flavian Fernandes,
trilha de foco **IoT**) num time cujo projeto está classificado como trilha
**IA** — sem nenhum alerta automático além de uma anotação manual "CONFERIR"
feita por quem gerou a planilha.

Isso não é caso isolado: a alocação de professor/time acontece antes do
desafio técnico da empresa estar totalmente definido (o desafio de Juá só
chegou via briefing recebido no SharePoint em 2026-09-16, depois do professor
já estar atribuído). Trilha do professor e trilha do projeto são preenchidas
em momentos diferentes do processo, por pessoas diferentes, sem constraint que
force as duas a baterem.

**Como aplicar:** ao popular o dossiê de qualquer uma das 8 empresas
(`docs/empresas/empresa-0N-<slug>.md`), sempre comparar `Times.Trilha do
professor` com `Times.Trilha do projeto` (ambas colunas fórmula na mesma
sheet) antes de fechar o checklist de pré-visita. Se divergirem, registrar
como observação/risco explícito no dossiê e no PM Canvas (bloco Riscos) — não
resolver a divergência silenciosamente escolhendo uma das duas, é decisão de
alocação que precisa de humano.

Fonte de dados usada para popular o primeiro dossiê: `empresas_residencia.xlsx`
(workbook reconciliado, sheets `Empresas`/`Projetos`/`Times`/`Atividades`)
cruzado com o material bruto recebido na pasta `00_Recebidos/` da empresa no
SharePoint (briefing docx + vídeo da linha de produção) — esse par de fontes
(planilha reconciliada + inbox do SharePoint) é o padrão a repetir pras
próximas 7 empresas, não algo específico da Juá.

Relacionado: [[Project Model Canvas vs ARCADIA - Mapeamento]],
[[Sem Log de Atribuição Por Trilha, Desenho Paralelo Não Prova Eficácia Causal]],
[[Corpus Multiempresa Só Vira Dataset Reaproveitável Com Consentimento Explícito]].
