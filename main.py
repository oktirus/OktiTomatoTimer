# -*- coding: utf-8 -*-
"""
TomatoTimer - Таймер продуктивності за методом Pomodoro
Головний файл запуску програми
"""

import logging
import os
import sys

# Додаємо поточну директорію до шляху пошуку модулів
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from qfluentwidgets import setThemeColor

from ui.main_window import MainWindow
from ui.settings_page import apply_theme
from ui.style import ACCENT
from utils.config_manager import ConfigManager

log = logging.getLogger("tomatotimer")


def setup_logging(log_dir: str):
    """Лог у файл (у --noconsole exe консолі немає) і в консоль, якщо вона є"""
    handlers = [logging.FileHandler(os.path.join(log_dir, "tomatotimer.log"), encoding="utf-8")]
    if sys.stderr:
        handlers.append(logging.StreamHandler())
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
    )


def log_unhandled(*exc_info):
    log.error("Необроблена помилка", exc_info=exc_info)


def main():
    """Головна функція запуску програми"""
    config_manager = ConfigManager()
    setup_logging(config_manager.config_dir)
    # Помилки в Qt-слотах інакше губляться в exe без консолі
    sys.excepthook = log_unhandled

    app = QApplication(sys.argv)
    # Вікно ховається в трей, тож закриття останнього вікна не завершує програму
    app.setQuitOnLastWindowClosed(False)

    apply_theme(config_manager.get("theme"))
    setThemeColor(ACCENT)

    window = MainWindow(config_manager)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
