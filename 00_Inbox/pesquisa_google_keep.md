# Técnicas Avançadas de RAG e Economia de Tokens

• Compressão Semântica: Uso de modelos menores para resumir outputs de ferramentas e trechos da conversa antes de enviar ao agente principal, reduzindo o histórico processado.

• Estruturação de Contexto: Priorização de informações estáticas e instruções no início do prompt para maximizar taxas de cache e reduzir custos.

• Limites de Processamento (Capping): Definição de limites (budgets) de tokens para o raciocínio da IA, evitando loops infinitos e protegendo o orçamento.

• RAG Avançado:

• Chunking Semântico: Divisão de documentos com base no significado das frases.

• Reranking: Reordenação dos resultados para priorizar a informação de maior densidade de dados.

• Busca Híbrida: Combinação de busca de palavras-chave com semântica para precisão cirúrgica na recuperação do contexto.

# Servidor MCP Tree-sitter

• Link: <https://github.com/wrale/mcp-server-tree-sitter>

• Descrição: Um servidor de Modelo Context Protocol (MCP) que fornece capacidades de análise de código usando tree-sitter.

• Funcionalidades: Permite que assistentes de IA (como o Claude Desktop) extraiam a árvore de sintaxe abstrata (AST), símbolos, e naveguem pela estrutura do código fonte de forma eficiente.

• Instalação: Pode ser instalado e configurado para rodar com o Claude Desktop, ajudando no gerenciamento de contexto do projeto.

# Integração Tree-sitter, Poda de Tokens e Claude Code

• O Tree-sitter é utilizado para analisar e extrair a estrutura sintática (AST) do código-fonte.

• Com base nessa estrutura, são aplicados filtros de poda de tokens.

• O Claude Code recebe apenas os trechos de código realmente relevantes para a tarefa em execução, otimizando o uso do contexto.

# PagedAttention / vLLM (Otimização de Cache de KV)

• Técnica para otimização de Cache de KV.

• Gerencia a memória de forma eficiente.

• Essencial para aumentar o rendimento em modelos de linguagem.

# Unieval (Poda de Tokens)

• Método de poda de tokens durante a inferência.

• Analisa a relevância das palavras no contexto.

• Descarta palavras dispensáveis, economizando recursos computacionais.

# LongLLMLingua (Compressão de Prompts)

• Técnica que reduz o tamanho do texto do prompt.

• Mantém a informação essencial para o modelo.

• Otimiza o consumo de tokens durante a geração.

# Neural Composer

• Plugin para Obsidian que se integra com servidores locais de LightRAG.

• Constrói e atualiza um grafo de conhecimentos das suas notas automaticamente.

• Permite visualização e buscas híbridas dentro do próprio aplicativo sem precisar sair dele.

# Graphify

• Transforma pastas de projetos (código, PDFs, markdown) em um grafo de conhecimentos consultável por IAs.

• Utiliza extração local (tree-sitter AST) para código e análise semântica por subagentes para documentos.

• Implementação: Requer instalação via pip, após a qual o comando `/graphify` cria um mapa estruturado do projeto, sem depender de bancos vetoriais.

• Relevância: Muito mais eficiente que busca por grep, reduzindo drasticamente o consumo de tokens em consultas repetitivas.

# Integração Graphify e Neural Composer

• O Graphify mapeia a estrutura do código e dependências em repositórios para IAs de desenvolvimento.

• O Neural Composer com LightRAG cria grafos de conhecimento em documentos e notas no Obsidian.

• Uso Integrado: Utilize o Graphify para gerenciar a arquitetura do código e o Neural Composer para consolidar a documentação e conceitos de pesquisa, permitindo que ambos os contextos sejam acessados e assimilados de forma unificada.

# Integração Tree-sitter e Graphify

• O Graphify utiliza o Tree-sitter como motor de análise sintática (AST) para processar código localmente.

• O Tree-sitter extrai a estrutura do código de forma incremental e rápida, sem consumir tokens, para construir o grafo de conhecimentos.

• As outras aplicações de notas e conceitos (como o Neural Composer) focam em análise semântica de textos e não dependem diretamente do Tree-sitter.

# Tree-sitter

• Biblioteca de análise sintática incremental e gerador de parsers.

• Cria árvores de sintaxe (AST) a partir de arquivos de código-fonte de forma extremamente rápida.

• Permite processar modificações no código incrementalmente, sem necessidade de reprocessar todo o arquivo.

• Utilizado para realce de sintaxe em tempo real, navegação de código, refatoração, linting e análise estática em vários editores de código modernos.
