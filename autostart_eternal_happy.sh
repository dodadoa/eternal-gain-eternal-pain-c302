#!/usr/bin/env bash

set -euo pipefail

# Autostart wrapper for Raspberry Pi: activates Python env and runs the Eternal Happiness loop with GUI

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="${VENV_DIR:-$HOME/.venvs/c302}"
PARAM_SET="${PARAM_SET:-A}"
REWARD_DELAY_MS="${REWARD_DELAY_MS:-0}"
BACKEND="${BACKEND:-jnml}"
TIMEOUT_S="${TIMEOUT_S:-30}"

export DISPLAY="${DISPLAY:-:0}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"

if [[ -d "$VENV_DIR" ]]; then
  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate"
else
  echo "[WARN] VENV_DIR not found: $VENV_DIR (continuing without venv)"
fi

cd "$PROJECT_DIR"

ARGS=("$PARAM_SET" "$REWARD_DELAY_MS" "$BACKEND" "--timeout" "$TIMEOUT_S")

LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/eternal_happy_autostart.log"

echo "[INFO] Starting Eternal Happiness loop: ${ARGS[*]}" | tee -a "$LOG_FILE"
exec python3 "$PROJECT_DIR/run_eternal_happy_loop.py" "${ARGS[@]}" >> "$LOG_FILE" 2>&1


