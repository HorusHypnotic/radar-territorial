-- Gerado por scripts/build_migration_bundle.py
begin;

-- >>> 000_core_schema.sql
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

-- >>> 001_audit_log.sql
-- OPERA Territorial — fundamento auditável (GAP-01, GAP-07 e GAP-08)
create extension if not exists pgcrypto;

create table if not exists public.audit_log (
  id uuid primary key default gen_random_uuid(),
  table_name text not null,
  row_id uuid not null,
  op text not null check (op in ('INSERT', 'UPDATE', 'DELETE')),
  actor_id uuid,
  at timestamptz not null default now(),
  old_row jsonb,
  new_row jsonb,
  prev_hash text,
  curr_hash text not null
);

create index if not exists audit_log_table_row_idx on public.audit_log (table_name, row_id, at desc);
alter table public.audit_log enable row level security;

create or replace function public.opera_audit_row()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  previous_hash text;
  current_row jsonb;
  current_row_id uuid;
  event_at timestamptz := clock_timestamp();
  actor uuid := auth.uid();
begin
  current_row := case when tg_op = 'DELETE' then to_jsonb(old) else to_jsonb(new) end;
  current_row_id := (current_row ->> 'id')::uuid;

  select curr_hash into previous_hash
  from public.audit_log
  order by at desc, id desc
  limit 1
  for update;

  insert into public.audit_log (table_name, row_id, op, actor_id, at, old_row, new_row, prev_hash, curr_hash)
  values (
    tg_table_name,
    current_row_id,
    tg_op,
    actor,
    event_at,
    case when tg_op in ('UPDATE', 'DELETE') then to_jsonb(old) end,
    case when tg_op in ('INSERT', 'UPDATE') then to_jsonb(new) end,
    previous_hash,
    encode(digest(coalesce(previous_hash, '') || coalesce(current_row::text, '') || event_at::text || coalesce(actor::text, ''), 'sha256'), 'hex')
  );
  return case when tg_op = 'DELETE' then old else new end;
end;
$$;

revoke all on public.audit_log from anon, authenticated;
revoke all on function public.opera_audit_row() from public;

-- Aplique depois de confirmar que as tabelas existem:
-- create trigger zonas_audit after insert or update or delete on public.zonas for each row execute function public.opera_audit_row();
-- create trigger obras_audit after insert or update or delete on public.obras for each row execute function public.opera_audit_row();
-- create trigger fornecedores_audit after insert or update or delete on public.fornecedores for each row execute function public.opera_audit_row();

-- >>> 002_audit_trigger.sql
-- GAP-01 — auditoria automática com cadeia por entidade.
create extension if not exists pgcrypto;

create or replace function public.opera_audit_row()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_old jsonb := case when tg_op in ('UPDATE', 'DELETE') then to_jsonb(old) end;
  v_new jsonb := case when tg_op in ('INSERT', 'UPDATE') then to_jsonb(new) end;
  v_row jsonb := coalesce(v_new, v_old);
  v_row_id uuid;
  v_actor uuid;
  v_at timestamptz := clock_timestamp();
  v_prev_hash text;
  v_curr_hash text;
begin
  v_row_id := nullif(v_row ->> 'id', '')::uuid;
  if v_row_id is null then
    raise exception 'Tabela %.% não possui id UUID auditável', tg_table_schema, tg_table_name;
  end if;

  v_actor := coalesce(
    auth.uid(),
    nullif(current_setting('app.current_user_id', true), '')::uuid,
    nullif(current_setting('app.service_user_id', true), '')::uuid
  );
  perform pg_advisory_xact_lock(hashtextextended(tg_table_name || ':' || v_row_id::text, 0));
  select curr_hash into v_prev_hash
    from public.audit_log
   where table_name = tg_table_name and row_id = v_row_id
   order by at desc, id desc limit 1;

  v_curr_hash := encode(digest(convert_to(
    coalesce(v_prev_hash, '') || '|' || coalesce(v_new::text, '') || '|' ||
    coalesce(v_old::text, '') || '|' || tg_op || '|' || coalesce(v_actor::text, '') || '|' || v_at::text,
    'UTF8'), 'sha256'), 'hex');

  insert into public.audit_log(table_name, row_id, op, actor_id, at, old_row, new_row, prev_hash, curr_hash)
  values (tg_table_name, v_row_id, tg_op, v_actor, v_at, v_old, v_new, v_prev_hash, v_curr_hash);
  return case when tg_op = 'DELETE' then old else new end;
end;
$$;

create or replace function public.verify_hash_chain(p_table_name text, p_row_id uuid)
returns table(position bigint, operation text, event_at timestamptz, stored_hash text, computed_hash text, is_valid boolean)
language sql
security definer
set search_path = public, pg_temp
as $$
  with ordered as (
    select a.*,
           row_number() over (order by a.at, a.id) as position,
           lag(a.curr_hash) over (order by a.at, a.id) as expected_prev
      from public.audit_log a
     where a.table_name = p_table_name and a.row_id = p_row_id
  ), checked as (
    select o.*,
           encode(digest(convert_to(
             coalesce(o.expected_prev, '') || '|' || coalesce(o.new_row::text, '') || '|' ||
             coalesce(o.old_row::text, '') || '|' || o.op || '|' || coalesce(o.actor_id::text, '') || '|' || o.at::text,
             'UTF8'), 'sha256'), 'hex') as recomputed
      from ordered o
  )
  select position, op, at, curr_hash, recomputed,
         curr_hash = recomputed and prev_hash is not distinct from expected_prev
    from checked order by position;
$$;

do $$
declare
  v_table text;
begin
  foreach v_table in array array['zonas','obras','fornecedores','atividades','cronograma','materiais','equipes','ocorrencias','ecos'] loop
    if to_regclass('public.' || v_table) is not null then
      execute format('drop trigger if exists opera_audit_trigger on public.%I', v_table);
      execute format('create trigger opera_audit_trigger after insert or update or delete on public.%I for each row execute function public.opera_audit_row()', v_table);
    end if;
  end loop;
end;
$$;

revoke all on function public.verify_hash_chain(text, uuid) from public;
grant execute on function public.verify_hash_chain(text, uuid) to authenticated;
grant execute on function public.verify_hash_chain(text, uuid) to service_role;

-- >>> 003_versioning.sql
-- GAP-02, GAP-05 e GAP-07 — versões append-only e retificação justificada.
do $$
declare v_table text;
begin
  foreach v_table in array array['zonas','obras','fornecedores','atividades','cronograma','materiais','equipes','ocorrencias','ecos'] loop
    if to_regclass('public.' || v_table) is not null then
      execute format('alter table public.%I add column if not exists version integer not null default 1', v_table);
      execute format('alter table public.%I add column if not exists updated_at timestamptz not null default now()', v_table);
      execute format('alter table public.%I add column if not exists updated_by uuid', v_table);
      execute format('alter table public.%I add column if not exists source_import_job_id uuid', v_table);
      if to_regclass('public.import_jobs') is not null and not exists (
        select 1 from pg_constraint where conname = v_table || '_source_import_job_id_fkey'
      ) then
        execute format('alter table public.%I add constraint %I foreign key (source_import_job_id) references public.import_jobs(id)', v_table, v_table || '_source_import_job_id_fkey');
      end if;
    end if;
  end loop;
end;
$$;

create table if not exists public.version_metadata (
  id uuid primary key default gen_random_uuid(),
  entity_type text not null,
  entity_id uuid not null,
  version integer not null check (version > 0),
  snapshot jsonb not null,
  reason text not null check (char_length(trim(reason)) >= 20),
  edited_by uuid,
  edited_at timestamptz not null default now(),
  approved_by uuid,
  approved_at timestamptz,
  valid_from timestamptz not null,
  valid_to timestamptz,
  prev_version_id uuid references public.version_metadata(id),
  prev_hash text,
  curr_hash text not null,
  unique(entity_type, entity_id, version),
  check (valid_to is null or valid_to >= valid_from)
);
create unique index if not exists version_metadata_current_idx
  on public.version_metadata(entity_type, entity_id) where valid_to is null;
alter table public.version_metadata enable row level security;

create or replace function public.create_new_version(
  p_entity_type text, p_entity_id uuid, p_snapshot jsonb, p_reason text,
  p_edited_by uuid default null, p_approved_by uuid default null
) returns uuid
language plpgsql security definer set search_path = public, pg_temp
as $$
declare
  v_id uuid;
  v_version integer := 1;
  v_prev_id uuid;
  v_prev_hash text;
  v_at timestamptz := clock_timestamp();
  v_hash text;
begin
  if p_entity_type not in ('zonas','obras','fornecedores','atividades','cronograma','materiais','equipes','ocorrencias','ecos') then
    raise exception 'Tipo de entidade não permitido';
  end if;
  if char_length(trim(coalesce(p_reason, ''))) < 20 then raise exception 'Motivo deve ter pelo menos 20 caracteres'; end if;
  if p_snapshot is null or jsonb_typeof(p_snapshot) <> 'object' then raise exception 'Snapshot deve ser um objeto JSON'; end if;
  perform pg_advisory_xact_lock(hashtextextended(p_entity_type || ':' || p_entity_id::text, 1));
  select id, version, curr_hash into v_prev_id, v_version, v_prev_hash
    from public.version_metadata where entity_type = p_entity_type and entity_id = p_entity_id and valid_to is null
    order by version desc limit 1 for update;
  if v_prev_id is null then v_version := 1; else v_version := v_version + 1; end if;
  v_hash := encode(digest(convert_to(coalesce(v_prev_hash, '') || '|' || p_snapshot::text || '|' || trim(p_reason) || '|' || coalesce(p_edited_by::text, '') || '|' || v_at::text, 'UTF8'), 'sha256'), 'hex');
  if v_prev_id is not null then update public.version_metadata set valid_to = v_at where id = v_prev_id; end if;
  insert into public.version_metadata(entity_type, entity_id, version, snapshot, reason, edited_by, edited_at, approved_by, approved_at, valid_from, prev_version_id, prev_hash, curr_hash)
  values (p_entity_type, p_entity_id, v_version, p_snapshot, trim(p_reason), p_edited_by, v_at, p_approved_by, case when p_approved_by is null then null else v_at end, v_at, v_prev_id, v_prev_hash, v_hash)
  returning id into v_id;
  return v_id;
end;
$$;

create or replace function public.retify_entity(p_entity_type text, p_entity_id uuid, p_updates jsonb, p_reason text, p_edited_by uuid default null, p_expected_version integer default null)
returns uuid language plpgsql security definer set search_path = public, pg_temp
as $$
declare
  v_current jsonb;
  v_snapshot jsonb;
  v_version_id uuid;
  v_set text;
  v_key text;
begin
  if p_entity_type not in ('zonas','obras','fornecedores','atividades','cronograma','materiais','equipes','ocorrencias','ecos') then raise exception 'Tipo de entidade não permitido'; end if;
  if to_regclass('public.' || p_entity_type) is null then raise exception 'Tabela não encontrada'; end if;
  if char_length(trim(coalesce(p_reason, ''))) < 20 then raise exception 'Motivo deve ter pelo menos 20 caracteres'; end if;
  if p_updates is null or jsonb_typeof(p_updates) <> 'object' or p_updates ?| array['id','created_at','created_by','version'] then raise exception 'Atualizações inválidas ou contêm campos protegidos'; end if;
  perform pg_advisory_xact_lock(hashtextextended(p_entity_type || ':' || p_entity_id::text, 1));
  execute format('select to_jsonb(t) from public.%I t where id = $1 for update', p_entity_type) into v_current using p_entity_id;
  if v_current is null then raise exception 'Entidade não encontrada'; end if;
  if p_expected_version is not null and coalesce((v_current ->> 'version')::integer, 1) <> p_expected_version then
    raise exception 'Conflito de versão: esperado %, atual %', p_expected_version, coalesce((v_current ->> 'version')::integer, 1) using errcode = '40001';
  end if;
  v_snapshot := v_current || p_updates;
  v_version_id := public.create_new_version(p_entity_type, p_entity_id, v_snapshot, p_reason, p_edited_by);
  for v_key in select jsonb_object_keys(p_updates) loop
    if exists(select 1 from pg_attribute where attrelid = to_regclass('public.' || p_entity_type) and attname = v_key and attnum > 0 and not attisdropped) then
      v_set := concat_ws(', ', v_set, format('%I = (jsonb_populate_record(null::public.%I, $1)).%I', v_key, p_entity_type, v_key));
    end if;
  end loop;
  if v_set is null then raise exception 'Nenhuma coluna atualizável encontrada'; end if;
  if exists(select 1 from pg_attribute where attrelid = to_regclass('public.' || p_entity_type) and attname = 'version' and attnum > 0 and not attisdropped) then v_set := v_set || ', version = version + 1'; end if;
  if exists(select 1 from pg_attribute where attrelid = to_regclass('public.' || p_entity_type) and attname = 'updated_at' and attnum > 0 and not attisdropped) then v_set := v_set || ', updated_at = now()'; end if;
  execute format('update public.%I set %s where id = $2', p_entity_type, v_set) using p_updates, p_entity_id;
  return v_version_id;
end;
$$;

create or replace function public.verify_version_chain(p_entity_type text, p_entity_id uuid)
returns table(position bigint, stored_hash text, computed_hash text, is_valid boolean)
language sql security definer set search_path = public, pg_temp
as $$
  with ordered as (
    select v.*, row_number() over(order by version) as position,
           lag(curr_hash) over(order by version) as expected_prev
      from public.version_metadata v where entity_type = p_entity_type and entity_id = p_entity_id
  ), checked as (
    select o.*, encode(digest(convert_to(coalesce(expected_prev, '') || '|' || snapshot::text || '|' || reason || '|' || coalesce(edited_by::text, '') || '|' || edited_at::text, 'UTF8'), 'sha256'), 'hex') as recomputed
      from ordered o
  )
  select position, curr_hash, recomputed, curr_hash = recomputed and prev_hash is not distinct from expected_prev
    from checked order by position;
$$;

revoke all on public.version_metadata from anon, authenticated;
revoke all on function public.create_new_version(text,uuid,jsonb,text,uuid,uuid) from public;
revoke all on function public.retify_entity(text,uuid,jsonb,text,uuid,integer) from public;
revoke all on function public.verify_version_chain(text,uuid) from public;
grant execute on function public.retify_entity(text,uuid,jsonb,text,uuid,integer) to authenticated;
grant execute on function public.verify_version_chain(text,uuid) to authenticated;
grant execute on function public.create_new_version(text,uuid,jsonb,text,uuid,uuid) to service_role;
grant execute on function public.retify_entity(text,uuid,jsonb,text,uuid,integer) to service_role;
grant execute on function public.verify_version_chain(text,uuid) to service_role;

-- >>> 004_snapshot_eov.sql
-- GAP-04 — Estado Operacional Verificável diário por obra.
create table if not exists public.snapshot_operacional (
  id uuid primary key default gen_random_uuid(),
  obra_id uuid not null,
  snapshot_date date not null,
  payload jsonb not null,
  prev_hash text,
  curr_hash text not null,
  gerado_at timestamptz not null default now(),
  gerado_por uuid,
  schema_version text not null default '1.0',
  unique(obra_id, snapshot_date)
);
alter table public.snapshot_operacional enable row level security;

do $$
begin
  if to_regclass('public.obras') is not null and not exists (
    select 1 from pg_constraint where conname = 'snapshot_operacional_obra_id_fkey'
  ) then
    alter table public.snapshot_operacional add constraint snapshot_operacional_obra_id_fkey foreign key (obra_id) references public.obras(id);
  end if;
end;
$$;

create or replace function public.opera_related_rows(p_table text, p_obra_id uuid)
returns jsonb language plpgsql stable security definer set search_path = public, pg_temp
as $$
declare v_result jsonb;
begin
  if p_table not in ('atividades','cronograma','materiais','equipes','ocorrencias','ico_registros') or to_regclass('public.' || p_table) is null then return '[]'::jsonb; end if;
  execute format('select coalesce(jsonb_agg(to_jsonb(t) order by t.id), ''[]''::jsonb) from public.%I t where obra_id = $1', p_table) into v_result using p_obra_id;
  return coalesce(v_result, '[]'::jsonb);
end;
$$;

create or replace function public.generate_obra_snapshot(p_obra_id uuid, p_snapshot_date date default current_date, p_gerado_por uuid default null)
returns uuid language plpgsql security definer set search_path = public, pg_temp
as $$
declare
  v_obra jsonb;
  v_payload jsonb;
  v_prev_hash text;
  v_hash text;
  v_id uuid;
  v_at timestamptz := clock_timestamp();
begin
  if to_regclass('public.obras') is null then raise exception 'Tabela obras não encontrada'; end if;
  perform pg_advisory_xact_lock(hashtextextended('snapshot:' || p_obra_id::text, 2));
  execute 'select to_jsonb(o) from public.obras o where id = $1' into v_obra using p_obra_id;
  if v_obra is null then raise exception 'Obra não encontrada'; end if;
  v_payload := jsonb_build_object(
    'obra', v_obra,
    'atividades', public.opera_related_rows('atividades', p_obra_id),
    'cronograma', public.opera_related_rows('cronograma', p_obra_id),
    'materiais', public.opera_related_rows('materiais', p_obra_id),
    'equipes', public.opera_related_rows('equipes', p_obra_id),
    'ocorrencias', public.opera_related_rows('ocorrencias', p_obra_id),
    'ico_registros', public.opera_related_rows('ico_registros', p_obra_id),
    'metadata', jsonb_build_object('gerado_em', v_at, 'snapshot_date', p_snapshot_date, 'schema_version', '1.0')
  );
  select curr_hash into v_prev_hash from public.snapshot_operacional where obra_id = p_obra_id and snapshot_date < p_snapshot_date order by snapshot_date desc limit 1;
  v_hash := encode(digest(convert_to(coalesce(v_prev_hash, '') || '|' || v_payload::text || '|' || p_snapshot_date::text || '|' || coalesce(p_gerado_por::text, ''), 'UTF8'), 'sha256'), 'hex');
  insert into public.snapshot_operacional(obra_id, snapshot_date, payload, prev_hash, curr_hash, gerado_at, gerado_por)
  values (p_obra_id, p_snapshot_date, v_payload, v_prev_hash, v_hash, v_at, p_gerado_por)
  on conflict (obra_id, snapshot_date) do nothing returning id into v_id;
  if v_id is null then raise exception 'Snapshot já existe para esta obra e data'; end if;
  return v_id;
end;
$$;

create or replace function public.generate_daily_snapshots()
returns integer language plpgsql security definer set search_path = public, pg_temp
as $$
declare v_obra record; v_count integer := 0;
begin
  if to_regclass('public.obras') is null then return 0; end if;
  for v_obra in execute 'select id from public.obras where lower(coalesce(status, '''')) not in (''concluida'',''concluído'',''concluido'')' loop
    begin perform public.generate_obra_snapshot(v_obra.id, current_date, null); v_count := v_count + 1;
    exception when unique_violation or raise_exception then null;
    end;
  end loop;
  return v_count;
end;
$$;

-- Restauração não apaga história: retifica a obra a partir do payload preservado.
create or replace function public.restore_snapshot(p_snapshot_id uuid, p_reason text, p_restored_by uuid default null)
returns uuid language plpgsql security definer set search_path = public, pg_temp
as $$
declare v_snapshot public.snapshot_operacional%rowtype; v_updates jsonb;
begin
  if char_length(trim(coalesce(p_reason, ''))) < 20 then raise exception 'Motivo deve ter pelo menos 20 caracteres'; end if;
  select * into v_snapshot from public.snapshot_operacional where id = p_snapshot_id;
  if not found then raise exception 'Snapshot não encontrado'; end if;
  v_updates := (v_snapshot.payload -> 'obra') - array['id','created_at','created_by','version'];
  return public.retify_entity('obras', v_snapshot.obra_id, v_updates, p_reason, p_restored_by, null);
end;
$$;

create or replace function public.verify_snapshot_chain(p_obra_id uuid)
returns table(position bigint, stored_hash text, computed_hash text, is_valid boolean)
language sql security definer set search_path = public, pg_temp
as $$
  with ordered as (
    select s.*, row_number() over(order by snapshot_date, id) as position,
           lag(curr_hash) over(order by snapshot_date, id) as expected_prev
      from public.snapshot_operacional s where obra_id = p_obra_id
  ), checked as (
    select o.*, encode(digest(convert_to(coalesce(expected_prev, '') || '|' || payload::text || '|' || snapshot_date::text || '|' || coalesce(gerado_por::text, ''), 'UTF8'), 'sha256'), 'hex') as recomputed
      from ordered o
  )
  select position, curr_hash, recomputed, curr_hash = recomputed and prev_hash is not distinct from expected_prev
    from checked order by position;
$$;

revoke all on public.snapshot_operacional from anon, authenticated;
revoke all on function public.generate_obra_snapshot(uuid,date,uuid) from public;
revoke all on function public.generate_daily_snapshots() from public;
revoke all on function public.restore_snapshot(uuid,text,uuid) from public;
revoke all on function public.verify_snapshot_chain(uuid) from public;
grant execute on function public.verify_snapshot_chain(uuid) to authenticated;
grant execute on function public.generate_obra_snapshot(uuid,date,uuid) to service_role;
grant execute on function public.generate_daily_snapshots() to service_role;
grant execute on function public.restore_snapshot(uuid,text,uuid) to service_role;
grant execute on function public.verify_snapshot_chain(uuid) to service_role;

-- >>> 005_entidades_apmo.sql
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

commit;
