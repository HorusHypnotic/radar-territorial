
-- =========================================================
-- Radar Urbano — Fase 0: schema-base do motor territorial
-- =========================================================

-- Roles ----------------------------------------------------
CREATE TYPE public.app_role AS ENUM ('admin', 'operator', 'viewer');

CREATE TABLE public.user_roles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  role public.app_role NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, role)
);

ALTER TABLE public.user_roles ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION public.has_role(_user_id UUID, _role public.app_role)
RETURNS BOOLEAN
LANGUAGE SQL
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.user_roles
    WHERE user_id = _user_id AND role = _role
  )
$$;

CREATE POLICY "Users can view their own roles"
  ON public.user_roles FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id OR public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins manage roles"
  ON public.user_roles FOR ALL
  TO authenticated
  USING (public.has_role(auth.uid(), 'admin'))
  WITH CHECK (public.has_role(auth.uid(), 'admin'));

-- Data sources --------------------------------------------
CREATE TABLE public.data_sources (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  kind TEXT NOT NULL, -- diario_oficial | crea | licitacao | observacao | api
  url TEXT,
  jurisdiction TEXT,  -- ex: 'GO/Goiania'
  licitude TEXT NOT NULL DEFAULT 'public',
  retention_days INTEGER NOT NULL DEFAULT 365,
  reliability_score NUMERIC(4,3) NOT NULL DEFAULT 0.800
    CHECK (reliability_score BETWEEN 0 AND 1),
  responsible TEXT,
  active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Bairros (cadastro normalizado)
CREATE TABLE public.neighborhoods (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  city TEXT NOT NULL,
  state TEXT NOT NULL,
  name TEXT NOT NULL,
  slug TEXT NOT NULL,
  centroid_lat DOUBLE PRECISION,
  centroid_lng DOUBLE PRECISION,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (city, state, slug)
);

-- Entities (obras, empresas, fornecedores, loteamentos)
CREATE TABLE public.urban_entities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_type TEXT NOT NULL, -- 'obra' | 'empresa' | 'fornecedor' | 'loteamento' | 'galpao'
  name TEXT,
  address TEXT,
  neighborhood_id UUID REFERENCES public.neighborhoods(id),
  lat DOUBLE PRECISION,
  lng DOUBLE PRECISION,
  geocode_confidence NUMERIC(4,3),
  geocode_provider TEXT,
  responsible_technical TEXT,
  company TEXT,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  status TEXT NOT NULL DEFAULT 'active',
  first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_seen_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_urban_entities_neighborhood ON public.urban_entities(neighborhood_id);
CREATE INDEX idx_urban_entities_type ON public.urban_entities(entity_type);
CREATE INDEX idx_urban_entities_latlng ON public.urban_entities(lat, lng);

-- Eventos (a tabela-coração)
CREATE TABLE public.urban_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type TEXT NOT NULL, -- new_permit | habite_se | art | bid | observation | alert | supply_signal
  severity TEXT NOT NULL DEFAULT 'low', -- low|medium|high
  source_id UUID REFERENCES public.data_sources(id),
  entity_id UUID REFERENCES public.urban_entities(id),
  neighborhood_id UUID REFERENCES public.neighborhoods(id),
  bairro_label TEXT,
  title TEXT,
  description TEXT,
  lat DOUBLE PRECISION,
  lng DOUBLE PRECISION,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  confidence NUMERIC(4,3) NOT NULL DEFAULT 0.700,
  needs_review BOOLEAN NOT NULL DEFAULT false,
  reviewed_by UUID,
  reviewed_at TIMESTAMPTZ,
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_urban_events_occurred_at ON public.urban_events(occurred_at DESC);
CREATE INDEX idx_urban_events_type ON public.urban_events(event_type);
CREATE INDEX idx_urban_events_neighborhood ON public.urban_events(neighborhood_id);
CREATE INDEX idx_urban_events_needs_review ON public.urban_events(needs_review) WHERE needs_review;

-- Documentos formais
CREATE TABLE public.permits (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id UUID REFERENCES public.urban_events(id) ON DELETE CASCADE,
  entity_id UUID REFERENCES public.urban_entities(id),
  permit_number TEXT,
  permit_type TEXT,
  issued_at DATE,
  raw JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE public.licenses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id UUID REFERENCES public.urban_events(id) ON DELETE CASCADE,
  entity_id UUID REFERENCES public.urban_entities(id),
  license_number TEXT,
  license_type TEXT, -- habite-se, regularizacao, etc.
  issued_at DATE,
  raw JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE public.technical_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id UUID REFERENCES public.urban_events(id) ON DELETE CASCADE,
  entity_id UUID REFERENCES public.urban_entities(id),
  art_number TEXT,
  professional TEXT,
  activity TEXT,
  issued_at DATE,
  raw JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Scores territoriais (snapshot semanal)
CREATE TABLE public.territorial_scores (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  neighborhood_id UUID NOT NULL REFERENCES public.neighborhoods(id) ON DELETE CASCADE,
  window_start DATE NOT NULL,
  window_end   DATE NOT NULL,
  score NUMERIC(8,2) NOT NULL,
  components JSONB NOT NULL DEFAULT '{}'::jsonb, -- {alvaras:x, arts:y, ...}
  trend NUMERIC(6,2),
  computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (neighborhood_id, window_start, window_end)
);
CREATE INDEX idx_scores_neighborhood ON public.territorial_scores(neighborhood_id, window_end DESC);

-- Regras de alerta
CREATE TABLE public.alert_rules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  description TEXT,
  condition JSONB NOT NULL, -- DSL simples
  severity TEXT NOT NULL DEFAULT 'medium',
  active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Auditoria (append-only)
CREATE TABLE public.governance_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  actor UUID,
  action TEXT NOT NULL,
  target_table TEXT,
  target_id UUID,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  source_id UUID REFERENCES public.data_sources(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_governance_logs_created_at ON public.governance_logs(created_at DESC);

-- =========================================================
-- RLS
-- =========================================================
ALTER TABLE public.data_sources       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.neighborhoods      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.urban_entities     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.urban_events       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.permits            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.licenses           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.technical_records  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.territorial_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alert_rules        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.governance_logs    ENABLE ROW LEVEL SECURITY;

-- Leitura pública via server functions usa supabaseAdmin (bypassa RLS).
-- Para acesso autenticado: operadores/admins têm acesso completo de leitura.
-- Sem políticas SELECT abertas para anon — leitura pública só pelos endpoints públicos curados.

CREATE POLICY "Staff read data_sources" ON public.data_sources
  FOR SELECT TO authenticated
  USING (public.has_role(auth.uid(),'operator') OR public.has_role(auth.uid(),'admin'));
CREATE POLICY "Admin writes data_sources" ON public.data_sources
  FOR ALL TO authenticated
  USING (public.has_role(auth.uid(),'admin'))
  WITH CHECK (public.has_role(auth.uid(),'admin'));

CREATE POLICY "Staff read neighborhoods" ON public.neighborhoods
  FOR SELECT TO authenticated
  USING (public.has_role(auth.uid(),'operator') OR public.has_role(auth.uid(),'admin'));
CREATE POLICY "Staff write neighborhoods" ON public.neighborhoods
  FOR ALL TO authenticated
  USING (public.has_role(auth.uid(),'operator') OR public.has_role(auth.uid(),'admin'))
  WITH CHECK (public.has_role(auth.uid(),'operator') OR public.has_role(auth.uid(),'admin'));

CREATE POLICY "Staff read entities" ON public.urban_entities
  FOR SELECT TO authenticated
  USING (public.has_role(auth.uid(),'operator') OR public.has_role(auth.uid(),'admin'));
CREATE POLICY "Staff write entities" ON public.urban_entities
  FOR ALL TO authenticated
  USING (public.has_role(auth.uid(),'operator') OR public.has_role(auth.uid(),'admin'))
  WITH CHECK (public.has_role(auth.uid(),'operator') OR public.has_role(auth.uid(),'admin'));

CREATE POLICY "Staff read events" ON public.urban_events
  FOR SELECT TO authenticated
  USING (public.has_role(auth.uid(),'operator') OR public.has_role(auth.uid(),'admin'));
CREATE POLICY "Staff write events" ON public.urban_events
  FOR ALL TO authenticated
  USING (public.has_role(auth.uid(),'operator') OR public.has_role(auth.uid(),'admin'))
  WITH CHECK (public.has_role(auth.uid(),'operator') OR public.has_role(auth.uid(),'admin'));

CREATE POLICY "Staff read permits" ON public.permits
  FOR SELECT TO authenticated
  USING (public.has_role(auth.uid(),'operator') OR public.has_role(auth.uid(),'admin'));
CREATE POLICY "Staff read licenses" ON public.licenses
  FOR SELECT TO authenticated
  USING (public.has_role(auth.uid(),'operator') OR public.has_role(auth.uid(),'admin'));
CREATE POLICY "Staff read arts" ON public.technical_records
  FOR SELECT TO authenticated
  USING (public.has_role(auth.uid(),'operator') OR public.has_role(auth.uid(),'admin'));

CREATE POLICY "Staff read scores" ON public.territorial_scores
  FOR SELECT TO authenticated
  USING (public.has_role(auth.uid(),'operator') OR public.has_role(auth.uid(),'admin'));

CREATE POLICY "Staff read rules" ON public.alert_rules
  FOR SELECT TO authenticated
  USING (public.has_role(auth.uid(),'operator') OR public.has_role(auth.uid(),'admin'));
CREATE POLICY "Admin writes rules" ON public.alert_rules
  FOR ALL TO authenticated
  USING (public.has_role(auth.uid(),'admin'))
  WITH CHECK (public.has_role(auth.uid(),'admin'));

CREATE POLICY "Admin reads logs" ON public.governance_logs
  FOR SELECT TO authenticated
  USING (public.has_role(auth.uid(),'admin'));
-- inserts em governance_logs feitos somente via service role (servidor)

-- =========================================================
-- Seed mínimo: data_sources de Goiânia + alguns bairros
-- =========================================================
INSERT INTO public.data_sources (slug,name,kind,url,jurisdiction,reliability_score,responsible) VALUES
  ('do-goiania','Diário Oficial do Município de Goiânia','diario_oficial','https://www.goiania.go.gov.br/diariooficial/','GO/Goiania',0.95,'Prefeitura de Goiânia'),
  ('do-goias','Diário Oficial do Estado de Goiás','diario_oficial','https://www.abegoias.go.gov.br/','GO/Estadual',0.95,'Governo de Goiás'),
  ('crea-go','CREA-GO (ARTs)','crea','https://www.creago.org.br/','GO',0.90,'CREA-GO'),
  ('obs-operacional','Observação operacional (input assistido)','observacao',NULL,'GO/Goiania',0.70,'Equipe Radar Urbano')
ON CONFLICT (slug) DO NOTHING;

INSERT INTO public.neighborhoods (city,state,name,slug,centroid_lat,centroid_lng) VALUES
  ('Goiânia','GO','Setor Industrial','setor-industrial',-16.7150,-49.2900),
  ('Goiânia','GO','Centro','centro',-16.6789,-49.2540),
  ('Goiânia','GO','Jardim América','jardim-america',-16.6850,-49.2820),
  ('Goiânia','GO','Vila Nova','vila-nova',-16.6680,-49.2450),
  ('Goiânia','GO','Setor Sul','setor-sul',-16.6950,-49.2620),
  ('Goiânia','GO','Setor Bueno','setor-bueno',-16.7000,-49.2750),
  ('Goiânia','GO','Setor Marista','setor-marista',-16.7060,-49.2680)
ON CONFLICT (city,state,slug) DO NOTHING;

INSERT INTO public.alert_rules (name,description,condition,severity) VALUES
  ('Aquecimento territorial',
   'Bairro com aumento de eventos ≥30% e ARTs ≥15% em 30d',
   '{"window_days":30,"events_growth_pct":30,"arts_growth_pct":15}'::jsonb,
   'high');
