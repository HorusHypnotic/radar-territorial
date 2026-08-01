-- Consulta mínima e sem escrita para atividade legítima do projeto Free.
create or replace function public.opera_keep_alive()
returns jsonb
language sql
stable
security definer
set search_path = public, pg_temp
as $$
  select jsonb_build_object(
    'ok', true,
    'checked_at', clock_timestamp(),
    'schema_ready', to_regclass('public.zonas') is not null
  );
$$;

revoke all on function public.opera_keep_alive() from public;
grant execute on function public.opera_keep_alive() to anon, authenticated, service_role;
