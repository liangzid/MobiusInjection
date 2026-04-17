#!/bin/bash
# Master Setup Script for All Agent Containers
# Location: /home/zi/paper_mobius/scripts/setup/setup_all.sh
# Usage: ./setup_all.sh [env_file]
#   env_file: Path to .env file (defaults to .env in setup directory)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${1:-$SCRIPT_DIR/.env}"

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: Environment file not found: $ENV_FILE"
    echo "Please copy .env.example to .env and fill in your API keys"
    exit 1
fi

echo "Loading environment from: $ENV_FILE"
source "$ENV_FILE"

AGENTS=(
    "claude_code:01_claude_code.sh"
    "openclaw:02_openclaw.sh"
    "opencode:03_opencode.sh"
    "codex:04_codex.sh"
    "kilo_code:05_kilo_code.sh"
    "grok_cli:06_grok_cli.sh"
    "zeroclaw:07_zeroclaw.sh"
    "hermes:08_hermes.sh"
    "nanobot:09_nanobot.sh"
    "droid:10_droid.sh"
    "zed:11_zed.sh"
)

echo "=========================================="
echo "Setting up all agent containers"
echo "=========================================="

for entry in "${AGENTS[@]}"; do
    container="${entry%%:*}"
    script="${entry##*:}"
    script_path="$SCRIPT_DIR/$script"

    echo ""
    echo "--- Setting up $container ---"

    if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        echo "Warning: Container $container is not running. Skipping."
        continue
    fi

    echo "Copying setup script to $container..."
    docker cp "$script_path" "${container}:/tmp/setup_agent.sh"

    echo "Running setup script in $container..."
    docker exec "$container" bash /tmp/setup_agent.sh

    echo "Cleaning up temporary script..."
    docker exec "$container" rm -f /tmp/setup_agent.sh

    echo "Done: $container"
done

echo ""
echo "=========================================="
echo "All agents configured!"
echo "=========================================="
echo ""
echo "To use an agent, exec into its container:"
echo "  docker exec -it <container> bash"
echo ""
echo "Then load the environment:"
echo "  source ~/.bashrc  # or source ~/.profile for alpine-based containers"