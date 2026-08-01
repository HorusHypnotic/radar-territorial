# Importação segura do QGIS

O utilitário `scripts/export_qgis_to_opera.py` gera um candidato a GeoJSON e dashboard sem atribuir caráter oficial automaticamente.

## Dependências

```powershell
pip install -r requirements-qgis.txt
```

## Preparação no QGIS

1. Corrija geometrias inválidas.
2. Confirme o CRS real da camada; não apenas atribua um CRS para eliminar um aviso.
3. Exporte Polygon/MultiPolygon com `.shp`, `.shx`, `.dbf` e `.prj`.
4. Identifique a lei, decreto ou processo administrativo que autoriza os dados.
5. Prepare um mapeamento de campos baseado em `config/qgis-field-map.example.json`.

## Gerar candidato para revisão

```powershell
python scripts/export_qgis_to_opera.py `
  --shapefile "C:\dados\zoneamento.shp" `
  --field-map config\qgis-field-map.example.json `
  --expected-bounds -52 -10 -48 -6 `
  --output data\candidate
```

O resultado recebe `metadata.status = "candidato"` e não substitui produção. Confira no QGIS, valide atributos e obtenha aceite formal.

## Publicar após aprovação

```powershell
python scripts/export_qgis_to_opera.py `
  --shapefile "C:\dados\zoneamento.shp" `
  --field-map config\qgis-field-map.example.json `
  --obras "C:\dados\obras.xlsx" `
  --fornecedores "C:\dados\fornecedores.xlsx" `
  --expected-bounds -52 -10 -48 -6 `
  --authority "Órgão responsável" `
  --legal-reference "Lei/Processo nº ..." `
  --output data\output `
  --publish --replace
```

`--publish` exige autoridade, referência legal e saída `data/output`. `--replace` é obrigatório na prática quando os arquivos demonstrativos já existem. O comando grava o SHA-256 de todos os componentes de origem para rastreabilidade.

## Controles aplicados

- rejeita shapefile sem `.prj`, CRS ou componentes essenciais;
- rejeita dataset vazio, geometrias inválidas e tipos não poligonais;
- reprojeta corretamente para EPSG:4326;
- simplifica em metros e preserva topologia quando solicitado;
- valida limites geográficos opcionais e percentuais;
- preserva corretamente Polygon e MultiPolygon;
- não inventa categoria, atividades ou índices urbanísticos;
- gera UUIDs estáveis, origem, CRS, limites e SHA-256;
- impede sobrescrita sem `--replace`.

Os limites do exemplo são uma barreira ampla, não uma delimitação municipal. Ajuste-os com uma fonte cartográfica confiável. Após publicar, execute testes, `validate_deploy.py`, revisão visual e aprovação do responsável antes do push.
