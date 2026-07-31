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
