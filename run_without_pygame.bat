@echo off
echo ========================================
echo   TomatoTimer (без pygame)
echo ========================================
echo.
echo УВАГА: Запуск без pygame
echo Звук буде відтворюватись через системні засоби
echo.

python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Помилка запуску!
    echo.
    echo Можливі причини:
    echo 1. Python не встановлено
    echo 2. Python не доданий до PATH
    echo.
    echo Рішення:
    echo 1. Встановіть Python з https://www.python.org/downloads/
    echo 2. Під час встановлення поставте галочку "Add Python to PATH"
    echo.
    pause
)
