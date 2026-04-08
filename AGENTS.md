# Repository Guidelines

## Objetivo

Este repositório reúne servidores MCP locais para uso em automação de pesquisa e edição documental. O foco é manter servidores pequenos, legíveis e fáceis de instalar em ambientes locais.

## Estrutura

- `server_llm.py`: integração local com Ollama
- `server_scopus.py`: indexação e busca semântica em acervo Scopus local
- `server_docx.py`: leitura e edição de arquivos `.docx`
- `prompt.md`: material auxiliar de desenvolvimento

## Convenções

- Use Python com alterações pequenas e diretas.
- Prefira funções auxiliares curtas e previsíveis.
- Evite dependências novas sem necessidade operacional clara.
- Quando uma operação alterar documentos, valide o estado antes e depois da escrita.

## Edição e Testes

- Trate `D:\mcp` como fonte principal.
- Antes de publicar mudanças em um servidor MCP, rode ao menos uma verificação local simples de importação ou execução.
- No `docx-manager`, operações sobre equações devem sempre validar a consistência das referências textuais.

## Git

- Não versione `pdf-indexer-mcp/` neste repositório.
- Não commite caches, ambientes virtuais ou artefatos temporários.
