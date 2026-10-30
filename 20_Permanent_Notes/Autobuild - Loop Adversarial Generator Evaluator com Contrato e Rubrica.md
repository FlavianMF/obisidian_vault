---
title: Autobuild - Loop Adversarial Generator Evaluator com Contrato e Rubrica
type: pattern
tags: [agentic-ai, traycer, evaluation, project-methodology, tokens]
created: 2026-10-29
provenance: obsidian_vault
seen_in: [obsidian_vault, dotfiles]
verified: 2026-10-29 via build real (vault 4 sprints, dotfiles 1 sprint) e leitura dos artifacts do épico Traycer
confidence: low
scope: global
---

# Autobuild - Loop Adversarial Generator Evaluator com Contrato e Rubrica

**Três agentes constroem e verificam uma entrega grande quase sem o usuário. O Planner escreve a spec e a rubrica. O Generator constrói. O Evaluator tenta quebrar o resultado. Cada sprint só fecha com dois vereditos: contrato e rubrica.**

Origem: build `harness-tokens-aprendizado` (2026-10-29). Fontes vivas: artifacts do épico Traycer `83132f3f` em `harness-tokens-aprendizado/` (`autobuild-spec`, `autobuild-rubrica`, `autobuild-vault`, `autobuild-dotfiles`).

## Por que funciona

- O Evaluator executa o código. Ele não lê o diff. Na rodada 02 do sprint 3, remover o `locked` do `propose` passava em 105 testes e perdia `session_ids` em 8 de 15 rodadas paralelas.
- O contrato é negociado antes do código. O Evaluator reprovou o contrato v1 do sprint 4 com 13 objeções. Uma delas: pasta de estado começada por `-` virava opção do `find`.
- Os inegociáveis impedem o par de baixar a barra. Só o Planner ou o usuário muda um deles.
- O estado fica em arquivo (`generator-state.json`, `evaluator-state.json`, `evaluator-bin/`). Um agente novo reproduz a rodada sem o chat antigo.

## Como aplicar

1. **Feche a intenção com o usuário.** Escreva dor, métrica, fora do escopo e decisões. Verifique a spec contra o repo antes. A decisão 18 mandava implementar algo que o RFC-002 §9 já rejeitara.
2. **Escreva a spec de alto nível.** Inclua objetivo, fora do escopo, tabela de builds com base `master @sha`, 3 a 6 sprints em comportamento e 8 a 10 invariantes que nenhum contrato afrouxa.
3. **Escreva a rubrica.**
   - 4 inegociáveis, cada um com procedimento de verificação e condição de falha.
   - Critérios com peso, com descrição de nota 5 e nota 2. Pese onde o modelo erra mais: bordas e força dos testes.
   - Um par bom/ruim de calibração por critério.
   - Passa quando os inegociáveis passam, cada critério tem nota 3 ou mais e a média ponderada é 4 ou mais. Critério que não se aplica vira `n/a`.
4. **Escreva o caminho de avaliação.** Liste os comandos das suítes com a contagem de linha de base, rodada pelo Planner. Dê ao Evaluator um bloco de ambiente isolado (`WT`, `EV=$(mktemp -d)`, estado e vault apontados para o worktree). Proíba escrita no worktree do Generator e nos caminhos reais do usuário.
5. **Lance o par.** Generator `claude` sonnet high. Evaluator `claude` opus high. Ambos filhos Traycer, com `expectReply: true`, senão o loop para.
6. **Rode cada sprint.** O Generator propõe o contrato. O Evaluator ataca. Depois o Generator constrói e o Evaluator roda a rodada. Tetos por sprint: 4 trocas de contrato, 3 rodadas, 1 restart. Acima do teto, o par para e o Planner escala ao usuário.
7. **Use quebra por mutação.** O Evaluator copia o worktree para `$EV`, quebra a regra e confirma que o teste novo falha.
8. **Pare antes do merge.** Agentes só fazem commit WIP na branch do build. Squash e merge são do usuário.

## O que NÃO funcionou

- **Teto de contexto errado.** Uma sessão nova já nasce com cerca de 82k tokens. O teto de 100k não cabia. Generator e Evaluator chegaram a 246k e 224k sem avisar. Conte o trabalho acima da base e peça relançamento perto de 160k totais.
- **Evaluator em `antigravity`.** Falhou duas vezes com `thinking.signature: Field required` no segundo turno. Esse harness não serve para papel multi-turno.
- **Rate limit.** A janela de 5h chegou a 100% e o Evaluator parou. Não repita a chamada. Espere a janela renovar e acorde o mesmo agente.
- **Planner trocado.** Um Planner deu erro de API em 3 turnos. Outro chegou a 238k. O Planner novo precisa mandar o próprio id aos filhos antes de qualquer ação.
- **Scripts só no chat.** Os comandos de fixture do Evaluator ficaram no histórico. Grave-os em `evaluator-bin/` desde a rodada 1.
- **Gatilho ignorado.** O plano mandava par novo na rodada 3. O par rodou no mesmo contexto e passou. Decida o gatilho como regra ou descarte-o.
- **Guard de diff.** Um teste que compara `master...HEAD` reprova qualquer branch futura que edite notas fora da pasta da skill, sem defeito no código.

## 🔗 Conexões

- [[Contrato de Direção Antes do Código]]
- [[Rubrica em Prosa Vira Gabarito de Evidência]]
- [[Benchmark Sem Baseline Degenerado Não Diz Quanto do Score é Capacidade]]
- [[Detector Determinístico Fora do LLM como Piso de Qualidade]]
- [[Traycer - Workspace de Agentes em Worktrees Paralelas]]
- [[Playbook - Autobuild no outlet_promo com Documentos do ECC]]
