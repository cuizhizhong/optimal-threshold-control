#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT/latex"
for document in main supplementary; do
  xelatex -interaction=nonstopmode -halt-on-error "$document.tex"
  if grep -Fq '\bibdata' "$document.aux"; then
    bibtex "$document"
  fi
  xelatex -interaction=nonstopmode -halt-on-error "$document.tex"
  xelatex -interaction=nonstopmode -halt-on-error "$document.tex"
done
echo "$ROOT/latex/main.pdf"
echo "$ROOT/latex/supplementary.pdf"
