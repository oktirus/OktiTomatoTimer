@echo off
chcp 65001 >nul
echo ========================================
echo   Збірка TomatoTimer в EXE файл
echo ========================================
echo.

REM Перевірка наявності PyInstaller
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [ПОМИЛКА] PyInstaller не встановлено!
    echo.
    echo Встановлюю PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo [ПОМИЛКА] Не вдалося встановити PyInstaller
        pause
        exit /b 1
    )
    echo.
    echo ✅ PyInstaller успішно встановлено!
    echo.
)

REM Видалення старих файлів збірки
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist TomatoTimer.spec del /q TomatoTimer.spec

echo Починаю збірку...
echo.

REM Збірка exe файлу
pyinstaller --noconsole --onefile --name TomatoTimer ^
    --add-data "data;data" ^
    --hidden-import=PIL ^
    --hidden-import=PIL._tkinter_finder ^
    --hidden-import=pystray ^
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
