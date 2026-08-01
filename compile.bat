@echo off
title Fiuza Technology - Build Executavel
mode con: cols=90 lines=40
color 0B

cd /d "%~dp0"

echo.
echo ==========================================================
echo                    FIUZA TECHNOLOGY BUILD
echo ==========================================================
echo.

set PYTHON=py -3.8

echo Limpando builds antigos e processos presos...
echo.

taskkill /f /im Pack_econect.exe >nul 2>&1
taskkill /f /im TelegramCloud.exe >nul 2>&1
taskkill /f /im updater.exe >nul 2>&1
taskkill /f /im pyinstaller.exe >nul 2>&1

if exist build rmdir /s /q build
if exist build_updater rmdir /s /q build_updater
if exist dist rmdir /s /q dist
if exist dist_updater rmdir /s /q dist_updater

if exist Pack_econect.spec del /f /q Pack_econect.spec
if exist TelegramCloud.spec del /f /q TelegramCloud.spec
if exist updater.spec del /f /q updater.spec

for /d /r %%d in (__pycache__) do (
    if exist "%%d" rmdir /s /q "%%d"
)

echo Limpeza concluida.
echo.

:: ==========================================================
:: BUILD 1: PACK_ECONECT (App Principal)
:: ==========================================================
echo ==========================================================
echo                1/3 - GERANDO PACK_ECONECT.EXE
echo ==========================================================
echo.

%PYTHON% -m PyInstaller ^
--noconfirm ^
--clean ^
--noupx ^
--onedir ^
--windowed ^
--paths=. ^
--collect-all customtkinter ^
--collect-all requests ^
--collect-all certifi ^
--collect-all cryptography ^
--collect-all PIL ^
--collect-all cv2 ^
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
--add-data "assets\wallpaper;assets\wallpaper" ^
--add-data ".env;." ^
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
:: BUILD 2: TELEGRAM CLOUD (Integração Nuvem)
:: ==========================================================
echo.
echo ==========================================================
echo                2/3 - GERANDO TELEGRAMCLOUD.EXE
echo ==========================================================
echo.

if exist "telegram_api\telegram_cloud_app.py" (
    %PYTHON% -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --noupx ^
    --onedir ^
    --windowed ^
    --paths=. ^
    --paths=telegram_api ^
    --collect-all customtkinter ^
    --collect-all telethon ^
    --collect-all PIL ^
    --hidden-import=utils ^
    --hidden-import=tela_bloqueio ^
    --collect-all cryptg ^
    --add-data "telegram_api\gerenciador.py;." ^
    --add-data "assets;assets" ^
    --add-data ".env;." ^
    --icon=assets/cloud.ico ^
    --name TelegramCloud ^
    --distpath="dist\TelegramCloud_Temp" ^
    telegram_api\telegram_cloud_app.py

    if errorlevel 1 (
        echo.
        echo ERRO AO GERAR TELEGRAMCLOUD.EXE
        goto FALHA_FINAL
    )
    
    :: Move o executavel da nuvem e suas dependencias para a mesma pasta do app principal
    xcopy /s /e /y "dist\TelegramCloud_Temp\TelegramCloud\*" "dist\Pack_econect\" >nul
    rmdir /s /q "dist\TelegramCloud_Temp" >nul
) else (
    echo.
    echo AVISO: telegram_api\telegram_cloud_app.py nao encontrado. Ignorando modulo de nuvem...
)

timeout /t 2 >nul

:: ==========================================================
:: BUILD 3: UPDATER (SANDBOX ISOLADO)
:: ==========================================================
echo.
echo ==========================================================
echo                3/3 - GERANDO UPDATER.EXE
echo ==========================================================
echo.

if exist updater_launcher.py (
    %PYTHON% -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --noupx ^
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
if exist TelegramCloud.spec del /f /q TelegramCloud.spec >nul 2>&1
if exist updater.spec del /f /q updater.spec >nul 2>&1

:: ==========================================================
:: RESULTADO FINAL
:: ==========================================================
echo.
echo ==========================================================
echo                        BUILD FINALIZADA
echo ==========================================================
echo.
echo COMPILACAO CONCLUIDA COM SUCESSO!
echo.
echo 1. O seu app principal (e a Nuvem) estao em 'dist\Pack_econect'.
echo 2. Se o updater foi gerado, estara em 'dist_updater'.
echo.

explorer dist\Pack_econect

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