@echo off

:: Obter o diretório atual
set "current_dir=%cd%"

:: Iniciar o primeiro processo em um novo shell
start cmd /k "cd /d %current_dir%\BackBolinha\BackBolinha && dotnet run BackBolinha.cprojs"

:: Iniciar o quarto processo em um novo shell
start chrome.exe %current_dir%\monitor.html