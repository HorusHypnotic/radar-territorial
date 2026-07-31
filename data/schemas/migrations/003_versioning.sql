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
