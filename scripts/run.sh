#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." &>/dev/null && pwd)"

VENV_DIR="$BACKEND_DIR/.venv"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

activate_venv() {
  if [ -f "$VENV_DIR/bin/activate" ]; then
    # bash / zsh
    source "$VENV_DIR/bin/activate"
  else
    echo "Virtual environment not found at $VENV_DIR"
    exit 1
  fi
}

run_backend() {
  echo "Starting backend server..."
  cd "$BACKEND_DIR"
  activate_venv
  exec python run.py
}

run_frontend() {
  echo "Starting frontend server..."
  cd "$FRONTEND_DIR"
  exec yarn dev
}

choose_server() {
  echo "Which part of ebarml do you want to run?"
  echo "1) Backend"
  echo "2) Frontend"
  echo "3) Exit"

  read -rp "Enter choice [1-2]: " choice

  case "$choice" in
  1) run_backend ;;
  2) run_frontend ;;
  3)
    echo "Exiting..."
    exit 0
    ;;
  *)
    echo "Invalid choice"
    choose_server
    ;;
  esac
}

PARAM="$1"

case $PARAM in
backend) run_backend ;;
frontend) run_frontend ;;
"") choose_server ;;
*)
  echo "Invalid parameter. Use: server | frontend | desktop"
  exit 1
  ;;
esac
