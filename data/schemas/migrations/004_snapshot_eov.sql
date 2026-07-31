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
