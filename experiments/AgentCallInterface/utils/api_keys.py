"""API Key Management Utility

Reads API keys from privacy_*.txt files in the project root.
This keeps sensitive credentials out of source code.
"""

from pathlib import Path
from functools import lru_cache
import os

# Project root is AgentCodingDos (parent of experiments/AgentCallInterface)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.absolute()
PRIVACY_DIR = PROJECT_ROOT / "privacy_secret_openrouter_API_key.txt"
PRIVACY_AIGOCODE_DIR = PROJECT_ROOT / "privacy_secret_aigocode_API_key.txt"
PRIVACY_AIGOCODE_PROVIDER_FILES = {
    "anthropic": PROJECT_ROOT / "privacy_secret_aigocode_anthropic_API_key.txt",
    "openai": PROJECT_ROOT / "privacy_secret_aigocode_openai_API_key.txt",
    "gemini": PROJECT_ROOT / "privacy_secret_aigocode_gemini_API_key.txt",
}
OPENROUTER_API_KEY_FILE_ENV = "OPENROUTER_API_KEY_FILE"
OPENROUTER_API_KEY_ENV = "OPENROUTER_API_KEY"
AIGOCODE_API_KEY_FILE_ENV = "AIGOCODE_API_KEY_FILE"
AIGOCODE_API_KEY_ENV = "AIGOCODE_API_KEY"
AIGOCODE_BASE_URL_ENV = "AIGOCODE_BASE_URL"


@lru_cache(maxsize=1)
def get_openrouter_api_key() -> str:
    """Read OpenRouter API key from env or privacy file.

    Returns:
        str: The OpenRouter API key

    Raises:
        FileNotFoundError: If the privacy file doesn't exist
        ValueError: If the key file is empty
    """
    env_key = os.environ.get(OPENROUTER_API_KEY_ENV, "").strip()
    if env_key:
        return env_key

    key_path = Path(os.environ.get(OPENROUTER_API_KEY_FILE_ENV, PRIVACY_DIR))
    if not key_path.exists():
        raise FileNotFoundError(
            f"OpenRouter API key file not found at {key_path}. "
            "Please create privacy_secret_openrouter_API_key.txt in the project root, "
            f"set {OPENROUTER_API_KEY_FILE_ENV}, or set {OPENROUTER_API_KEY_ENV}."
        )

    api_key = key_path.read_text().strip()
    if not api_key:
        raise ValueError(f"OpenRouter API key file at {key_path} is empty.")

    return api_key


@lru_cache(maxsize=1)
def get_openrouter_base_url() -> str:
    """Get the OpenRouter API base URL."""
    return "https://openrouter.ai/api/v1"


@lru_cache(maxsize=1)
def get_aigocode_api_key() -> str:
    """Read AiGoCode API key from env or privacy file."""
    env_key = os.environ.get(AIGOCODE_API_KEY_ENV, "").strip()
    if env_key:
        return env_key

    key_path = Path(os.environ.get(AIGOCODE_API_KEY_FILE_ENV, PRIVACY_AIGOCODE_DIR))
    if not key_path.exists():
        raise FileNotFoundError(
            f"AiGoCode API key file not found at {key_path}. "
            "Please create privacy_secret_aigocode_API_key.txt in the project root, "
            f"set {AIGOCODE_API_KEY_FILE_ENV}, or set {AIGOCODE_API_KEY_ENV}."
        )

    api_key = key_path.read_text().strip()
    if not api_key:
        raise ValueError(f"AiGoCode API key file at {key_path} is empty.")

    return api_key


@lru_cache(maxsize=None)
def get_aigocode_provider_api_key(provider: str) -> str:
    """Read an AiGoCode API key for a specific provider family."""
    normalized = provider.strip().lower()
    if normalized not in PRIVACY_AIGOCODE_PROVIDER_FILES:
        raise ValueError(f"Unsupported AiGoCode provider: {provider}")

    env_key = os.environ.get(f"AIGOCODE_{normalized.upper()}_API_KEY", "").strip()
    if env_key:
        return env_key

    file_env = f"AIGOCODE_{normalized.upper()}_API_KEY_FILE"
    key_path = Path(os.environ.get(file_env, PRIVACY_AIGOCODE_PROVIDER_FILES[normalized]))
    if key_path.exists():
        api_key = key_path.read_text().strip()
        if not api_key:
            raise ValueError(f"AiGoCode {normalized} API key file at {key_path} is empty.")
        return api_key

    return get_aigocode_api_key()


@lru_cache(maxsize=1)
def get_aigocode_base_url() -> str:
    """Get the AiGoCode API root URL."""
    return os.environ.get(AIGOCODE_BASE_URL_ENV, "https://api.aigocode.com").rstrip("/")


if __name__ == "__main__":
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Privacy file: {PRIVACY_DIR}")
    print(f"API key found: {bool(PRIVACY_DIR.exists())}")
    if PRIVACY_DIR.exists():
        key = get_openrouter_api_key()
        print(f"API key (first 20 chars): {key[:20]}...")
