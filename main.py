# -*- coding: utf-8 -*-
"""
TomatoTimer - Таймер продуктивності за методом Pomodoro
Головний файл запуску програми
"""

import tkinter as tk
import sys
import os

# Додаємо поточну директорію до шляху пошуку модулів
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow
from utils.config_manager import ConfigManager


def main():
    """Головна функція запуску програми"""
    # Створюємо кореневе вікно
    root = tk.Tk()

    # Ініціалізуємо менеджер конфігурації
    config_manager = ConfigManager()

    # Створюємо головне вікно
    app = MainWindow(root, config_manager)

    # Запускаємо головний цикл
    try:
        app.run()
    except KeyboardInterrupt:
        print("\nПрограма завершена користувачем")
    except Exception as e:
        print(f"Помилка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
