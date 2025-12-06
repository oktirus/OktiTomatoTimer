@echo off
REM Запуск TomatoTimer

echo Starting TomatoTimer...
python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Помилка запуску! Переконайтесь, що Python встановлено.
    echo.
    pause
)
