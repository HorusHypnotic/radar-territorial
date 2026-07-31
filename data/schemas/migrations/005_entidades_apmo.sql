-- Fase 3 — entidades operacionais APMO.
-- Pré-requisitos: tabelas obras/fornecedores e migrations 001–004.

create table if not exists public.atividades (
  id uuid primary key default gen_random_uuid(),
  obra_id uuid not null references public.obras(id) on delete cascade,
  nome text not null check (char_length(trim(nome)) > 0),
  tipo text not null check (tipo in ('fundacao','estrutura','instalacao','acabamento','servico','outro')),
  responsavel_id uuid,
  inicio_previsto date,
  fim_previsto date,
  inicio_real date,
  fim_real date,
  progresso_pct numeric(5,2) not null default 0 check (progresso_pct between 0 and 100),
  custo_previsto numeric(14,2) check (custo_previsto >= 0),
  custo_real numeric(14,2) check (custo_real >= 0),
  descricao text,
  status text not null default 'planejada' check (status in ('planejada','em_andamento','concluida','paralisada')),
  prioridade integer not null default 1 check (prioridade between 1 and 5),
  source_import_job_id uuid references public.import_jobs(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  updated_by uuid,
  version integer not null default 1 check (version > 0),
  deleted_at timestamptz,
  check (fim_previsto is null or inicio_previsto is null or fim_previsto >= inicio_previsto),
  check (fim_real is null or inicio_real is null or fim_real >= inicio_real)
);

create table if not exists public.cronograma (
  id uuid primary key default gen_random_uuid(),
  obra_id uuid not null references public.obras(id) on delete cascade,
  atividade_id uuid references public.atividades(id) on delete cascade,
  baseline_inicio date not null,
  baseline_fim date not null,
  revisao_inicio date,
  revisao_fim date,
  motivo_revisao text,
  aprovado_por uuid,
  aprovado_at timestamptz,
  source_import_job_id uuid references public.import_jobs(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  updated_by uuid,
  version integer not null default 1 check (version > 0),
  check (baseline_fim >= baseline_inicio),
  check (revisao_fim is null or revisao_inicio is null or revisao_fim >= revisao_inicio),
  check ((revisao_inicio is null and revisao_fim is null) or char_length(trim(coalesce(motivo_revisao, ''))) >= 20)
);

create table if not exists public.ico_registros (
  id uuid primary key default gen_random_uuid(),
  obra_id uuid not null references public.obras(id) on delete cascade,
  atividade_id uuid references public.atividades(id) on delete set null,
  data_referencia date not null default current_date,
  ico_valor numeric(5,2) not null check (ico_valor between 0 and 100),
  componentes jsonb not null check (jsonb_typeof(componentes) = 'object'),
  calculado_por uuid,
  calculado_at timestamptz not null default now(),
  metodo text not null default 'ponderado' check (metodo in ('ponderado','manual')),
  peso_qualidade numeric(4,3) not null default 0.25 check (peso_qualidade between 0 and 1),
  peso_prazo numeric(4,3) not null default 0.25 check (peso_prazo between 0 and 1),
  peso_custo numeric(4,3) not null default 0.25 check (peso_custo between 0 and 1),
  peso_seguranca numeric(4,3) not null default 0.25 check (peso_seguranca between 0 and 1),
  observacao text,
  unique (obra_id, data_referencia),
  check (abs((peso_qualidade + peso_prazo + peso_custo + peso_seguranca) - 1) < 0.001)
);

create table if not exists public.evidencias (
  id uuid primary key default gen_random_uuid(),
  obra_id uuid references public.obras(id) on delete cascade,
  atividade_id uuid references public.atividades(id) on delete set null,
  tipo text not null check (tipo in ('foto','video','audio','pdf','checklist','reo','eco','documento')),
  storage_path text not null,
  hash_sha256 text not null check (hash_sha256 ~ '^[0-9a-f]{64}$'),
  exif jsonb,
  gps_lat numeric(10,7) check (gps_lat between -90 and 90),
  gps_lng numeric(10,7) check (gps_lng between -180 and 180),
  captured_at timestamptz,
  device text,
  tamanho_bytes bigint not null check (tamanho_bytes >= 0),
  mime_type text not null,
  upload_id uuid,
  uploaded_by uuid,
  uploaded_at timestamptz not null default now(),
  descricao text,
  tags text[] not null default '{}',
  aprovado boolean not null default false,
  aprovado_por uuid,
  aprovado_at timestamptz,
  deleted_at timestamptz,
  check ((aprovado = false) or (aprovado_por is not null and aprovado_at is not null)),
  check (obra_id is not null or atividade_id is not null)
);

create table if not exists public.ecos (
  id uuid primary key default gen_random_uuid(),
  obra_id uuid not null references public.obras(id) on delete cascade,
  tipo text not null check (tipo in ('aditivo','distrato','ocorrencia','medicao','revisao','outro')),
  descricao text not null check (char_length(trim(descricao)) > 0),
  impacto_prazo_dias integer,
  impacto_custo numeric(14,2),
  evidencias_ids uuid[] not null default '{}',
  status text not null default 'pendente' check (status in ('pendente','aprovado','rejeitado','cancelado')),
  criado_por uuid,
  criado_at timestamptz not null default now(),
  aprovado_por uuid,
  aprovado_at timestamptz,
  motivo text,
  valor_original numeric(14,2),
  valor_novo numeric(14,2),
  source_import_job_id uuid references public.import_jobs(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  updated_by uuid,
  version integer not null default 1 check (version > 0)
);

create table if not exists public.materiais (
  id uuid primary key default gen_random_uuid(),
  obra_id uuid not null references public.obras(id) on delete cascade,
  nome text not null,
  unidade text not null,
  quantidade_prevista numeric(14,3) check (quantidade_prevista >= 0),
  quantidade_real numeric(14,3) check (quantidade_real >= 0),
  quantidade_consumida numeric(14,3) not null default 0 check (quantidade_consumida >= 0),
  custo_unitario numeric(14,2) check (custo_unitario >= 0),
  fornecedor_id uuid references public.fornecedores(id) on delete set null,
  data_entrada date,
  data_vencimento date,
  lote text,
  localizacao text,
  status text not null default 'disponivel' check (status in ('disponivel','em_uso','esgotado','vencido')),
  source_import_job_id uuid references public.import_jobs(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  updated_by uuid,
  version integer not null default 1 check (version > 0)
);

create table if not exists public.equipes (
  id uuid primary key default gen_random_uuid(),
  obra_id uuid not null references public.obras(id) on delete cascade,
  nome text not null,
  encarregado text,
  membros integer not null default 0 check (membros >= 0),
  especialidade text,
  ativa boolean not null default true,
  source_import_job_id uuid references public.import_jobs(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  updated_by uuid,
  version integer not null default 1 check (version > 0)
);

create table if not exists public.ocorrencias (
  id uuid primary key default gen_random_uuid(),
  obra_id uuid not null references public.obras(id) on delete cascade,
  atividade_id uuid references public.atividades(id) on delete set null,
  tipo text not null check (tipo in ('acidente','nao_conformidade','atraso','retrabalho','problema_qualidade','outro')),
  descricao text not null,
  gravidade text not null check (gravidade in ('baixa','media','alta','critica')),
  evidencias_ids uuid[] not null default '{}',
  resolvida boolean not null default false,
  resolvida_em timestamptz,
  resolvida_por uuid,
  solucao text,
  causa_raiz text,
  source_import_job_id uuid references public.import_jobs(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  updated_by uuid,
  version integer not null default 1 check (version > 0),
  check ((resolvida = false) or (resolvida_em is not null and char_length(trim(coalesce(solucao, ''))) > 0))
);

create table if not exists public.checklists (
  id uuid primary key default gen_random_uuid(),
  obra_id uuid references public.obras(id) on delete cascade,
  atividade_id uuid references public.atividades(id) on delete set null,
  template_nome text not null,
  template_version text not null default '1.0',
  itens jsonb not null check (jsonb_typeof(itens) = 'array'),
  preenchido_por uuid,
  preenchido_at timestamptz not null default now(),
  assinatura_hash text check (assinatura_hash is null or assinatura_hash ~ '^[0-9a-f]{64}$'),
  aprovado_por uuid,
  aprovado_at timestamptz,
  observacao text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  updated_by uuid,
  version integer not null default 1 check (version > 0),
  check (obra_id is not null or atividade_id is not null)
);

create index if not exists idx_atividades_obra_status on public.atividades(obra_id, status) where deleted_at is null;
create index if not exists idx_cronograma_obra on public.cronograma(obra_id);
create index if not exists idx_ico_obra_data on public.ico_registros(obra_id, data_referencia desc);
create index if not exists idx_evidencias_obra on public.evidencias(obra_id) where deleted_at is null;
create index if not exists idx_ecos_obra_status on public.ecos(obra_id, status);
create index if not exists idx_materiais_obra on public.materiais(obra_id);
create index if not exists idx_equipes_obra on public.equipes(obra_id) where ativa;
create index if not exists idx_ocorrencias_obra on public.ocorrencias(obra_id) where not resolvida;
create index if not exists idx_checklists_obra on public.checklists(obra_id);

do $$
declare v_table text;
begin
  foreach v_table in array array['atividades','cronograma','ico_registros','evidencias','ecos','materiais','equipes','ocorrencias','checklists'] loop
    execute format('drop trigger if exists opera_audit_trigger on public.%I', v_table);
    execute format('create trigger opera_audit_trigger after insert or update or delete on public.%I for each row execute function public.opera_audit_row()', v_table);
    execute format('alter table public.%I enable row level security', v_table);
    execute format('revoke all on public.%I from anon, authenticated', v_table);
  end loop;
end;
$$;

grant select, insert, update, delete on public.atividades, public.cronograma, public.ico_registros,
  public.evidencias, public.ecos, public.materiais, public.equipes, public.ocorrencias, public.checklists to service_role;
