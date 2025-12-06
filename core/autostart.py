# -*- coding: utf-8 -*-
"""
Менеджер автозапуску для TomatoTimer
Підтримка Windows, macOS, Linux
"""

import os
import sys
import platform


class AutostartManager:
    def __init__(self, app_name="TomatoTimer"):
        """
        Ініціалізація менеджера автозапуску

        Args:
            app_name: Назва додатка
        """
        self.app_name = app_name
        self.system = platform.system()

        # Визначаємо шлях до виконуваного файлу
        if getattr(sys, 'frozen', False):
            # Якщо запущено як exe (PyInstaller)
            self.app_path = sys.executable
        else:
            # Якщо запущено як скрипт Python
            self.app_path = os.path.abspath(sys.argv[0])

    def enable(self):
        """Увімкнення автозапуску"""
        if self.system == "Windows":
            return self._enable_windows()
        elif self.system == "Darwin":  # macOS
            return self._enable_macos()
        elif self.system == "Linux":
            return self._enable_linux()
        else:
            print(f"Автозапуск не підтримується для {self.system}")
            return False

    def disable(self):
        """Вимкнення автозапуску"""
        if self.system == "Windows":
            return self._disable_windows()
        elif self.system == "Darwin":
            return self._disable_macos()
        elif self.system == "Linux":
            return self._disable_linux()
        else:
            return False

    def is_enabled(self):
        """Перевірка чи увімкнений автозапуск"""
        if self.system == "Windows":
            return self._is_enabled_windows()
        elif self.system == "Darwin":
            return self._is_enabled_macos()
        elif self.system == "Linux":
            return self._is_enabled_linux()
        else:
            return False

    # Windows методи
    def _enable_windows(self):
        """Увімкнення автозапуску для Windows"""
        try:
            import winreg

            # Відкриваємо ключ реєстру
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )

            # Додаємо значення
            winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, f'"{self.app_path}"')
            winreg.CloseKey(key)

            return True

        except Exception as e:
            print(f"Помилка увімкнення автозапуску Windows: {e}")
            return False

    def _disable_windows(self):
        """Вимкнення автозапуску для Windows"""
        try:
            import winreg

            # Відкриваємо ключ реєстру
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )

            # Видаляємо значення
            try:
                winreg.DeleteValue(key, self.app_name)
            except FileNotFoundError:
                pass  # Значення вже відсутнє

            winreg.CloseKey(key)
            return True

        except Exception as e:
            print(f"Помилка вимкнення автозапуску Windows: {e}")
            return False

    def _is_enabled_windows(self):
        """Перевірка автозапуску для Windows"""
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ
            )

            try:
                value, _ = winreg.QueryValueEx(key, self.app_name)
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False

        except Exception as e:
            print(f"Помилка перевірки автозапуску Windows: {e}")
            return False

    # macOS методи
    def _enable_macos(self):
        """Увімкнення автозапуску для macOS"""
        try:
            import plistlib

            # Шлях до plist файлу
            plist_path = os.path.expanduser(f"~/Library/LaunchAgents/com.{self.app_name}.plist")

            # Створюємо plist
            plist_data = {
                'Label': f'com.{self.app_name}',
                'ProgramArguments': [self.app_path],
                'RunAtLoad': True
            }

            # Зберігаємо файл
            with open(plist_path, 'wb') as f:
                plistlib.dump(plist_data, f)

            # Встановлюємо права
            os.chmod(plist_path, 0o644)

            return True

        except Exception as e:
            print(f"Помилка увімкнення автозапуску macOS: {e}")
            return False

    def _disable_macos(self):
        """Вимкнення автозапуску для macOS"""
        try:
            plist_path = os.path.expanduser(f"~/Library/LaunchAgents/com.{self.app_name}.plist")

            if os.path.exists(plist_path):
                os.remove(plist_path)

            return True

        except Exception as e:
            print(f"Помилка вимкнення автозапуску macOS: {e}")
            return False

    def _is_enabled_macos(self):
        """Перевірка автозапуску для macOS"""
        plist_path = os.path.expanduser(f"~/Library/LaunchAgents/com.{self.app_name}.plist")
        return os.path.exists(plist_path)

    # Linux методи
    def _enable_linux(self):
        """Увімкнення автозапуску для Linux"""
        try:
            # Створюємо директорію, якщо не існує
            autostart_dir = os.path.expanduser("~/.config/autostart")
            os.makedirs(autostart_dir, exist_ok=True)

            # Шлях до desktop файлу
            desktop_path = os.path.join(autostart_dir, f"{self.app_name}.desktop")

            # Створюємо desktop файл
            desktop_content = f"""[Desktop Entry]
Type=Application
Name={self.app_name}
Exec=python3 "{self.app_path}"
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Comment=Pomodoro Timer
"""

            with open(desktop_path, 'w', encoding='utf-8') as f:
                f.write(desktop_content)

            # Встановлюємо права
            os.chmod(desktop_path, 0o755)

            return True

        except Exception as e:
            print(f"Помилка увімкнення автозапуску Linux: {e}")
            return False

    def _disable_linux(self):
        """Вимкнення автозапуску для Linux"""
        try:
            desktop_path = os.path.expanduser(f"~/.config/autostart/{self.app_name}.desktop")

            if os.path.exists(desktop_path):
                os.remove(desktop_path)

            return True

        except Exception as e:
            print(f"Помилка вимкнення автозапуску Linux: {e}")
            return False

    def _is_enabled_linux(self):
        """Перевірка автозапуску для Linux"""
        desktop_path = os.path.expanduser(f"~/.config/autostart/{self.app_name}.desktop")
        return os.path.exists(desktop_path)
