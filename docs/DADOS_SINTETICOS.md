# Dados sintéticos para testes

O gerador permite testar o contrato estático do OPERA sem shapefile oficial:

```powershell
python scripts/generate_test_data.py --zones 9 --obras 20 --fornecedores 10 --output data/test
python scripts/export_qgis_to_opera.py --validate data/test
```

`--seed` reproduz exatamente o mesmo cenário. Para substituir uma geração anterior, use `--replace` conscientemente.

Todo pacote recebe `status = "candidato"`, `synthetic = true` e nomes explicitamente sintéticos. O gerador recusa os destinos `data/output` e `frontend/data`, não envia dados ao Supabase e não altera a produção. Ele gera `zonas_poligonos.geojson`, `dashboard_data.json` e `import_manifest.json`, usando o mesmo manifesto SHA-256 e o mesmo validador do fluxo QGIS.
