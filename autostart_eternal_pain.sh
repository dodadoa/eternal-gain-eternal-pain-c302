#!/usr/bin/env bash

set -euo pipefail

# Autostart wrapper for Raspberry Pi: activates Python env and runs the Eternal Pain loop with GUI
# Configure these as needed or export before calling

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="${VENV_DIR:-$HOME/.venvs/c302}"
PARAM_SET="${PARAM_SET:-A}"
PAIN_DELAY_MS="${PAIN_DELAY_MS:-2000}"
BACKEND="${BACKEND:-jnml}"
TIMEOUT_S="${TIMEOUT_S:-30}"
ENABLE_GUI="${ENABLE_GUI:-1}"   # 1 to enable --gui, 0 to disable
FULLSCREEN="${FULLSCREEN:-1}"    # 1 to enable --fullscreen, 0 to disable
POPUP="${POPUP:-1}"              # 1 to enable --popup, 0 to disable

# Set display for X11 on Raspberry Pi (adjust if using Wayland)
export DISPLAY="${DISPLAY:-:0}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"

# Optional: ensure PATH includes venv bin
if [[ -d "$VENV_DIR" ]]; then
  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate"
else
  echo "[WARN] VENV_DIR not found: $VENV_DIR (continuing without venv)"
fi

cd "$PROJECT_DIR"

ARGS=("$PARAM_SET" "$PAIN_DELAY_MS" "$BACKEND" "--timeout" "$TIMEOUT_S")
if [[ "$ENABLE_GUI" == "1" ]]; then
  ARGS+=("--gui")
  [[ "$FULLSCREEN" == "1" ]] && ARGS+=("--fullscreen")
  [[ "$POPUP" == "1" ]] && ARGS+=("--popup")
fi

LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/eternal_pain_autostart.log"

echo "[INFO] Starting Eternal Pain loop: ${ARGS[*]}" | tee -a "$LOG_FILE"
exec python3 "$PROJECT_DIR/run_eternal_pain_loop.py" "${ARGS[@]}" >> "$LOG_FILE" 2>&1


