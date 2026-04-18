"""API Key Management Utility

Reads API keys from privacy_*.txt files in the project root.
This keeps sensitive credentials out of source code.
"""

from pathlib import Path
from functools import lru_cache

# Project root is AgentCodingDos (parent of experiments/AgentCallInterface)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.absolute()
PRIVACY_DIR = PROJECT_ROOT / "privacy_secret_openrouter_API_key.txt"


@lru_cache(maxsize=1)
def get_openrouter_api_key() -> str:
    """Read OpenRouter API key from privacy file.

    Returns:
        str: The OpenRouter API key

    Raises:
        FileNotFoundError: If the privacy file doesn't exist
        ValueError: If the key file is empty
    """
    if not PRIVACY_DIR.exists():
        raise FileNotFoundError(
            f"OpenRouter API key file not found at {PRIVACY_DIR}. "
            "Please create privacy_secret_openrouter_API_key.txt in the project root."
        )

    api_key = PRIVACY_DIR.read_text().strip()
    if not api_key:
        raise ValueError(f"OpenRouter API key file at {PRIVACY_DIR} is empty.")

    return api_key


@lru_cache(maxsize=1)
def get_openrouter_base_url() -> str:
    """Get the OpenRouter API base URL."""
    return "https://openrouter.ai/api/v1"


if __name__ == "__main__":
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Privacy file: {PRIVACY_DIR}")
    print(f"API key found: {bool(PRIVACY_DIR.exists())}")
    if PRIVACY_DIR.exists():
        key = get_openrouter_api_key()
        print(f"API key (first 20 chars): {key[:20]}...")
