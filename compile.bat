@echo off
title Fiuza Technology - Build Executavel
mode con: cols=90 lines=35
color 0B

cd /d "%~dp0"

echo.
echo ==========================================================
echo                    FIUZA TECHNOLOGY BUILD
echo ==========================================================
echo.

set PYTHON=py -3.12

echo Limpando builds antigos e processos presos...
echo.

taskkill /f /im Pack_econect.exe >nul 2>&1
taskkill /f /im updater.exe >nul 2>&1
taskkill /f /im pyinstaller.exe >nul 2>&1

if exist build rmdir /s /q build
if exist build_updater rmdir /s /q build_updater
if exist dist rmdir /s /q dist
if exist dist_updater rmdir /s /q dist_updater

if exist Pack_econect.spec del /f /q Pack_econect.spec
if exist updater.spec del /f /q updater.spec

for /d /r %%d in (__pycache__) do (
    if exist "%%d" rmdir /s /q "%%d"
)

echo Limpeza concluida.
echo.

:: ==========================================================
:: BUILD PACK_ECONECT
:: ==========================================================
echo ==========================================================
echo                GERANDO PACK_ECONECT.EXE
echo ==========================================================
echo.

%PYTHON% -m PyInstaller ^
--noconfirm ^
--clean ^
--onedir ^
--windowed ^
--paths=. ^
--collect-all customtkinter ^
--collect-all requests ^
--collect-all certifi ^
--collect-all cryptography ^
--collect-all PIL ^
--hidden-import=ui ^
--hidden-import=ui.app ^
--hidden-import=core ^
--hidden-import=core.auth ^
--hidden-import=core.downloader ^
--hidden-import=core.file_builder ^
--hidden-import=core.parser ^
--hidden-import=core.theme ^
--hidden-import=core.updater ^
--hidden-import=core.zip_manager ^
--add-data "assets;assets" ^
--icon=assets/icon.ico ^
--name Pack_econect ^
main.py

if errorlevel 1 (
    echo.
    echo ERRO AO GERAR PACK_ECONECT.EXE
    goto FALHA_FINAL
)

timeout /t 2 >nul

:: ==========================================================
:: BUILD UPDATER (SANDBOX ISOLADO)
:: ==========================================================
echo.
echo ==========================================================
echo                GERANDO UPDATER.EXE
echo ==========================================================
echo.

if exist updater_launcher.py (
    %PYTHON% -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --windowed ^
    --uac-admin ^
    --specpath="." ^
    --workpath="build_updater" ^
    --distpath="dist_updater" ^
    --collect-all requests ^
    --collect-all certifi ^
    --hidden-import=core.updater ^
    --icon=assets/icon.ico ^
    --name updater ^
    updater_launcher.py
) else (
    echo.
    echo AVISO: updater_launcher.py nao encontrado. Ignorando updater...
)

:: Limpeza de pastas temporarias de codigo, mantendo apenas os executaveis finais
if exist build rmdir /s /q build >nul 2>&1
if exist build_updater rmdir /s /q build_updater >nul 2>&1
if exist Pack_econect.spec del /f /q Pack_econect.spec >nul 2>&1
if exist updater.spec del /f /q updater.spec >nul 2>&1

:: ==========================================================
:: RESULTADO FINAL
:: ==========================================================
echo.
echo ==========================================================
echo                   BUILD FINALIZADA
echo ==========================================================
echo.
echo COMPILACAO CONCLUIDA COM SUCESSO!
echo.
echo 1. O seu app principal esta em 'dist\Pack_econect'.
echo 2. Se o updater foi gerado, estara em 'dist_updater'.
echo.

explorer dist

echo msgbox "Compilacao concluida com sucesso!",64,"Fiuza Technology" > popup.vbs
start /wait popup.vbs
del popup.vbs
goto FIM

:FALHA_FINAL
echo.
echo ATENCAO: O PROCESSO DE BUILD FALHOU!
echo.

:FIM
echo Pressione qualquer tecla para fechar esta janela...
pause >nul