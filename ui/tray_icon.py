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
        self.current_progress = 0.0  # Прогрес від 0.0 до 1.0
        self.current_mode = "idle"  # idle, work, break

        if not PYSTRAY_AVAILABLE:
            print("[TRAY] pystray не встановлено. Іконка в треї недоступна.")
            print("[TRAY] Для увімкнення: pip install pystray pillow")
            return

    def create_image(self, time_text="25:00", progress=0.0, mode="idle"):
        """
        Створення зображення для іконки з текстом часу

        Args:
            time_text: Текст таймера для відображення
            progress: Прогрес від 0.0 до 1.0
            mode: Режим таймера (idle, work, break)

        Returns:
            PIL.Image або None
        """
        if not PIL_AVAILABLE:
            # Повертаємо просту іконку без PIL
            return self._create_simple_icon()

        try:
            # Створюємо зображення 64x64 з ПРОЗОРИМ фоном (RGBA)
            width = 64
            height = 64
            image = Image.new('RGBA', (width, height), color=(0, 0, 0, 0))

            # Малюємо
            draw = ImageDraw.Draw(image)

            # Параметри кругового прогрес-бару
            center_x = width // 2
            center_y = height // 2
            radius = 28  # Радіус кола
            line_width = 6  # Товщина лінії

            # Координати для arc (обмежуюча рамка)
            bbox = [
                center_x - radius,
                center_y - radius,
                center_x + radius,
                center_y + radius
            ]

            # Малюємо повний круг білим кольором (фон)
            draw.arc(bbox, 0, 360, fill=(255, 255, 255, 255), width=line_width)

            # Малюємо круговий прогрес-бар
            # Початок зверху (270 градусів = -90 від 0)
            # progress: 0.0 (пусто) -> 1.0 (повний круг)
            start_angle = -90  # Починаємо зверху
            end_angle = start_angle + (360 * progress)

            # Визначаємо колір заповнення залежно від режиму
            if mode == "work":
                fill_color = (46, 125, 50, 255)  # Зелений (#2E7D32)
            elif mode == "break":
                fill_color = (255, 111, 0, 255)  # Червоний/помаранчевий (#FF6F00)
            else:
                fill_color = (255, 255, 255, 255)  # Білий за замовчуванням

            # Малюємо прогрес кольоровою лінією
            if progress > 0:
                draw.arc(bbox, start_angle, end_angle, fill=fill_color, width=line_width)

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

    def update_time(self, time_text, progress=0.0, mode="idle"):
        """
        Оновлення часу на іконці

        Args:
            time_text: Новий час для відображення
            progress: Прогрес від 0.0 до 1.0
            mode: Режим таймера (idle, work, break)
        """
        if not PYSTRAY_AVAILABLE or not self.icon:
            return

        self.current_time = time_text
        self.current_progress = progress
        self.current_mode = mode

        try:
            # Оновлюємо іконку
            new_image = self.create_image(time_text, progress, mode)
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
