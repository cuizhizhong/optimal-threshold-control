@echo off
setlocal
set ROOT=%~dp0
pushd "%ROOT%latex"
xelatex -interaction=nonstopmode -halt-on-error main.tex || exit /b 1
bibtex main || exit /b 1
xelatex -interaction=nonstopmode -halt-on-error main.tex || exit /b 1
xelatex -interaction=nonstopmode -halt-on-error main.tex || exit /b 1
popd
echo %ROOT%latex\main.pdf
endlocal
