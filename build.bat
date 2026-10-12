@echo off
chcp 65001 >nul
echo ========================================
echo   Збірка TomatoTimer в EXE файл
echo ========================================
echo.

REM Встановлення залежностей і PyInstaller фіксованих версій
python -m pip install -r requirements.txt pyinstaller==6.17.0
if errorlevel 1 (
    echo [ПОМИЛКА] Не вдалося встановити залежності
    pause
    exit /b 1
)

REM pygame опціональний (гучність, MP3/OGG); без нього збірка використовує winsound
python -m pip install pygame==2.6.1 || echo [УВАГА] pygame не встановлено, звук лише WAV без гучності
echo.

REM Видалення старих файлів збірки
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist TomatoTimer.spec del /q TomatoTimer.spec

echo Починаю збірку...
echo.

REM Збірка exe файлу
python -m PyInstaller --noconsole --onefile --name TomatoTimer ^
    --add-data "data;data" ^
    main.py

if errorlevel 1 (
    echo.
    echo [ПОМИЛКА] Збірка не вдалася!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   ✅ Збірка завершена успішно!
echo ========================================
echo.
echo EXE файл знаходиться тут:
echo %CD%\dist\TomatoTimer.exe
echo.
echo Для запуску просто відкрийте файл TomatoTimer.exe
echo.

REM Відкриваємо папку з результатом
explorer dist

pause
