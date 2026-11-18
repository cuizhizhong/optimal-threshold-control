#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT/latex"
for document in main supplementary; do
  xelatex -no-pdf -interaction=nonstopmode -halt-on-error "$document.tex"
  biber "$document"
  xelatex -no-pdf -interaction=nonstopmode -halt-on-error "$document.tex"
  xelatex -interaction=nonstopmode -halt-on-error "$document.tex"
done
echo "$ROOT/latex/main.pdf"
echo "$ROOT/latex/supplementary.pdf"
