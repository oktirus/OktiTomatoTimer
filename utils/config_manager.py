# -*- coding: utf-8 -*-
"""
Менеджер конфігурації для TomatoTimer
Відповідає за завантаження, збереження та управління налаштуваннями
"""

import json
import os
from typing import Any, Dict
from config.default_settings import DEFAULT_SETTINGS


class ConfigManager:
    def __init__(self, config_dir: str = None):
        """
        Ініціалізація менеджера конфігурації

        Args:
            config_dir: Директорія для збереження конфігурації
        """
        if config_dir is None:
            # Використовуємо домашню директорію користувача
            home = os.path.expanduser("~")
            config_dir = os.path.join(home, ".tomatotimer")

        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "settings.json")
        self.settings = {}

        # Створюємо директорію, якщо не існує
        os.makedirs(config_dir, exist_ok=True)

        # Завантажуємо налаштування
        self.load()

    def load(self):
        """Завантаження налаштувань з файлу"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)

                # Додаємо відсутні налаштування зі значень за замовчуванням
                for key, value in DEFAULT_SETTINGS.items():
                    if key not in self.settings:
                        self.settings[key] = value
            except Exception as e:
                print(f"Помилка завантаження налаштувань: {e}")
                self.settings = DEFAULT_SETTINGS.copy()
        else:
            # Використовуємо налаштування за замовчуванням
            self.settings = DEFAULT_SETTINGS.copy()
            self.save()

    def save(self):
        """Збереження налаштувань у файл"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Помилка збереження налаштувань: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Отримання значення налаштування

        Args:
            key: Ключ налаштування
            default: Значення за замовчуванням

        Returns:
            Значення налаштування
        """
        return self.settings.get(key, default)

    def set(self, key: str, value: Any, save: bool = True):
        """
        Встановлення значення налаштування

        Args:
            key: Ключ налаштування
            value: Нове значення
            save: Чи зберігати зміни одразу
        """
        self.settings[key] = value
        if save:
            self.save()

    def get_all(self) -> Dict[str, Any]:
        """Отримання всіх налаштувань"""
        return self.settings.copy()

    def update(self, settings_dict: Dict[str, Any], save: bool = True):
        """
        Оновлення декількох налаштувань одразу

        Args:
            settings_dict: Словник з новими налаштуваннями
            save: Чи зберігати зміни одразу
        """
        self.settings.update(settings_dict)
        if save:
            self.save()

    def reset_to_defaults(self):
        """Скидання налаштувань до значень за замовчуванням"""
        self.settings = DEFAULT_SETTINGS.copy()
        self.save()
