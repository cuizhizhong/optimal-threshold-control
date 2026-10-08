@echo off
setlocal enabledelayedexpansion
set ROOT=%~dp0
set TVARG=
if "%1"=="--recompute-tv" set TVARG=--recompute-tv

python "%ROOT%python\generate_data.py" %TVARG% || exit /b 1
for %%F in ("%ROOT%python\Figure_*.py") do (
  python "%%~fF" || exit /b 1
)

pushd "%ROOT%latex"
xelatex -interaction=nonstopmode -halt-on-error main.tex || exit /b 1
where bibtex >nul 2>nul
if %errorlevel%==0 (
  bibtex main || exit /b 1
) else (
  where bibtex8 >nul 2>nul
  if %errorlevel%==0 bibtex8 main || exit /b 1
)
xelatex -interaction=nonstopmode -halt-on-error main.tex || exit /b 1
xelatex -interaction=nonstopmode -halt-on-error main.tex || exit /b 1
copy /Y main.pdf "%ROOT%tracing_isolation_optimal_control.pdf" >nul
popd
echo %ROOT%tracing_isolation_optimal_control.pdf
endlocal
