# Radar Territorial

Projeto base para um laboratório de geointeligência com fluxo de dados, processamento em Python e visualização no QGIS.

## Estrutura

- `config/`: parâmetros e logs
- `data/`: dados brutos, staging e saída
- `database/`: SQL e migrações
- `python/`: ingestão, processamento, indicadores e exportação
- `qgis/`: projetos e estilos
- `tests/`: testes automatizados

## Execução

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python python/pipeline.py
```
