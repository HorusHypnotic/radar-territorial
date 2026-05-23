
-- ingestion_runs: histórico auditável de cada execução do crawler
CREATE TABLE public.ingestion_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id uuid REFERENCES public.data_sources(id) ON DELETE SET NULL,
  started_at timestamptz NOT NULL DEFAULT now(),
  finished_at timestamptz,
  status text NOT NULL DEFAULT 'running', -- running | success | partial | error
  items_found integer NOT NULL DEFAULT 0,
  items_inserted integer NOT NULL DEFAULT 0,
  items_queued integer NOT NULL DEFAULT 0,
  errors jsonb NOT NULL DEFAULT '[]'::jsonb,
  meta jsonb NOT NULL DEFAULT '{}'::jsonb
);

ALTER TABLE public.ingestion_runs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Staff read ingestion_runs"
  ON public.ingestion_runs FOR SELECT
  TO authenticated
  USING (public.has_role(auth.uid(), 'operator') OR public.has_role(auth.uid(), 'admin'));

CREATE INDEX idx_ingestion_runs_started ON public.ingestion_runs (started_at DESC);

-- urban_events: dedupe + trecho original
ALTER TABLE public.urban_events
  ADD COLUMN IF NOT EXISTS dedupe_hash text,
  ADD COLUMN IF NOT EXISTS raw_excerpt text;

CREATE UNIQUE INDEX IF NOT EXISTS idx_urban_events_dedupe
  ON public.urban_events (dedupe_hash)
  WHERE dedupe_hash IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_urban_events_recent
  ON public.urban_events (occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_urban_events_review
  ON public.urban_events (needs_review, occurred_at DESC)
  WHERE needs_review = true;

-- Seed da fonte oficial
INSERT INTO public.data_sources (slug, name, kind, url, jurisdiction, licitude, reliability_score, responsible, active)
VALUES (
  'diario-oficial-goiania',
  'Diário Oficial do Município de Goiânia',
  'gazette',
  'https://www.goiania.go.gov.br/diariooficial/',
  'GO/Goiânia',
  'public',
  0.90,
  'Prefeitura de Goiânia',
  true
)
ON CONFLICT (slug) DO UPDATE SET
  name = EXCLUDED.name,
  url = EXCLUDED.url,
  reliability_score = EXCLUDED.reliability_score,
  updated_at = now();
