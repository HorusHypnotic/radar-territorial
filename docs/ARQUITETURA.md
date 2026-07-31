# Arquitetura

O OPERA Territorial reúne três domínios: Radar Territorial (normas e consulta), OPERA Control (execução de obras) e OPERA Atlas (evidências e memória operacional).

O frontend é estático, escrito em HTML, CSS e JavaScript nativos, e pode ser publicado pelo GitHub Pages. Dados locais em `data/output/` são a fonte de contingência. O `server.py` expõe a API local; o pipeline Python extrai dados do Supabase, calcula indicadores e gera GeoJSON e snapshots.

Princípios: operação sem CDN obrigatória, chave de serviço restrita ao backend, registros mutáveis versionados e eventos críticos preservados em trilha de auditoria encadeada por SHA-256.
