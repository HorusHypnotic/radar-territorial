# Deploy

O workflow `deploy-pages.yml` publica o repositório como artefato estático no GitHub Pages. Configure a origem do Pages como **GitHub Actions** e faça push para `master` ou `main`.

O arquivo raiz `index.html` redireciona para `frontend/`. O build não depende de CDN; Leaflet é mantido em `frontend/vendor/leaflet/`.

## Snapshot diário

Agende o job diretamente no host do backend, sem expor chave de serviço ou endpoint administrativo:

```cron
59 23 * * * cd /caminho/radar-territorial && .venv/bin/python -m python.modules.eov_job
```

No Windows, crie uma tarefa no Agendador executando `.venv\Scripts\python.exe -m python.modules.eov_job` às 23:59.

## Validação integrada

Antes do merge, execute `python scripts/validate_deploy.py`. O comando monta `_site`, confirma os assets obrigatórios, valida o GeoJSON e rejeita dependências externas ou arquivos privados. Em Linux/macOS, `scripts/deploy-fase3.sh` executa testes e essa validação em sequência.

O utilitário `scripts/extract_polygons.py` aceita SVG/HTML com elementos `polygon`. Por segurança cartográfica, o CRS padrão é `LOCAL:SVG`; um EPSG só pode ser informado junto de uma transformação explícita. Pixels de um desenho nunca são tratados como coordenadas UTM automaticamente.
