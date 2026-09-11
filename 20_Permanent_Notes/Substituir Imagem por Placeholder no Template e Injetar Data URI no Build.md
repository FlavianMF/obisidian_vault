---
title: Substituir Imagem por Placeholder no Template e Injetar Data URI no Build
type: pattern
tags: [agentic-ai, build, data-uri, artifact, context-window, html]
created: 2026-09-11
provenance: projetos_ita
project: projetos_ita
---

# Substituir Imagem por Placeholder no Template e Injetar Data URI no Build

## Contexto

Um deck HTML precisava embutir 13 imagens como data URI (CSP bloqueia host externo
em Artifacts). Embutir base64 direto no arquivo editado cria dois problemas para um
agente:

1. **O arquivo vira ilegível para edição** — uma única imagem de 118 KB vira ~160 KB
   de base64 numa linha só. Qualquer `Read` ou `Edit` depois disso é caro e frágil.
2. **O base64 entra no contexto do modelo** — 780 KB de página seriam ~200k tokens
   de lixo se o agente reler o próprio arquivo.

## Padrão

Separar **template** (editável, com placeholders) de **build** (gerado, com base64):

```python
# build.py
repl = { "__SHOT_HERO__": uri("shot_hero.png", "image/png"), ... }
targets = [("deck_template.html", "deck.html"), ...]
for src, dst in targets:
    html = (base/src).read_text()
    for k, v in repl.items(): html = html.replace(k, v)
    (base/dst).write_text(html)
    print(dst, f"{(base/dst).stat().st_size/1024:.1f} KB",
          "placeholders restantes:", html.count("__IMG") + html.count("__SHOT"))
```

No template, a imagem é só `<img src="__SHOT_HERO__" alt="…">`. O agente edita o
template à vontade; o base64 nunca passa pelo contexto dele.

Dois detalhes que evitam bug silencioso:
- **Imprimir quantos placeholders sobraram** no fim do build. Zero é o esperado;
  qualquer outro número denuncia um placeholder digitado errado que viraria `<img>`
  quebrado na página publicada.
- **Publicar o arquivo gerado, não o template** — e, se a ferramenta de publicação
  identifica o artifact pelo caminho do arquivo, passar explicitamente a URL de
  destino, senão a mudança de caminho cria um artifact novo em vez de atualizar o
  existente.

Quando o mesmo conjunto de imagens serve vários documentos, o build vira uma lista de
pares `(template, saída)` com um mapa de placeholders compartilhado — três decks
saíram de um `build.py` só.

## Quando aplicar

Qualquer geração de HTML/SVG/Markdown auto-contido com assets binários embutidos,
especialmente quando um agente vai iterar no arquivo várias vezes. O mesmo raciocínio
vale para qualquer blob grande gerado (fontes em base64, JSON de dados pesado).

## 🔗 Conexões
- [[Screenshot de UI Comprime Melhor com Quantização de Cores que com JPEG]]
- [[Migrar Vários Documentos para um Design System Preservando Nomes de Token e Classe]]
