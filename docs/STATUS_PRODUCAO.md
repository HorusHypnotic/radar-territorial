# Estado de produção

Validação executada em **31/07/2026** sobre o commit `11859f4` (`Fase 3: entidades APMO e mapa híbrido`).

- Site: <https://horushypnotic.github.io/radar-territorial/>
- Testes locais: 34 aprovados, nenhuma falha (execução: 8,88 s)
- CI do commit publicado: 31 testes aprovados, nenhuma falha
- Build: artefato estático aprovado, 214.814 bytes
- Deploy: workflows de testes e GitHub Pages concluídos com sucesso
- Produção: página, tema, fallback demonstrativo, mapa, service worker e GeoJSON responderam HTTP 200

## Matriz funcional

| Componente | Estado verificável | Observação |
|---|---|---|
| Dashboard e KPIs | Disponível | Usa dados estáticos/demonstrativos no Pages |
| Tema escuro | Disponível | CSS local; tipografia usa a pilha de fontes do sistema |
| Mapa territorial | Disponível | Leaflet local em telas maiores e SVG em telas móveis |
| Entidades APMO | Implementadas no código | CRUD depende do backend Python e do Supabase; não é ativado pelo Pages estático |
| Exportação CSV | Disponível | Executada no navegador |
| Livro-razão JSON | Disponível | Cadeia SHA-256 verificável; sem assinatura/timestamp externo enquanto não configurados |
| Exportação PDF | Não implementada | Item de roadmap |
| PWA e offline | Disponível | Manifest, ícones e service worker; cache cobre shell e dados demonstrativos essenciais |
| Dados oficiais | Pendente | GeoJSON e registros publicados são demonstrativos |
| Supabase | Pendente de ativação | Credenciais reais e aplicação das migrations `001`–`005` não foram comprovadas |

## Evidências e limites

O repositório contém 19 arquivos de backend (1.584 linhas), 14 de frontend (961 linhas), 5 migrations SQL (634 linhas) e 6 arquivos de testes após esta validação. Essas contagens são informativas e não substituem métricas de qualidade.

Não há relatório de cobertura nem execução do Lighthouse versionados. Portanto, percentuais de cobertura, notas de performance/acessibilidade/SEO e tempos de carregamento não são declarados como resultados. Eles só devem ser publicados depois de uma medição reproduzível.

O GitHub Pages hospeda apenas o artefato estático. Rotas mutáveis, auditoria persistente, snapshots e CRUD APMO exigem a implantação separada do backend, credenciais do Supabase e banco migrado. Nenhuma chave de serviço deve ser exposta no frontend.

## Como reproduzir

```powershell
python -m pytest -q
python scripts/validate_deploy.py
python scripts/validate_production.py
```

O último comando consulta os arquivos essenciais no endereço público, valida marcadores da interface e confirma que o GeoJSON é uma `FeatureCollection` não vazia. Falhas HTTP, de rede ou de conteúdo encerram o processo com código diferente de zero.

## Próximos bloqueios reais

1. Obter e configurar as credenciais do projeto Supabase fora do repositório.
2. Aplicar e verificar as migrations `001`–`005` no banco de destino.
3. Substituir os polígonos demonstrativos por exportação oficial em EPSG:4326, validada pela equipe responsável.
4. Implantar o backend em ambiente próprio e configurar sua origem permitida.
5. Somente depois, executar teste integrado com persistência, Lighthouse e relatório de cobertura.
