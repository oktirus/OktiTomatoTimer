# -*- coding: utf-8 -*-
"""
System Tray Icon для TomatoTimer
Відображає таймер в треї Windows
"""

import tkinter as tk
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pystray
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False


class TrayIcon:
    """Клас для роботи з іконкою в system tray"""

    def __init__(self, app_name="TomatoTimer", on_click=None):
        """
        Ініціалізація tray icon

        Args:
            app_name: Назва програми
            on_click: Колбек при кліку на іконку
        """
        self.app_name = app_name
        self.on_click = on_click
        self.icon = None
        self.current_time = "25:00"

        if not PYSTRAY_AVAILABLE:
            print("[TRAY] pystray не встановлено. Іконка в треї недоступна.")
            print("[TRAY] Для увімкнення: pip install pystray pillow")
            return

    def create_image(self, time_text="25:00"):
        """
        Створення зображення для іконки з текстом часу

        Args:
            time_text: Текст таймера для відображення

        Returns:
            PIL.Image або None
        """
        if not PIL_AVAILABLE:
            # Повертаємо просту іконку без PIL
            return self._create_simple_icon()

        try:
            # Створюємо зображення 64x64
            width = 64
            height = 64
            image = Image.new('RGB', (width, height), color=(255, 87, 34))  # Помаранчевий

            # Малюємо
            draw = ImageDraw.Draw(image)

            # Малюємо круг
            draw.ellipse([4, 4, 60, 60], fill=(255, 87, 34), outline=(255, 255, 255), width=2)

            # Додаємо текст часу
            try:
                font = ImageFont.truetype("arial.ttf", 14)
            except:
                font = ImageFont.load_default()

            # Центруємо текст
            bbox = draw.textbbox((0, 0), time_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            x = (width - text_width) // 2
            y = (height - text_height) // 2

            draw.text((x, y), time_text, fill=(255, 255, 255), font=font)

            return image
        except Exception as e:
            print(f"[TRAY] Помилка створення зображення: {e}")
            return self._create_simple_icon()

    def _create_simple_icon(self):
        """Створення простої іконки без PIL"""
        if not PIL_AVAILABLE:
            return None

        try:
            image = Image.new('RGB', (64, 64), color=(255, 87, 34))
            return image
        except:
            return None

    def update_time(self, time_text):
        """
        Оновлення часу на іконці

        Args:
            time_text: Новий час для відображення
        """
        if not PYSTRAY_AVAILABLE or not self.icon:
            return

        self.current_time = time_text

        try:
            # Оновлюємо іконку
            new_image = self.create_image(time_text)
            if new_image and self.icon:
                self.icon.icon = new_image
        except Exception as e:
            print(f"[TRAY] Помилка оновлення іконки: {e}")

    def start(self):
        """Запуск іконки в треї"""
        if not PYSTRAY_AVAILABLE:
            return

        try:
            import threading

            # Створюємо меню
            menu = pystray.Menu(
                pystray.MenuItem("Відкрити", self._on_open),
                pystray.MenuItem("Вихід", self._on_exit)
            )

            # Створюємо іконку
            image = self.create_image(self.current_time)
            self.icon = pystray.Icon(
                self.app_name,
                image if image else self._create_simple_icon(),
                self.app_name,
                menu
            )

            # Запускаємо в окремому потоці
            thread = threading.Thread(target=self.icon.run, daemon=True)
            thread.start()

            print("[TRAY] Іконка в треї запущена")
        except Exception as e:
            print(f"[TRAY] Помилка запуску іконки: {e}")

    def stop(self):
        """Зупинка іконки в треї"""
        if self.icon:
            try:
                self.icon.stop()
                print("[TRAY] Іконка в треї зупинена")
            except Exception as e:
                print(f"[TRAY] Помилка зупинки іконки: {e}")

    def _on_open(self, icon, item):
        """Обробка кліку на 'Відкрити'"""
        if self.on_click:
            self.on_click()

    def _on_exit(self, icon, item):
        """Обробка кліку на 'Вихід'"""
        self.stop()
