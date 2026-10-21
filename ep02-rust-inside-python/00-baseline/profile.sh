#!/usr/bin/env bash
# Profile the baseline with py-spy and write a flame graph to profile.svg.
# Run it inside the baseline's virtual environment:
#   cd 00-baseline && source .venv/bin/activate && bash profile.sh
set -euo pipefail
cd "$(dirname "$0")"
pip install -q py-spy httpx
py-spy record -o profile.svg -- python ../bench/load.py .
echo "Open 00-baseline/profile.svg in a browser."
