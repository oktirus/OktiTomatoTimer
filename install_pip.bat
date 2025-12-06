@echo off
echo Встановлення pip...
echo.

REM Завантажуємо get-pip.py
echo Крок 1: Завантаження get-pip.py...
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py

if %ERRORLEVEL% NEQ 0 (
    echo Помилка завантаження! Спробуйте вручну:
    echo 1. Відкрийте https://bootstrap.pypa.io/get-pip.py
    echo 2. Збережіть як get-pip.py
    echo 3. Запустіть: python get-pip.py
    pause
    exit /b 1
)

echo.
echo Крок 2: Встановлення pip...
python get-pip.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Помилка встановлення!
    echo Можливо Python не встановлений або не доданий до PATH.
    pause
    exit /b 1
)

echo.
echo Крок 3: Перевірка встановлення...
pip --version

echo.
echo ========================================
echo pip успішно встановлено!
echo ========================================
echo.
pause
