from experiments.AgentCallInterface.utils import api_keys


def test_get_openrouter_api_key_prefers_env_value(monkeypatch):
    api_keys.get_openrouter_api_key.cache_clear()
    monkeypatch.setenv("OPENROUTER_API_KEY", "env-key")
    monkeypatch.setenv("OPENROUTER_API_KEY_FILE", "/does/not/matter")

    assert api_keys.get_openrouter_api_key() == "env-key"


def test_get_openrouter_api_key_reads_env_file(monkeypatch, tmp_path):
    api_keys.get_openrouter_api_key.cache_clear()
    key_file = tmp_path / "openrouter_key.txt"
    key_file.write_text("file-key\n")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY_FILE", str(key_file))

    assert api_keys.get_openrouter_api_key() == "file-key"


def test_get_aigocode_api_key_prefers_env_value(monkeypatch):
    api_keys.get_aigocode_api_key.cache_clear()
    monkeypatch.setenv("AIGOCODE_API_KEY", "env-aigocode-key")
    monkeypatch.setenv("AIGOCODE_API_KEY_FILE", "/does/not/matter")

    assert api_keys.get_aigocode_api_key() == "env-aigocode-key"


def test_get_aigocode_api_key_reads_env_file(monkeypatch, tmp_path):
    api_keys.get_aigocode_api_key.cache_clear()
    key_file = tmp_path / "aigocode_key.txt"
    key_file.write_text("file-aigocode-key\n")
    monkeypatch.delenv("AIGOCODE_API_KEY", raising=False)
    monkeypatch.setenv("AIGOCODE_API_KEY_FILE", str(key_file))

    assert api_keys.get_aigocode_api_key() == "file-aigocode-key"


def test_get_aigocode_base_url_uses_env_without_trailing_slash(monkeypatch):
    api_keys.get_aigocode_base_url.cache_clear()
    monkeypatch.setenv("AIGOCODE_BASE_URL", "https://api.example.test/")

    assert api_keys.get_aigocode_base_url() == "https://api.example.test"


def test_get_aigocode_provider_api_key_prefers_provider_env(monkeypatch):
    api_keys.get_aigocode_provider_api_key.cache_clear()
    monkeypatch.setenv("AIGOCODE_OPENAI_API_KEY", "openai-provider-key")
    monkeypatch.setenv("AIGOCODE_API_KEY", "fallback-key")

    assert api_keys.get_aigocode_provider_api_key("openai") == "openai-provider-key"


def test_get_aigocode_provider_api_key_falls_back_to_default(monkeypatch):
    api_keys.get_aigocode_provider_api_key.cache_clear()
    api_keys.get_aigocode_api_key.cache_clear()
    monkeypatch.delenv("AIGOCODE_GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("AIGOCODE_API_KEY", "fallback-key")
    monkeypatch.setenv("AIGOCODE_GEMINI_API_KEY_FILE", "/does/not/exist")

    assert api_keys.get_aigocode_provider_api_key("gemini") == "fallback-key"
