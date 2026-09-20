---
title: Escolher Subdomínio é Escolher Sessão Separada
type: trap
tags: [frontend, security, browser, localStorage, same-origin, architecture, armadilha]
created: 2026-09-20
provenance: orbita-platform
project: orbita-platform
---

# Escolher Subdomínio é Escolher Sessão Separada

## O ponto

Decidir que uma área nova do produto vai morar em `algo.dominio.com` parece
uma decisão de **marca e roteamento**. Não é só isso: se a sessão é guardada
em `localStorage`, `sessionStorage` ou IndexedDB, a decisão também determina
que **o usuário vai logar de novo** ao atravessar.

Esses três storages são por **origem** (esquema + host + porta), e
`app.dominio.com` e `beneficios.dominio.com` são origens diferentes. O token
salvo numa não existe na outra. Não há configuração que conserte isso —
diferente de cookies, que podem ser emitidos para `.dominio.com` e valer em
todos os subdomínios.

## Por que morde

A conversa de produto costuma ser "queremos uma marca própria para isso", e a
resposta técnica correta é "mesmo app, host novo, zero container novo" — o que
é verdade e barato. O segundo login não aparece em nenhuma das duas frases, e
só é descoberto quando alguém testa o fluxo completo.

No caso real, a consequência era aceitável e até coerente (as outras áreas do
produto — consultor, admin — já tinham login próprio pelo mesmo motivo), mas
**precisava ser dita antes**, não descoberta depois: ela muda a tela de
entrada da área nova, que passa a precisar de login e cadastro próprios em vez
de herdar a sessão.

## Como decidir com o custo à vista

Ao propor subdomínio para uma área nova, declare junto:

1. **Storage de sessão atual.** `localStorage`/`sessionStorage`/IndexedDB ⇒
   login novo. Cookie com `Domain=.dominio.com` ⇒ sessão compartilhada, mas aí
   a superfície de CSRF cresce para todos os subdomínios.
2. **CORS.** O host novo precisa entrar na allowlist de origens da API, senão
   a primeira chamada da área nova falha no navegador — e o teste de
   integração no servidor **não** pega, porque CORS é imposto pelo browser.
3. **Build-time vs runtime.** Em frameworks que fazem replace estático de
   variáveis públicas no bundle (`NEXT_PUBLIC_*` no Next), o host novo precisa
   ser **build-arg**, não só env de runtime — esquecer isso produz um bundle
   que não conhece o host novo.

Caminho alternativo, quando o segundo login for inaceitável: path em vez de
subdomínio (`/area`), que mantém a origem e a sessão, ao custo de abrir mão da
marca própria no endereço.

Relacionado: [[Gate de Autenticação na Página Deixa as Rotas Irmãs Abertas]],
[[Imagem de Deploy Carrega ENV que Quebra Teste de Valor Default]].
