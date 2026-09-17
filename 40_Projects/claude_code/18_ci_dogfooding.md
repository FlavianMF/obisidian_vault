---
title: O harness rodando headless em CI
type: project
tags: [claude-code, ci-cd, headless, security, dogfooding]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

> Ver [[claude-code]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# O harness rodando em CI, sobre o próprio repositório

[← Índice](00_indice.md)

13 workflows, 8 scripts. Cinco deles rodam o **próprio Claude Code** como agente de manutenção
do repositório. É o melhor exemplo publicado de "harness headless em produção" — e o mais
instrutivo, porque mostra a disciplina de contenção que isso exige.

## Os workflows

| Workflow | O que faz | Usa Claude? |
|---|---|:---:|
| `claude-issue-triage.yml` | Aplica labels a issues novas e a comentários | ✅ |
| `claude-dedupe-issues.yml` | Detecta duplicatas | ✅ |
| `claude.yml` | `@claude` em issue/PR | ✅ |
| `auto-close-duplicates.yml` | Fecha duplicatas confirmadas | |
| `backfill-duplicate-comments.yml` | Retroage comentários de duplicata | |
| `issue-lifecycle-comment.yml` | Comentários de ciclo de vida | |
| `issue-opened-dispatch.yml` | Dispara os demais | |
| `lock-closed-issues.yml` | Tranca issues antigas | |
| `log-issue-events.yml` | Eventos para o Statsig | |
| `non-write-users-check.yml` | Checa permissão do autor | |
| `remove-autoclose-label.yml` | Remove label ao haver atividade | |
| `sweep.yml` | Varredura periódica | |
| `mod-tests.yml` | **Typecheck + testes dos mods** | |

## O padrão de contenção, em quatro camadas

O `claude-issue-triage.yml` é o exemplo completo. Vale destrinchar porque cada linha é uma
decisão de segurança.

### 1. Permissão do workflow, mínima

```yaml
permissions:
  contents: read
  issues: write
  id-token: write   # para cunhar o token OIDC
```

### 2. Autenticação sem chave estática

```yaml
anthropic_federation_rule_id: ${{ vars.ANTHROPIC_FEDERATION_RULE_ID }}
anthropic_organization_id:   ${{ vars.ANTHROPIC_ORGANIZATION_ID }}
anthropic_service_account_id: ${{ vars.ANTHROPIC_SERVICE_ACCOUNT_ID }}
anthropic_workspace_id:      ${{ vars.ANTHROPIC_WORKSPACE_ID }}
```

> Autentica na Claude API via **Workload Identity Federation** (o token OIDC do workflow é
> trocado por um token de acesso de vida curta) em vez de uma API key estática.

Nenhum segredo de longa duração no repositório. Isso é o estado da arte e é replicável em
qualquer CI que emita OIDC.

### 3. Ferramentas restritas a wrappers, não ao `gh`

O comando `/triage-issue` (`.claude/commands/triage-issue.md`, 74 linhas) declara no
frontmatter:

```yaml
allowed-tools: Bash(./scripts/gh.sh:*),Bash(./scripts/edit-issue-labels.sh:*)
```

O agente **não tem acesso ao `gh`**. Tem acesso a dois scripts. E `scripts/gh.sh` é um
wrapper que só deixa passar quatro subcomandos e cinco flags:

```bash
ALLOWED_FLAGS=(--comments --state --limit --label)
case "$CMD" in
  "issue view"|"issue list"|"search issues"|"label list")
```

E força o escopo: `GH_REPO` é derivado do ambiente do workflow e validado com formato
`owner/repo`. O agente não consegue mirar outro repositório nem que queira.

### 4. Orçamento de chamadas

```yaml
env:
  CLAUDE_CODE_SCRIPT_CAPS: '{"edit-issue-labels.sh":2}'
```

O script que **escreve** (aplica labels) pode ser chamado **duas vezes**. Não é uma regra de
permissão — é um teto de quantidade. Um agente em loop não consegue rotular uma issue
cinquenta vezes.

Somando: `timeout-minutes: 10` no job e `5` no passo, `concurrency` com
`cancel-in-progress` por número de issue, e um `if:` que exclui comentários de bot (evitando
que dois agentes conversem entre si).

## O prompt como especificação

O `/triage-issue` vale leitura por si. Ele não é "triage this issue" — é um procedimento:

- **Restrição negativa logo no topo**:
  *"IMPORTANTE: Não poste nenhum comentário ou mensagem na issue. Suas únicas ações são
  adicionar ou remover labels."*
- **Inventário fechado**: *"Você pode SOMENTE usar labels desta lista. Nunca invente labels
  novas."* — e o passo 1 é buscar a lista.
- **Regra de desempate explícita**: *"O texto do corpo é autoritativo. Se um dropdown do
  formulário (ex.: Platform) contradiz evidência no corpo, confie no corpo — dropdowns são
  frequentemente mal selecionados."*
- **Viés declarado em caso de dúvida**: *"Se ambíguo, prossiga para o passo 5 SEM aplicar
  `invalid`."* — na dúvida, a ação menos destrutiva.
- **Critério anti-falso-positivo**: para `needs-repro`, *"NÃO aplique se o usuário já forneceu
  mensagens de erro, logs, caminhos de arquivo, ou uma descrição do que fez. Não exija um
  formato específico — descrições narrativas contam."*

É o mesmo padrão dos agentes de revisão do `pr-review-toolkit`
([14](14_subagentes_skills_comandos.md)): o prompt carrega o *processo* e os *critérios de
não-ação*, não só o objetivo.

## `mod-tests.yml` — a flag que revela o estado do recurso

```yaml
- name: Install Claude Code and TypeScript
  run: npm install -g @anthropic-ai/claude-code typescript@5.9.3
- name: Typecheck each mod's hooks and tests
  run: tsc -p mods/tsconfig.json
- name: Run each mod's tests
  run: |
    if ! claude plugin test --help 2>/dev/null | grep -q '^Usage: claude plugin test'; then
      echo "claude $(claude --version) has no 'plugin test' yet; skipping the test step"
      exit 0
    fi
    for mod in mods/*/; do
      [ -d "$mod/tests" ] || continue
      claude plugin test "$mod" || status=1
    done
  env:
    CLAUDE_CODE_ENABLE_FUNCTION_HOOKS: "1"
```

Três achados:

1. **`CLAUDE_CODE_ENABLE_FUNCTION_HOOKS: "1"`** — toda a API de mods
   ([02](02_modelo_engine_hooks.md)) está atrás de uma **feature flag por variável de
   ambiente**. É a confirmação operacional do aviso *EARLY ACCESS* no topo do `.d.ts`.
2. O passo **se auto-desliga** quando o `claude` instalado ainda não tem `plugin test`, com
   `exit 0` e uma linha de log. O CI tolera a versão do produto estar atrás do source dos
   mods — porque o `npm install -g` pega a versão publicada, não a do PR.
3. `persist-credentials: false` no checkout e action pinada por SHA
   (`actions/checkout@11bd719...`). Higiene de supply chain no próprio repo.

## O que copiar disso

Para qualquer harness próprio que vá rodar agente sem supervisão:

1. **Wrapper, não CLI.** Dê ao agente um script com allowlist de subcomando e flag, não a
   ferramenta real. O allowlist fica em bash, versionado e revisável, não no prompt.
2. **Escopo forçado pelo ambiente**, não pedido ao agente (o `GH_REPO` do `gh.sh`).
3. **Teto de chamadas** para o que escreve, separado da permissão de chamar.
4. **Credencial de vida curta** por federação de identidade.
5. **Concorrência cancelável** por unidade de trabalho, para não ter dois agentes na mesma
   issue.
6. **Restrição negativa no prompt** ("não comente") + **inventário fechado** ("só estas
   labels") + **viés para a não-ação na dúvida**.

## Ver também

- [06](06_permissoes_seguranca.md) — as mesmas ideias dentro do produto
- [14](14_subagentes_skills_comandos.md) — comandos e agentes como arquivos
- [12](12_testing_kit.md) — o que o `mod-tests.yml` está rodando
