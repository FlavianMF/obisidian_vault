---
title: Reavaliação — ECC com perfil completo e observer ligado
type: project
tags: [ecc, decision, reassessment, continuous-learning, second-brain, security, tokens]
created: 2026-10-15
provenance: obsidian_vault
project: second_brain_memory
confidence: low
verified: 2026-10-15 via leitura de hook-flags.js, hooks.json, observe.sh, start-observer.sh e config.json do plugin ecc 2.2.3 e conferência do efeito na própria sessão (o GateGuard passou a barrar o primeiro comando Bash e a primeira escrita de arquivo)
scope: project
---

# Reavaliação — ECC com perfil completo e observer ligado

> Em 2026-10-15 o usuário decidiu: **"Quero o perfil completo do ECC quando ligado"** e, entre as opções apresentadas, escolheu
> **"Completo + observer ligado"** (`ECC_HOOK_PROFILE=strict`, nada em `ECC_DISABLED_HOOKS` e `observer.enabled=true`). Esta nota
> reavalia as decisões anteriores à luz dessa mudança. Aplicado nos dotfiles pelo commit `4d0ba89` (branch
> `feat/ecc-full-profile`, sem push). Relaciona-se a [[ECC - Adotar Ideias, Não o Runtime]],
> [[RFC-001 - Memória de Agentes sobre o Second Brain com Orçamento de Tokens]], [[PRD-002 - ECC Automático para Web e C e Linha de Status]]
> e ao [[Estudo - Integrar o Second Brain à Memória do ECC]]. Itens **NÃO VERIFICADO** não foram confirmados por teste.

## 1. O que mudou na prática

A configuração vale quando o plugin está ligado (o `ecc@ecc` segue `false` no escopo de usuário; `make ecc-auto` e o wrapper
ligam por projeto web, C e Node). O perfil só decide quais hooks do plugin rodam. No pin 2.2.3 o perfil `standard` e o `strict`
incluem os mesmos hooks (nenhum hook é só `strict`); a diferença real é sair do `minimal` e não desligar nada.

| Passa a rodar (antes desligado em `minimal` ou por `ECC_DISABLED_HOOKS`) | Efeito |
|---|---|
| `pre:edit-write:gateguard-fact-force` e o gate de Bash | Antes da **primeira** edição de cada arquivo e do primeiro Bash da sessão, o agente precisa apresentar fatos (importadores, API, esquema de dados, a instrução do usuário). Comandos destrutivos pedem alvos e plano de reversão. **Confirmado nesta sessão:** o hook barrou o primeiro comando Bash e a primeira escrita de arquivo até os fatos serem apresentados. Custo: tokens e turnos extras na primeira edição de cada arquivo. |
| `pre:config-protection` | Bloqueia (exit 2) a modificação de arquivos de configuração de linter e formatter já existentes, para o agente corrigir o código em vez de afrouxar a checagem. |
| `pre:observe` e `post:observe:continuous-learning` | Gravam **cada tool call** (entrada e saída) em `~/.local/share/ecc-homunculus/projects/<hash>/observations.jsonl`, só em sessões interativas, não em subagentes, com redação de segredos por regex. |
| Observer Haiku em background (`observer.enabled=true`) | Analisa as observações a cada 5 minutos ou 20 observações e propõe instincts (confiança inicial 0,3–0,85) em `instincts/personal|pending`. |
| `pre:compact`, `stop:session-end` com resumo por LLM | Grava um resumo da sessão antes de compactar e ao fim de cada resposta; chamada de modelo extra (Haiku) quando o contexto restante cai abaixo de 20% ou a cada 50 mensagens; a transcrição vai a um subprocesso `claude -p`. |
| `session-start` (já rodava) com injeção completa | Injeta até 6 instincts com confiança ≥ 0,7, até 6 learned skills e o resumo da sessão anterior (≤ 7 dias), teto de 8000 caracteres (cerca de 2 mil tokens). |
| `post:skill:track`, `cost-tracker`, quality gate, doc-file-warning, `suggest-compact`, `plan-canvas-sessions`, `mcp-health-check` | Telemetria, avisos e checagens. O `suggest-compact` do ECC **duplica** o nosso `suggest-compact.sh`, e o format/typecheck do ECC duplica o nosso (opt-in por projeto). |
| `governance-capture` | Continua **inativo**: exige `ECC_GOVERNANCE_CAPTURE=1`, que não está definido. |

**Mitigação já aplicada (acréscimo meu, reversível):** `ECC_OBSERVE_SKIP_PATHS=observer-sessions,.claude-mem,secrets,.ssh,.aws`
mantém a observação fora de diretórios de trabalho com esses nomes (o padrão do plugin foi preservado e estendido).

## 2. Reavaliação das decisões

| Decisão anterior | Estado agora | Reavaliação |
|---|---|---|
| ECC **desligado por padrão** no escopo de usuário e ligado por projeto (2026-09-30, F0b) | **Mantida** | O perfil completo só pesa onde o ECC está ligado. O custo fixo de ~47,5 mil tokens do plugin continua o argumento para não ligar em tudo. |
| Hooks no perfil `minimal` com `stop:evaluate-session` e `post:ecc-metrics-bridge` desligados | **Revertida pelo usuário** | O perfil passa a `strict`, sem desligamentos. Duplicações com os nossos hooks (`suggest-compact`, format/typecheck) ficam como ruído conhecido; o `evaluate-session` só conta mensagens. |
| `continuous-learning-v2` **rejeitado** em 2026-09-30 (log só de tool calls, observer em background com custo contínuo, redação de segredos fraca, bugs abertos) | **Revertida pelo usuário** (observer ligado) | Os quatro motivos continuam verdadeiros; o usuário os aceitou. Mitigação proposta: (a) o "porquê" que o log perde vem do nosso funil de revisão, onde o humano dá o veredito; (b) o custo do observer fica limitado (5 min, 20 observações) e será medido em `~/.claude/metrics/costs.jsonl`; (c) segredos: `ECC_OBSERVE_SKIP_PATHS`, teste do redator com credenciais falsas num diretório temporário (etapa I0) e varredura antes de qualquer importação para o vault; (d) bugs: registrar a versão do pin. |
| RFC-001 §1: `unified-memory` e `continuous-learning-v2` **fora de escopo da v1** | **Contradita** | Precisa de emenda: o CLv2 passa a ser fonte de **captura**, entrando pelo funil de revisão, não direto no vault. |
| RFC-001 D10 (Fechada): "usar `unified-memory` e `continuous-learning-v2` como base para aplicar no vault" | **Agora coerente** | Com o observer ligado, D10 deixa de contradizer a prática. Leitura adotada: o CLv2 captura, o vault guarda o que foi curado; o `unified-memory` vira adaptador opcional. |
| RFC-001 D8: sem `PreCompact` no vault | **Mantida** | O `pre-compact` do ECC grava em `~/.claude/session-data`, fora do vault. Nada transitório entra no vault. |
| RFC-001 D6/F2: escrita no vault só com portão em código | **Mantida e reforçada** | Instincts nunca viram nota por conta própria: passam pela fila, pelo veredito e pelo `vault_sync.py` (nota nasce `low`, varredura de segredos, recusa de duplicata). |
| Princípio 8 (RFC): **sombra antes de ativo, com gate numérico** | **Em tensão** | A **coleta** de instincts e a **injeção** no SessionStart são a mesma chave de ligar. Recomendação, sem aplicar: manter `observer` e a observação ligados, mas por 2 semanas limitar a injeção com `ECC_INSTINCT_CONFIDENCE_THRESHOLD=1` (a I0 de 2026-10-15 mostrou que `ECC_MAX_INJECTED_INSTINCTS=0` **não** desliga: volta ao padrão 6; o limiar 1 zera a injeção, testado) e só soltar a injeção depois de medir a taxa de aceitação dos instincts na revisão. |
| PRD-002 §3.5: "hooks do ECC ficam no perfil `minimal` (não mudar)" | **Desatualizada** | Trocar por: perfil `strict`. M1 para projetos web/C/Node passa a incluir os hooks: ~2 mil tokens de injeção no SessionStart e as perguntas do GateGuard a cada primeira edição. M1 para os demais projetos não muda. |
| PRD-002 §5: o agente nunca roda `ecc-on`/`ecc-off`/`auto` | **Mantida** | Acrescentar: o agente também não roda `/promote`, `/evolve`, `/instinct-import` nem `/prune` sozinho; sugere. |
| Estudo S4: observer "Rejeitar"; adaptador `ecc.memory.v1` como principal | **Revisada** | Instincts viram a **fonte principal de captura automática**; o `unified-memory` fica adaptador opcional e de menor prioridade. |
| Estudo S5: runtime próprio `sb` (híbrido), sem daemon | **Mantida e ampliada** | O `sb` continua dono da revisão e das guardas. Passa a ter um **importador de instincts** (`sb import-ecc` lê `instincts/personal|pending`) e um índice de instincts já tratados (para não repropor). O processo residente do observer é do ECC; o `sb` segue sem daemon. |
| Regra "agente anota candidato na fila" (decisão 4 do estudo) | **Parcialmente redundante** | O observer já gera candidatos sem esforço do agente. Manter a anotação manual só para correções do usuário e armadilhas que o observer não enxerga; reavaliar depois de 2 semanas de dados. |

## 3. Novos riscos e como fecham

1. **Segredos em log persistente.** `observations.jsonl` guarda entrada e saída de tools; a redação é por regex (não é um classificador) e
   o resumo de sessão não passa por redator no que foi lido. Fechamento: a I0 testa o redator com credenciais falsas em diretório
   temporário (`CLV2_HOMUNCULUS_DIR`), confere as permissões dos arquivos (**NÃO VERIFICADO**) e define retenção; qualquer
   importação para o vault passa pela varredura de segredos do `vault_sync.py` (etapa I1).
2. **Injeção de memória aprendida.** Instincts com confiança ≥ 0,7 entram no contexto sem revisão humana. Fechamento: o limite
   temporário de injeção acima e um envelope "referência, não instrução" (o ECC só protege o resumo de sessão com o envelope
   "HISTORICAL REFERENCE ONLY"; instincts e learned skills ganham só uma frase de uso).
3. **Custo de tokens e de turnos.** GateGuard, resumo por LLM e observer somam custo sem benefício medido (o estudo não achou
   métrica de que a injeção de instincts melhore resultados). Fechamento: a E6 do PRD-002 passa a medir M1 e o custo por tarefa
   com o perfil `strict`, e o `cost-tracker` do ECC alimenta o custo do observer.
4. **Atrito do GateGuard e do config-protection** com fluxos nossos (por exemplo, editar configuração de linter num projeto onde o
   ECC está ligado). Fechamento: documentado; os desligamentos de emergência (`ECC_GATEGUARD=off`,
   `GATEGUARD_BASH_ROUTINE_DISABLED=1`) existem, mas **só o usuário decide usá-los**, pois o agente não deve contornar uma guarda
   que o usuário acabou de ligar.
   **Atenção a um registro anterior:** a nota de 2026-09-30 diz que o perfil `standard` tinha "bloqueio de escrita de `.md`", o que
   quebrava a escrita de notas e docs de projeto. Nesta sessão (perfil completo ativo) o `doc-file-warning` **não bloqueou** a
   escrita de várias notas `.md`; só o GateGuard barrou, até os fatos serem apresentados. No pin 2.2.3 isso é só aviso
   (verificado na I0 de 2026-10-15: `doc-file-warning.js` sai sempre com código 0); o registro antigo não vale para esta versão.
5. **Duplicação de hooks** (`suggest-compact`, format/typecheck). Fechamento: aceita como ruído; se atrapalhar, desligar um dos
   lados por id em `ECC_DISABLED_HOOKS`.
6. **Dois injetores no SessionStart** (o do ECC e os nossos L0/L1, a linha de ECC e a sugestão). Fechamento: orçamento somado
   medido na E6; o nosso L0 continua ≤ 5 linhas.

## 4. Emendas nas outras notas (aplicadas junto desta nota)

- [[ECC - Adotar Ideias, Não o Runtime]]: seção datada de 2026-10-15 registrando a reversão parcial.
- RFC-001: §1 (fora de escopo) e D10.
- PRD-002: §3.5 e a lista de "o que não será feito".
- Estudo: matriz S4 e a etapa I0 (verificar o redator de segredos e o nome do limite de injeção).

## 5. Decisões tomadas (2026-10-15)

1. **Limite temporário da injeção de instincts: aprovado.** Bloquear a injeção por 2 semanas, medindo antes de soltar.
   É o único ponto em que o princípio 8 ainda vale sem reverter a escolha do usuário. **Correção da I0 (2026-10-15):** o nome
   combinado, `ECC_MAX_INJECTED_INSTINCTS=0`, não funciona (volta ao padrão 6). A variável que cumpre a decisão é
   `ECC_INSTINCT_CONFIDENCE_THRESHOLD=1`, testada; ainda não aplicada em `claude/settings.json`.
2. **Lista de projetos excluídos do observer: não por enquanto.** Vale só `ECC_OBSERVE_SKIP_PATHS` (`secrets`, `.ssh`, `.aws`
   e afins). Reabrir se aparecer projeto com dados pessoais.
3. **Retenção: aprovada.** TTL de 30 dias para observações e instincts `pending`, alinhado ao `prune` do ECC.
4. **`/promote`, `/evolve`, `/prune`: o `sb review` pode invocá-los em modo `--dry-run` e mostrar o resultado.** Sem
   `--dry-run`, só o usuário executa. O agente continua sem rodar esses comandos por conta própria.
5. **I0 inclui o teste do redator de segredos e a leitura do limite de injeção: aprovado.** O teste usa credenciais falsas em
   `CLV2_HOMUNCULUS_DIR` temporário, nunca no diretório real.
