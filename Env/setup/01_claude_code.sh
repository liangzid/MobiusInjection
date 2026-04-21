#!/bin/bash
# Claude Code Container Setup Script
# Location: /home/zi/paper_mobius/scripts/setup/01_claude_code.sh

set -euo pipefail

eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv bash)"

CLAUDE_USER="${CLAUDE_USER:-zi}"
CLAUDE_HOME="${CLAUDE_HOME:-/home/${CLAUDE_USER}}"
ANTHROPIC_BASE_URL="${ANTHROPIC_BASE_URL:-https://openrouter.ai/api}"
OPENROUTER_BASE_URL="${OPENROUTER_BASE_URL:-https://openrouter.ai/api}"

if [ "$(id -u)" -ne 0 ]; then
    echo "Claude Code setup must run as root so it can prepare ${CLAUDE_USER}." >&2
    exit 1
fi

if ! id -u "$CLAUDE_USER" >/dev/null 2>&1; then
    useradd -m -s /bin/bash "$CLAUDE_USER"
fi

mkdir -p "$CLAUDE_HOME/.claude" "$CLAUDE_HOME/.cache" "$CLAUDE_HOME/.config"

if ! grep -q "Claude Code API Configuration" "$CLAUDE_HOME/.bashrc" 2>/dev/null; then
    cat >> "$CLAUDE_HOME/.bashrc" <<SETUP_EOF
# Claude Code API Configuration
export ANTHROPIC_BASE_URL="${ANTHROPIC_BASE_URL}"
export OPENROUTER_BASE_URL="${OPENROUTER_BASE_URL}"
SETUP_EOF
fi

cat > "$CLAUDE_HOME/.claude/settings.json" <<SETUP_EOF
{
  "env": {
    "ANTHROPIC_BASE_URL": "${ANTHROPIC_BASE_URL}",
    "OPENROUTER_BASE_URL": "${OPENROUTER_BASE_URL}"
  }
}
SETUP_EOF

chown -R "$CLAUDE_USER:$CLAUDE_USER" "$CLAUDE_HOME"

echo "Claude Code configured for ${CLAUDE_USER}. Run with: docker exec -u ${CLAUDE_USER} -e HOME=${CLAUDE_HOME} claude_code ..."
