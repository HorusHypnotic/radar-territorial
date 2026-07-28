import json
import logging
import logging.config
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yaml
from supabase import create_client

from python.audit import registrar_evento
from python.snapshots import salvar_snapshot
from python.indicators import (
    calcular_cobertura,
    calcular_densidade,
    calcular_risco,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import (
    DATE_CUTOFF_DAYS,
    OUTPUT_DIR,
    STAGING_DIR,
    SUPABASE_KEY,
    SUPABASE_TABLE,
    SUPABASE_URL,
)

LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

with open(Path(__file__).resolve().parent.parent / "config" / "logging.yaml", "r", encoding="utf-8") as handle:
    LOG_CONFIG = yaml.safe_load(handle)

logging.config.dictConfig(LOG_CONFIG)
logger = logging.getLogger(__name__)


class PipelineRadar:
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Defina SUPABASE_URL e SUPABASE_SERVICE_KEY no arquivo .env")
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Conectado ao Supabase")

    def extract(self):
        logger.info("Extraindo dados do Supabase...")
        try:
            response = self.supabase.table(SUPABASE_TABLE).select("*").execute()
            if not getattr(response, "data", None):
                logger.warning("Nenhum dado encontrado na tabela radar")
                registrar_evento("pipeline_extracao_sem_dados", detalhes={"tabela": SUPABASE_TABLE})
                return pd.DataFrame()
            df = pd.DataFrame(response.data)
            logger.info(f"Extraídos {len(df)} registros")
            registrar_evento(
                "pipeline_extracao",
                detalhes={"tabela": SUPABASE_TABLE, "registros": len(df)},
            )
            return df
        except Exception as exc:
            logger.error(f"Erro na extração: {exc}")
            registrar_evento("pipeline_extracao_erro", detalhes={"erro": str(exc)})
            raise

    def transform(self, df):
        logger.info("Transformando dados...")
        if df.empty:
            logger.warning("DataFrame vazio, pulando transformação")
            return df

        df = df.copy()
        if "data_coleta" in df.columns:
            df["data_coleta"] = pd.to_datetime(df["data_coleta"], errors="coerce")
            cutoff = datetime.now() - timedelta(days=DATE_CUTOFF_DAYS)
            recent_df = df[df["data_coleta"] > cutoff]
            if not recent_df.empty:
                df = recent_df

        if "indicador" in df.columns:
            df["indicador_ajustado"] = df["indicador"] * 1.2

        df = calcular_densidade(df)
        df = calcular_risco(df)
        df = calcular_cobertura(df)

        STAGING_DIR.mkdir(parents=True, exist_ok=True)
        staging_path = STAGING_DIR / "radar_staging.parquet"
        df.to_parquet(staging_path, index=False)
        registrar_evento(
            "pipeline_transformacao",
            detalhes={"staging_path": str(staging_path), "registros": len(df)},
        )
        logger.info(f"Arquivo de staging criado em {staging_path}")
        return df

    def export(self, df):
        logger.info("Exportando dados para saída...")
        if df.empty:
            logger.warning("Nenhum dado para exportar")
            return

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / "radar_geojson.geojson"

        if {"longitude", "latitude"}.issubset(df.columns):
            df = df.dropna(subset=["longitude", "latitude"])
            if df.empty:
                logger.warning("Não há coordenadas válidas para exportar")
                return

            features = []
            for row in df.to_dict(orient="records"):
                properties = {
                    key: value
                    for key, value in row.items()
                    if key not in {"longitude", "latitude"}
                }
                features.append(
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [float(row["longitude"]), float(row["latitude"])],
                        },
                        "properties": properties,
                    }
                )

            geojson = {"type": "FeatureCollection", "features": features}
            with output_path.open("w", encoding="utf-8") as handle:
                json.dump(geojson, handle, ensure_ascii=False, indent=2)

            registrar_evento(
                "pipeline_exportacao",
                detalhes={"geojson_path": str(output_path), "features": len(features)},
            )
            logger.info(f"GeoJSON salvo em {output_path}")
        else:
            logger.warning("Colunas longitude/latitude não encontradas; exportação pulada")

    def run(self):
        logger.info("Iniciando pipeline Radar Territorial")
        df_raw = self.extract()
        df_staging = self.transform(df_raw)
        self.export(df_staging)
        snapshot = salvar_snapshot(df_staging, metadata_extra={"status": "exportado"})
        registrar_evento(
            "pipeline_snapshot",
            detalhes={"timestamp": snapshot["timestamp"], "registros": snapshot["total_registros"]},
        )
        logger.info("Pipeline concluído com sucesso")
        registrar_evento("pipeline_concluido", detalhes={"status": "ok"})
        try:
            from python.export.dashboard_data import carregar_dados_para_dashboard

            carregar_dados_para_dashboard()
        except Exception as exc:
            logger.warning(f"Não foi possível atualizar o dashboard: {exc}")
        return True


if __name__ == "__main__":
    pipeline = PipelineRadar()
    pipeline.run()
