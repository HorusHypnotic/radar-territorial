-- Fase 4 — preservação verificável, provas externas e registro append-only.
alter table public.evidencias add column if not exists timestamp_rfc3161 jsonb;
alter table public.evidencias add column if not exists timestamp_opentimestamps jsonb;
alter table public.evidencias add column if not exists assinatura_digital jsonb;
alter table public.evidencias add column if not exists preservacao_status text not null default 'hash_local'
  check (preservacao_status in ('hash_local','timestamp_solicitado','timestamp_confirmado','assinado','verificado','falha'));

create table if not exists public.verificacao_integridade (
  id uuid primary key default gen_random_uuid(),
  obra_id uuid references public.obras(id) on delete cascade,
  entidade_tipo text not null,
  entidade_id uuid not null,
  verificado_at timestamptz not null default now(),
  resultado boolean not null,
  detalhes jsonb not null default '{}'::jsonb,
  metodo text not null check (metodo in ('sha256','audit_chain','version_chain','snapshot_chain','evidence_metadata','completo')),
  verificado_por uuid,
  hash_verificado text check (hash_verificado is null or hash_verificado ~ '^[0-9a-f]{64}$')
);

create index if not exists idx_verificacao_obra_data on public.verificacao_integridade(obra_id, verificado_at desc);
create index if not exists idx_verificacao_entidade on public.verificacao_integridade(entidade_tipo, entidade_id, verificado_at desc);
alter table public.verificacao_integridade enable row level security;
revoke all on public.verificacao_integridade from anon, authenticated;
grant select, insert on public.verificacao_integridade to service_role;

create or replace function public.opera_append_only()
returns trigger language plpgsql security definer set search_path = public, pg_temp as $$
begin
  raise exception 'Registros de integridade são append-only';
end;
$$;
drop trigger if exists verificacao_integridade_immutable on public.verificacao_integridade;
create trigger verificacao_integridade_immutable before update or delete on public.verificacao_integridade
for each row execute function public.opera_append_only();

create or replace function public.verificar_integridade_obra(p_obra_id uuid, p_verificado_por uuid default null)
returns jsonb language plpgsql security definer set search_path = public, pg_temp as $$
declare
  v_audit boolean;
  v_snapshot boolean;
  v_version boolean;
  v_evidence boolean;
  v_result boolean;
  v_details jsonb;
begin
  if not exists (select 1 from public.obras where id = p_obra_id) then raise exception 'Obra não encontrada'; end if;
  select coalesce(bool_and(is_valid), true) into v_audit from public.verify_hash_chain('obras', p_obra_id);
  select coalesce(bool_and(is_valid), true) into v_snapshot from public.verify_snapshot_chain(p_obra_id);
  select coalesce(bool_and(is_valid), true) into v_version from public.verify_version_chain('obras', p_obra_id);
  select coalesce(bool_and(hash_sha256 ~ '^[0-9a-f]{64}$' and tamanho_bytes >= 0 and storage_path <> ''), true)
    into v_evidence from public.evidencias where obra_id = p_obra_id and deleted_at is null;
  v_result := v_audit and v_snapshot and v_version and v_evidence;
  v_details := jsonb_build_object('audit_chain',v_audit,'snapshot_chain',v_snapshot,'version_chain',v_version,
    'evidence_metadata',v_evidence,'external_timestamp_verified',false,
    'note','O conteúdo binário deve ser recalculado pelo backend para validação completa.');
  insert into public.verificacao_integridade(obra_id,entidade_tipo,entidade_id,resultado,detalhes,metodo,verificado_por)
  values(p_obra_id,'obras',p_obra_id,v_result,v_details,'completo',p_verificado_por);
  return jsonb_build_object('obra_id',p_obra_id,'valid',v_result,'checks',v_details,'verified_at',clock_timestamp());
end;
$$;

revoke all on function public.verificar_integridade_obra(uuid, uuid) from public;
grant execute on function public.verificar_integridade_obra(uuid, uuid) to service_role;

insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
values('evidencias','evidencias',false,10485760,array['image/jpeg','image/png','video/mp4','audio/mpeg','application/pdf'])
on conflict (id) do update set public=false,file_size_limit=excluded.file_size_limit,allowed_mime_types=excluded.allowed_mime_types;
