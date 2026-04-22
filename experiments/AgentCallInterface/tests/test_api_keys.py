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
