# Deploy

O workflow `deploy-pages.yml` publica o repositório como artefato estático no GitHub Pages. Configure a origem do Pages como **GitHub Actions** e faça push para `master` ou `main`.

O arquivo raiz `index.html` redireciona para `frontend/`. O build não depende de CDN; Leaflet é mantido em `frontend/vendor/leaflet/`.

## Snapshot diário

Agende o job diretamente no host do backend, sem expor chave de serviço ou endpoint administrativo:

```cron
59 23 * * * cd /caminho/radar-territorial && .venv/bin/python -m python.modules.eov_job
```

No Windows, crie uma tarefa no Agendador executando `.venv\Scripts\python.exe -m python.modules.eov_job` às 23:59.
