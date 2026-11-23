#!/bin/bash
DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
cd "$DIR"
exec python3 "$DIR/install.py" "$@"
