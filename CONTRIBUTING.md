# Contribuindo

## Fluxo de trabalho

1. Crie uma branch curta a partir do estado mais recente.
2. Mantenha a alteração focada e preserve mudanças locais que não sejam suas.
3. Atualize testes e documentação quando o comportamento mudar.
4. Execute as validações abaixo.
5. Abra um pull request descrevendo resultado, riscos e evidências de teste.

```powershell
python -m pytest -q
python scripts/validate_deploy.py
git diff --check
```

## Convenções

- Python: `snake_case`, classes em `PascalCase`, type hints nos contratos novos e mensagens de erro explícitas.
- JavaScript: ES Modules, `camelCase`, APIs nativas e nenhuma dependência carregada por CDN.
- SQL: nomes em `snake_case`, migrations sequenciais e imutáveis depois de publicadas.
- Frontend: preservar responsividade, navegação por teclado e `prefers-reduced-motion`.

## Segurança e dados

- Nunca envie `.env`, tokens, service keys, dados pessoais ou arquivos geográficos brutos restritos.
- Não declare dados candidatos ou sintéticos como oficiais.
- Não reescreva a versão anterior de uma entidade auditável; registre retificação e motivo.
- Não aplique migrations, RLS ou publicação oficial sem autorização e validação do ambiente de destino.

## Dados sintéticos

```powershell
python scripts/generate_test_data.py --zones 9 --obras 20 --fornecedores 10 --seed 42 --output data/test
python scripts/export_qgis_to_opera.py --validate data/test
```

O gerador recusa `data/output` e `frontend/data`. Não copie o pacote para produção.

## Dados oficiais via QGIS

Use o procedimento de [importação segura](docs/IMPORTACAO_QGIS.md). A publicação requer revisão do candidato, fonte completa, CRS confirmado, autoridade competente e referência legal verdadeira.

## Documentação

- `README.md`: entrada rápida e comandos estáveis;
- `CHANGELOG.md`: mudanças notáveis ainda não lançadas;
- `docs/PRODUCAO_REAL.md`: fonte da verdade sobre o estado operacional;
- documentos especializados em `docs/`: detalhes técnicos e procedimentos.
