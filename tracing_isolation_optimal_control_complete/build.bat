@echo off
setlocal
set "ROOT=%~dp0"
pushd "%ROOT%latex" || exit /b 1
for %%D in (main supplementary) do (
    call :build %%D || goto :failed
)
popd
echo %ROOT%latex\main.pdf
echo %ROOT%latex\supplementary.pdf
endlocal
exit /b 0

:build
xelatex -interaction=nonstopmode -halt-on-error "%~1.tex" || exit /b 1
findstr /L /C:"\bibdata" "%~1.aux" >nul
if not errorlevel 1 (
    bibtex "%~1" || exit /b 1
)
xelatex -interaction=nonstopmode -halt-on-error "%~1.tex" || exit /b 1
xelatex -interaction=nonstopmode -halt-on-error "%~1.tex" || exit /b 1
exit /b 0

:failed
popd
endlocal
exit /b 1
