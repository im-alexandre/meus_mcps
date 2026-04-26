# Contribuindo

Obrigado pelo interesse em contribuir! Este projeto é voltado a pesquisadores que combinam programação e escrita acadêmica, então qualquer melhoria que facilite esse fluxo é bem-vinda.

## Como reportar um problema

Abra uma [issue](../../issues) descrevendo:

- o que você tentou fazer
- o que aconteceu (mensagem de erro, comportamento inesperado)
- o que era esperado
- versão do Python, sistema operacional e, se aplicável, versão do Ollama

## Como sugerir uma melhoria

Abra uma issue com o prefixo `[sugestão]` no título. Descreva o caso de uso — especialmente se vier de uma necessidade real de pesquisa.

## Como contribuir com código

1. Faça um fork do repositório
2. Crie uma branch a partir de `main`:
   ```bash
   git checkout -b minha-contribuicao
   ```
3. Faça as alterações e adicione testes se aplicável
4. Certifique-se de que o código roda sem erros:
   ```bash
   python -m py_compile server_llm.py server_scopus.py
   ```
5. Abra um pull request descrevendo o que foi alterado e por quê

## Convenções

- Código em inglês; comentários e mensagens de log podem ser em português
- Nomes de funções e variáveis em `snake_case`
- Evite dependências externas novas sem discussão prévia em issue — o projeto prioriza ferramentas locais e leves
- Cada servidor MCP deve permanecer independente (sem importar código de outro servidor)

## Dúvidas

Abra uma issue com o prefixo `[dúvida]`. Não há pergunta pequena demais.
