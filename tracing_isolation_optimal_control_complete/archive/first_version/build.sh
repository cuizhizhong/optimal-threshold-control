#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

TV_ARG=""
if [[ "${1:-}" == "--recompute-tv" ]]; then
  TV_ARG="--recompute-tv"
fi

python "$ROOT/python/generate_data.py" $TV_ARG
for script in "$ROOT"/python/Figure_*.py; do
  python "$script"
done

cd "$ROOT/latex"
xelatex -interaction=nonstopmode -halt-on-error main.tex
if command -v bibtex >/dev/null 2>&1; then
  bibtex main
elif command -v bibtex8 >/dev/null 2>&1; then
  bibtex8 main
else
  echo "Neither bibtex nor bibtex8 was found; using the included main.bbl." >&2
fi
xelatex -interaction=nonstopmode -halt-on-error main.tex
xelatex -interaction=nonstopmode -halt-on-error main.tex
cp -f main.pdf "$ROOT/tracing_isolation_optimal_control.pdf"
echo "$ROOT/tracing_isolation_optimal_control.pdf"
