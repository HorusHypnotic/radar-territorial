from scripts.check_supabase import credentials_error


def test_credentials_are_required():
    assert "obrigatórios" in credentials_error(None, None)


def test_placeholders_are_rejected():
    assert "placeholders" in credentials_error(
        "https://seu-projeto.supabase.co", "sua-service-key"
    )


def test_non_supabase_url_is_rejected():
    assert "supabase.co" in credentials_error("https://example.com", "secret")


def test_valid_shape_is_accepted_without_exposing_key():
    assert credentials_error("https://abc123.supabase.co", "secret") is None
