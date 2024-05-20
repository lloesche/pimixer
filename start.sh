#!/bin/sh
export KIVY_BCM_DISPMANX_ID=2
SCRIPT_DIR="$(dirname "$0")"
. "$SCRIPT_DIR/venv/bin/activate"
python3 "$SCRIPT_DIR/pimixer/__main__.py"
