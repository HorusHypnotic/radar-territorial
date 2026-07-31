-- OPERA Territorial — tabelas-base exigidas pelas migrations 001–005.
create extension if not exists pgcrypto;

create table if not exists public.import_jobs (
  id uuid primary key default gen_random_uuid(),
  origem text not null,
  status text not null default 'recebido' check (status in ('recebido','validado','processado','rejeitado')),
  arquivo_sha256 text check (arquivo_sha256 is null or arquivo_sha256 ~ '^[0-9a-f]{64}$'),
  registros integer not null default 0 check (registros >= 0),
  detalhes jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  completed_at timestamptz
);

create table if not exists public.zonas (
  id uuid primary key default gen_random_uuid(),
  sigla text not null unique check (char_length(trim(sigla)) > 0),
  nome text not null check (char_length(trim(nome)) > 0),
  tipo text,
  categoria text,
  macrozona text,
  nivel text,
  area_km2 numeric(14,4) check (area_km2 is null or area_km2 >= 0),
  to_max numeric(6,2),
  ca_basico numeric(6,2),
  ca_maximo numeric(6,2),
  permeabilidade numeric(6,2),
  altura_max numeric(8,2),
  lotes integer check (lotes is null or lotes >= 0),
  conformidade numeric(5,2) check (conformidade is null or conformidade between 0 and 100),
  source_import_job_id uuid references public.import_jobs(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  updated_by uuid,
  version integer not null default 1 check (version > 0)
);

create table if not exists public.obras (
  id uuid primary key default gen_random_uuid(),
  nome text not null check (char_length(trim(nome)) > 0),
  zona_id uuid references public.zonas(id) on delete set null,
  status text not null default 'planejada',
  ico numeric(5,2) check (ico is null or ico between 0 and 100),
  regiao text,
  descricao text,
  source_import_job_id uuid references public.import_jobs(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  updated_by uuid,
  version integer not null default 1 check (version > 0)
);

create table if not exists public.fornecedores (
  id uuid primary key default gen_random_uuid(),
  nome text not null check (char_length(trim(nome)) > 0),
  ativo boolean not null default true,
  tipo text,
  documento text,
  contato jsonb not null default '{}'::jsonb,
  source_import_job_id uuid references public.import_jobs(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  updated_by uuid,
  version integer not null default 1 check (version > 0)
);

create index if not exists idx_zonas_sigla on public.zonas(sigla);
create index if not exists idx_obras_zona on public.obras(zona_id);
create index if not exists idx_obras_status on public.obras(status);
create index if not exists idx_fornecedores_ativo on public.fornecedores(ativo);

alter table public.import_jobs enable row level security;
alter table public.zonas enable row level security;
alter table public.obras enable row level security;
alter table public.fornecedores enable row level security;

revoke all on public.import_jobs, public.zonas, public.obras, public.fornecedores from anon, authenticated;
grant select, insert, update, delete on public.import_jobs, public.zonas, public.obras, public.fornecedores to service_role;
