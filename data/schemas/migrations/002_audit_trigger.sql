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
