from scripts.build_migration_bundle import build_bundle, migration_paths


def test_migrations_are_complete_and_ordered():
    assert [path.name[:3] for path in migration_paths()] == ["000", "001", "002", "003", "004", "005", "006", "007"]


def test_bundle_is_transactional_and_contains_core_dependencies():
    bundle = build_bundle()
    assert bundle.startswith("-- Gerado")
    assert "begin;" in bundle and bundle.rstrip().endswith("commit;")
    assert bundle.index("create table if not exists public.import_jobs") < bundle.index(">>> 005_entidades_apmo.sql")
    assert bundle.index("create table if not exists public.obras") < bundle.index("create table if not exists public.atividades")
