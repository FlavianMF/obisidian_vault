---
title: "Skill acha seu motor pelo local do link com readlink -f"
type: permanent
created: 2026-11-10T14:43:25
moc: "Design de Interface com Agente"
tags: [skill, symlink, readlink, zsh]
source_inbox: "601057fd-skill-acha-seu-motor-pelo-local-do-link-com-readlink-f.md"
tier: "L1"
score: 0.761
---

# Skill acha seu motor pelo local do link com readlink -f

Skill instalada como symlink resolve o diretório irmão com dirname(dirname(readlink -f SKILL_DIR)), com variável de ambiente como sobreposição. Evita fixar $HOME/dotfiles. Em zsh, não use variável com comando e espaços sem aspas: não divide em palavras.

# Skill acha seu motor pelo local do link com readlink -f

## Contexto
A skill em questão é projetada para resolver o diretório irmão de um arquivo de configuração, utilizando `readlink -f`. Isso é particularmente útil em ambientes onde a localização dos arquivos pode variar.

## Detalhes
- **Resolução do Diretório**: A skill utiliza `readlink -f` para obter o caminho absoluto do arquivo de skill. Em seguida, aplica `dirname` duas vezes para navegar até o diretório irmão.
- **Sobreposição com Variável de Ambiente**: A variável de ambiente é usada como uma sobreposição para evitar fixar a localização em `$HOME/dotfiles`.
- **Zsh Considerações**: Em zsh, é importante notar que variáveis com comandos e espaços devem ser colocadas entre aspas para evitar divisão em palavras.

## Próximos Passos
- Testar a skill em diferentes ambientes para garantir que ela funcione corretamente.
- Documentar os passos para configurar a skill adequadamente.
- Considerar a implementação de uma função zsh para facilitar o uso da skill.

## Conexões
- [[Design de Interface com Agente]]
