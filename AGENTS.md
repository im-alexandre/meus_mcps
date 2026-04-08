# Repository Guidelines

## Objetivo

Este repositório reúne servidores MCP locais para uso em automação de pesquisa e edição documental. O foco é manter servidores pequenos, legíveis e fáceis de instalar em ambientes locais.

## Estrutura

- `server_llm.py`: integração local com Ollama
- `server_scopus.py`: indexação e busca semântica em acervo Scopus local
- `server_docx.py`: leitura e edição de arquivos `.docx`

## Convenções

- Use Python com alterações pequenas e diretas.
- Prefira funções auxiliares curtas e previsíveis.
- Evite dependências novas sem necessidade operacional clara.
- Quando uma operação alterar documentos, valide o estado antes e depois da escrita.
- Para tabelas em `.docx`, o padrão esperado é: legenda acima no formato `Tabela N – ...`, tabela centralizada, autoajuste, borda superior e inferior na primeira linha, borda inferior na última linha, texto interno em `Times New Roman` tamanho `10` e primeira linha em negrito.
- As tabelas 1 e 2 do documento da dissertação atual são exceções conhecidas de formatação e não devem ser corrigidas automaticamente, salvo solicitação explícita.

## Edição e Testes

- Trate `D:\mcp` como fonte principal.
- Antes de publicar mudanças em um servidor MCP, rode ao menos uma verificação local simples de importação ou execução.
- No `docx-manager`, operações sobre equações devem sempre validar a consistência das referências textuais.
- Quando o usuário pedir uma ação com o `docx-manager`, o comportamento padrão deve ser alterar e salvar in-place no mesmo `.docx`. Só gerar arquivo novo quando o usuário pedir explicitamente uma cópia, uma versão nova ou um caminho de saída diferente.

## Git

- Não versione `pdf-indexer-mcp/` neste repositório.
- Não commite caches, ambientes virtuais ou artefatos temporários.
