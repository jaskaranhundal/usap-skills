#!/usr/bin/env bash
# install.sh — Install USAP AnythingLLM skill plugins
# Run from anythingllm-package/ directory

set -euo pipefail

# Detect storage path
if [[ -n "${ANYTHINGLLM_STORAGE:-}" ]]; then
  STORAGE="$ANYTHINGLLM_STORAGE"
elif [[ "$(uname)" == "Darwin" ]]; then
  STORAGE="$HOME/Library/Application Support/anythingllm-desktop/storage"
elif [[ -d "/app/server/storage" ]]; then
  STORAGE="/app/server/storage"
else
  STORAGE="$HOME/.config/anythingllm/storage"
fi

SKILLS_DIR="$STORAGE/plugins/agent-skills"

echo "Installing USAP skills to: $SKILLS_DIR"
mkdir -p "$SKILLS_DIR"

# Copy all usap-* skill folders
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COUNT=0
for skill_dir in "$SCRIPT_DIR/skills"/usap-*/; do
  skill_name=$(basename "$skill_dir")
  cp -r "$skill_dir" "$SKILLS_DIR/$skill_name"
  COUNT=$((COUNT + 1))
done

echo "Installed $COUNT skills."
echo ""
echo "Next steps:"
echo "  1. Reload the AnythingLLM browser tab (or restart the app)"
echo "  2. In Agent Skills settings, configure USAP_REPO_PATH for each skill"
echo "  3. Run: python3 setup_workspaces.py --api-key <key> --url http://localhost:3001"
