-- 001_initial.sql
-- Schema completo para o OPERA Territorial / Radar
-- Execute no SQL Editor do Supabase

-- Extensões
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ======================
-- TABELAS BASE
-- ======================

CREATE TABLE zonas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  codigo TEXT UNIQUE NOT NULL,
  nome TEXT NOT NULL,
  macrozona TEXT,
  tipo TEXT CHECK (tipo IN ('ZUM','ZEIS','ZCOR','ZUP','ZOR','ZPE','OUTRA')),
  to_ratio NUMERIC(5,2),
  ca_basico NUMERIC(5,2),
  ca_maximo NUMERIC(5,2),
  permeabilidade_min NUMERIC(5,2),
  altura_maxima NUMERIC(5,2),
  nivel_incomodidade TEXT CHECK (nivel_incomodidade IN ('Baixo','Médio','Alto','Crítico')),
  geometria GEOGRAPHY(POLYGON, 4326),
  version INT NOT NULL DEFAULT 1,
  source_import_job_id UUID,
  owner_id UUID,
  created_reason TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE obras (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nome TEXT NOT NULL,
  zona_id UUID REFERENCES zonas(id),
  endereco TEXT,
  status TEXT CHECK (status IN ('planejada','em_andamento','paralisada','concluida')),
  area_total NUMERIC(12,2),
  custo_previsto NUMERIC(12,2),
  inicio_previsto DATE,
  fim_previsto DATE,
  version INT NOT NULL DEFAULT 1,
  source_import_job_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE fornecedores (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nome TEXT NOT NULL,
  cnpj TEXT UNIQUE,
  tipo TEXT CHECK (tipo IN ('material','servico','equipamento','consultoria')),
  ativo BOOLEAN DEFAULT true,
  version INT NOT NULL DEFAULT 1,
  source_import_job_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- ======================
-- TABELAS DE AUDITORIA E VERSIONAMENTO (APMO)
-- ======================

CREATE TABLE audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  table_name TEXT NOT NULL,
  row_id UUID NOT NULL,
  op TEXT NOT NULL CHECK (op IN ('INSERT','UPDATE','DELETE')),
  actor_id UUID,
  at TIMESTAMPTZ DEFAULT now(),
  old_row JSONB,
  new_row JSONB,
  prev_hash TEXT,
  curr_hash TEXT
);

CREATE OR REPLACE FUNCTION audit_log_hash_trigger()
RETURNS TRIGGER AS $$
BEGIN
  NEW.curr_hash := encode(
    sha256(
      COALESCE(NEW.prev_hash, '0x00') || 
      COALESCE(NEW.new_row::text, '') || 
      NEW.at::text || 
      COALESCE(NEW.actor_id::text, '')
    ),
    'hex'
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_audit_hash
BEFORE INSERT ON audit_log
FOR EACH ROW EXECUTE FUNCTION audit_log_hash_trigger();

-- Tabelas de versão
CREATE TABLE zonas_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_id UUID NOT NULL REFERENCES zonas(id) ON DELETE CASCADE,
  version INT NOT NULL,
  snapshot JSONB NOT NULL,
  reason TEXT NOT NULL CHECK (char_length(reason) >= 10),
  edited_by UUID,
  edited_at TIMESTAMPTZ DEFAULT now(),
  valid_from TIMESTAMPTZ NOT NULL DEFAULT now(),
  valid_to TIMESTAMPTZ
);

CREATE TABLE obras_versions (LIKE zonas_versions INCLUDING ALL);
CREATE TABLE fornecedores_versions (LIKE zonas_versions INCLUDING ALL);

-- ======================
-- TABELAS OPERACIONAIS
-- ======================

CREATE TABLE atividades (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  obra_id UUID REFERENCES obras(id) ON DELETE CASCADE,
  nome TEXT NOT NULL,
  tipo TEXT CHECK (tipo IN ('fundacao','estrutura','instalacao','acabamento','infraestrutura')),
  responsavel_id UUID,
  inicio_previsto DATE,
  fim_previsto DATE,
  inicio_real DATE,
  fim_real DATE,
  progresso_pct NUMERIC(5,2) DEFAULT 0,
  custo_previsto NUMERIC(12,2),
  custo_real NUMERIC(12,2),
  version INT NOT NULL DEFAULT 1,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE cronograma (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  obra_id UUID REFERENCES obras(id) ON DELETE CASCADE,
  atividade_id UUID REFERENCES atividades(id) ON DELETE CASCADE,
  baseline_inicio DATE,
  baseline_fim DATE,
  revisao_inicio DATE,
  revisao_fim DATE,
  motivo_revisao TEXT,
  version INT NOT NULL DEFAULT 1,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE ico_registros (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  obra_id UUID REFERENCES obras(id) ON DELETE CASCADE,
  atividade_id UUID REFERENCES atividades(id) ON DELETE CASCADE,
  data_referencia DATE NOT NULL,
  ico_valor NUMERIC(5,2) CHECK (ico_valor BETWEEN 0 AND 100),
  componentes JSONB,
  calculado_por TEXT,
  calculado_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE evidencias (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  obra_id UUID REFERENCES obras(id) ON DELETE CASCADE,
  atividade_id UUID REFERENCES atividades(id) ON DELETE CASCADE,
  tipo TEXT NOT NULL CHECK (tipo IN ('foto','video','audio','pdf','checklist','reo','eco')),
  storage_path TEXT NOT NULL,
  hash_sha256 TEXT NOT NULL,
  exif JSONB,
  gps_lat NUMERIC(10,7),
  gps_lng NUMERIC(10,7),
  captured_at TIMESTAMPTZ,
  device TEXT,
  uploaded_by UUID,
  uploaded_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE ecos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  obra_id UUID REFERENCES obras(id) ON DELETE CASCADE,
  tipo TEXT CHECK (tipo IN ('aditivo','distrato','ocorrencia','medicao','revisao')),
  descricao TEXT NOT NULL,
  impacto_prazo_dias INT,
  impacto_custo NUMERIC(12,2),
  evidencias_ids UUID[],
  status TEXT DEFAULT 'pendente' CHECK (status IN ('pendente','aprovado','rejeitado','implementado')),
  criado_por UUID,
  criado_at TIMESTAMPTZ DEFAULT now(),
  aprovado_por UUID,
  aprovado_at TIMESTAMPTZ,
  version INT NOT NULL DEFAULT 1
);

CREATE TABLE snapshot_operacional (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  obra_id UUID REFERENCES obras(id) ON DELETE CASCADE,
  snapshot_date DATE NOT NULL,
  payload JSONB NOT NULL,
  prev_hash TEXT,
  curr_hash TEXT,
  gerado_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(obra_id, snapshot_date)
);

CREATE TABLE materiais (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  obra_id UUID REFERENCES obras(id) ON DELETE CASCADE,
  nome TEXT NOT NULL,
  unidade TEXT,
  quantidade_prevista NUMERIC(12,3),
  quantidade_real NUMERIC(12,3),
  custo_unitario NUMERIC(12,2),
  fornecedor_id UUID REFERENCES fornecedores(id),
  data_entrada DATE,
  version INT NOT NULL DEFAULT 1,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE equipes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  obra_id UUID REFERENCES obras(id) ON DELETE CASCADE,
  nome TEXT NOT NULL,
  encarregado TEXT,
  membros INT,
  especialidade TEXT,
  ativa BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE ocorrencias (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  obra_id UUID REFERENCES obras(id) ON DELETE CASCADE,
  atividade_id UUID REFERENCES atividades(id) ON DELETE CASCADE,
  tipo TEXT CHECK (tipo IN ('acidente','nao_conformidade','atraso','retrabalho','desvio')),
  descricao TEXT NOT NULL,
  gravidade TEXT CHECK (gravidade IN ('baixa','media','alta','critica')),
  evidencias_ids UUID[],
  resolvida BOOLEAN DEFAULT false,
  registrada_por UUID,
  registrada_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE checklists (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  obra_id UUID REFERENCES obras(id) ON DELETE CASCADE,
  atividade_id UUID REFERENCES atividades(id) ON DELETE CASCADE,
  template_nome TEXT,
  itens JSONB NOT NULL,
  preenchido_por UUID,
  preenchido_at TIMESTAMPTZ DEFAULT now(),
  assinatura_hash TEXT
);

-- ======================
-- RLS (Row Level Security)
-- ======================

ALTER TABLE zonas ENABLE ROW LEVEL SECURITY;
ALTER TABLE obras ENABLE ROW LEVEL SECURITY;
ALTER TABLE fornecedores ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE atividades ENABLE ROW LEVEL SECURITY;
ALTER TABLE ecos ENABLE ROW LEVEL SECURITY;
ALTER TABLE snapshot_operacional ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Leitura pública para zonas" ON zonas FOR SELECT USING (true);
CREATE POLICY "Leitura pública para obras" ON obras FOR SELECT USING (true);
CREATE POLICY "Leitura pública para fornecedores" ON fornecedores FOR SELECT USING (true);
