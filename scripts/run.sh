#!/usr/bin/env bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"

BACKEND_DIR="$PROJECT_ROOT/backend"
VENV_DIR="$BACKEND_DIR/.venv"

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

choose_server() {
    echo "Which part of ebarml do you want to run?"
    echo "1) Backend"
    echo "2) Exit"

    read -rp "Enter choice [1-2]: " choice

    case "$choice" in
        1) run_backend ;;
        2) echo "Exiting..."; exit 0 ;;
        *) echo "Invalid choice"; choose_server ;;
    esac
}

PARAM="$1"

case "$PARAM" in
    server|backend)
        run_backend
        ;;
    "" )
        choose_server
        ;;
    * )
        echo "Invalid parameter. Use: backend or no arguments"
        exit 1
        ;;
esac
