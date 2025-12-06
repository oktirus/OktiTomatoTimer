# -*- coding: utf-8 -*-
"""
Вікно налаштувань TomatoTimer
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from utils.config_manager import ConfigManager
from core.sound_manager import SoundManager


class SettingsWindow:
    def __init__(self, parent, config_manager: ConfigManager, on_save_callback=None):
        """
        Ініціалізація вікна налаштувань

        Args:
            parent: Батьківське вікно
            config_manager: Менеджер конфігурації
            on_save_callback: Колбек при збереженні
        """
        self.parent = parent
        self.config = config_manager
        self.on_save_callback = on_save_callback

        # Створюємо модальне вікно
        self.window = tk.Toplevel(parent)
        self.window.title("Налаштування")
        self.window.geometry("500x600")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()

        # Центруємо вікно
        self._center_window()

        # Менеджер звуку для тестування
        self.sound_manager = SoundManager()

        # Створюємо віджети
        self._create_widgets()

        # Завантажуємо поточні налаштування
        self._load_settings()

    def _center_window(self):
        """Центрування вікна відносно батьківського"""
        self.window.update_idletasks()
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()

        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2

        self.window.geometry(f"+{x}+{y}")

    def _create_widgets(self):
        """Створення віджетів"""
        # Основний контейнер з можливістю прокручування
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        title_label = ttk.Label(
            main_frame,
            text="⚙ Налаштування",
            font=("Arial", 18, "bold")
        )
        title_label.pack(pady=(0, 20))

        # --- Налаштування часу ---
        time_frame = ttk.LabelFrame(main_frame, text="Налаштування часу", padding="10")
        time_frame.pack(fill=tk.X, pady=10)

        # Робочий час
        ttk.Label(time_frame, text="Робочий час (хвилини):").grid(
            row=0, column=0, sticky=tk.W, pady=5
        )

        self.work_duration_var = tk.IntVar()
        work_spinbox = ttk.Spinbox(
            time_frame,
            from_=1,
            to=60,
            textvariable=self.work_duration_var,
            width=10
        )
        work_spinbox.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # Час перерви
        ttk.Label(time_frame, text="Час перерви (хвилини):").grid(
            row=1, column=0, sticky=tk.W, pady=5
        )

        self.break_duration_var = tk.IntVar()
        break_spinbox = ttk.Spinbox(
            time_frame,
            from_=1,
            to=30,
            textvariable=self.break_duration_var,
            width=10
        )
        break_spinbox.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # --- Звукові налаштування ---
        sound_frame = ttk.LabelFrame(main_frame, text="Звукові налаштування", padding="10")
        sound_frame.pack(fill=tk.X, pady=10)

        # Гучність
        ttk.Label(sound_frame, text="Гучність:").grid(
            row=0, column=0, sticky=tk.W, pady=5
        )

        self.volume_var = tk.IntVar()
        volume_scale = ttk.Scale(
            sound_frame,
            from_=0,
            to=100,
            variable=self.volume_var,
            orient=tk.HORIZONTAL,
            length=200,
            command=self._on_volume_change
        )
        volume_scale.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        self.volume_label = ttk.Label(sound_frame, text="50%")
        self.volume_label.grid(row=0, column=2, sticky=tk.W, pady=5, padx=(10, 0))

        # Кнопка тестування звуку
        test_button = ttk.Button(
            sound_frame,
            text="🔊 Тест",
            command=self._test_sound
        )
        test_button.grid(row=0, column=3, sticky=tk.W, pady=5, padx=(10, 0))

        # Увімкнути звук
        self.sound_enabled_var = tk.BooleanVar()
        sound_check = ttk.Checkbutton(
            sound_frame,
            text="Увімкнути звукові сигнали",
            variable=self.sound_enabled_var
        )
        sound_check.grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=5)

        # Вибір звуку для закінчення роботи
        ttk.Label(sound_frame, text="Звук закінчення роботи:").grid(
            row=2, column=0, sticky=tk.W, pady=5
        )

        self.work_end_sound_var = tk.StringVar()
        self.work_sound_entry = ttk.Entry(
            sound_frame,
            textvariable=self.work_end_sound_var,
            width=25,
            state='readonly'
        )
        self.work_sound_entry.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(10, 5))

        browse_work_sound_btn = ttk.Button(
            sound_frame,
            text="Вибрати...",
            command=self._browse_work_sound
        )
        browse_work_sound_btn.grid(row=2, column=2, columnspan=2, sticky=tk.W, pady=5, padx=5)

        # Вибір звуку для закінчення перерви
        ttk.Label(sound_frame, text="Звук закінчення перерви:").grid(
            row=3, column=0, sticky=tk.W, pady=5
        )

        self.break_end_sound_var = tk.StringVar()
        self.break_sound_entry = ttk.Entry(
            sound_frame,
            textvariable=self.break_end_sound_var,
            width=25,
            state='readonly'
        )
        self.break_sound_entry.grid(row=3, column=1, sticky=tk.W, pady=5, padx=(10, 5))

        browse_break_sound_btn = ttk.Button(
            sound_frame,
            text="Вибрати...",
            command=self._browse_break_sound
        )
        browse_break_sound_btn.grid(row=3, column=2, columnspan=2, sticky=tk.W, pady=5, padx=5)

        # --- Інші налаштування ---
        other_frame = ttk.LabelFrame(main_frame, text="Інші налаштування", padding="10")
        other_frame.pack(fill=tk.X, pady=10)

        # Автозапуск
        self.autostart_var = tk.BooleanVar()
        autostart_check = ttk.Checkbutton(
            other_frame,
            text="Запускати при старті системи",
            variable=self.autostart_var
        )
        autostart_check.grid(row=0, column=0, sticky=tk.W, pady=5)

        # Повноекранний режим під час перерви
        self.fullscreen_var = tk.BooleanVar()
        fullscreen_check = ttk.Checkbutton(
            other_frame,
            text="Повноекранний режим під час перерви",
            variable=self.fullscreen_var
        )
        fullscreen_check.grid(row=1, column=0, sticky=tk.W, pady=5)

        # Показувати поради
        self.show_tips_var = tk.BooleanVar()
        tips_check = ttk.Checkbutton(
            other_frame,
            text="Показувати поради під час перерви",
            variable=self.show_tips_var
        )
        tips_check.grid(row=2, column=0, sticky=tk.W, pady=5)

        # --- Кнопки ---
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(pady=20)

        save_button = ttk.Button(
            buttons_frame,
            text="💾 Зберегти",
            command=self._save_settings,
            width=15
        )
        save_button.grid(row=0, column=0, padx=5)

        cancel_button = ttk.Button(
            buttons_frame,
            text="❌ Скасувати",
            command=self.window.destroy,
            width=15
        )
        cancel_button.grid(row=0, column=1, padx=5)

        reset_button = ttk.Button(
            buttons_frame,
            text="🔄 За замовчуванням",
            command=self._reset_to_defaults,
            width=15
        )
        reset_button.grid(row=0, column=2, padx=5)

    def _load_settings(self):
        """Завантаження поточних налаштувань"""
        self.work_duration_var.set(self.config.get("work_duration", 25))
        self.break_duration_var.set(self.config.get("break_duration", 5))
        self.volume_var.set(self.config.get("volume", 50))
        self.sound_enabled_var.set(self.config.get("sound_enabled", True))
        self.autostart_var.set(self.config.get("autostart_enabled", False))
        self.fullscreen_var.set(self.config.get("fullscreen_break", True))
        self.show_tips_var.set(self.config.get("show_tips", True))

        # Завантажуємо звукові файли
        work_sound = self.config.get("work_end_sound", "")
        break_sound = self.config.get("break_end_sound", "")
        self.work_end_sound_var.set(work_sound if work_sound else "Системний звук")
        self.break_end_sound_var.set(break_sound if break_sound else "Системний звук")

        self._update_volume_label()

    def _on_volume_change(self, value):
        """Оновлення мітки гучності"""
        self._update_volume_label()

    def _update_volume_label(self):
        """Оновлення тексту мітки гучності"""
        volume = int(self.volume_var.get())
        self.volume_label.config(text=f"{volume}%")

    def _browse_work_sound(self):
        """Вибір звукового файлу для закінчення роботи"""
        file_path = filedialog.askopenfilename(
            title="Виберіть звуковий файл для закінчення роботи",
            filetypes=[
                ("Звукові файли", "*.wav *.mp3 *.ogg"),
                ("WAV файли", "*.wav"),
                ("MP3 файли", "*.mp3"),
                ("OGG файли", "*.ogg"),
                ("Всі файли", "*.*")
            ]
        )

        if file_path:
            self.work_end_sound_var.set(file_path)

    def _browse_break_sound(self):
        """Вибір звукового файлу для закінчення перерви"""
        file_path = filedialog.askopenfilename(
            title="Виберіть звуковий файл для закінчення перерви",
            filetypes=[
                ("Звукові файли", "*.wav *.mp3 *.ogg"),
                ("WAV файли", "*.wav"),
                ("MP3 файли", "*.mp3"),
                ("OGG файли", "*.ogg"),
                ("Всі файли", "*.*")
            ]
        )

        if file_path:
            self.break_end_sound_var.set(file_path)

    def _test_sound(self):
        """Тестування звуку"""
        # Встановлюємо поточну гучність
        self.sound_manager.set_volume(self.volume_var.get())

        if self.sound_enabled_var.get():
            self.sound_manager.enable()
        else:
            self.sound_manager.disable()

        # Відтворюємо тестовий звук
        work_sound = self.work_end_sound_var.get()
        if work_sound and work_sound != "Системний звук":
            self.sound_manager.test_sound(work_sound)
        else:
            self.sound_manager.test_sound()

    def _save_settings(self):
        """Збереження налаштувань"""
        # Валідація
        work_duration = self.work_duration_var.get()
        break_duration = self.break_duration_var.get()

        if work_duration < 1 or work_duration > 60:
            messagebox.showerror(
                "Помилка",
                "Робочий час повинен бути від 1 до 60 хвилин"
            )
            return

        if break_duration < 1 or break_duration > 30:
            messagebox.showerror(
                "Помилка",
                "Час перерви повинен бути від 1 до 30 хвилин"
            )
            return

        # Збереження
        self.config.set("work_duration", work_duration, save=False)
        self.config.set("break_duration", break_duration, save=False)
        self.config.set("volume", self.volume_var.get(), save=False)
        self.config.set("sound_enabled", self.sound_enabled_var.get(), save=False)
        self.config.set("autostart_enabled", self.autostart_var.get(), save=False)
        self.config.set("fullscreen_break", self.fullscreen_var.get(), save=False)
        self.config.set("show_tips", self.show_tips_var.get(), save=False)

        # Зберігаємо звукові файли
        work_sound = self.work_end_sound_var.get()
        break_sound = self.break_end_sound_var.get()
        self.config.set("work_end_sound", work_sound if work_sound != "Системний звук" else "", save=False)
        self.config.set("break_end_sound", break_sound if break_sound != "Системний звук" else "", save=False)

        # Зберігаємо всі зміни одразу
        self.config.save()

        # Застосовуємо автозапуск
        self._apply_autostart()

        # Викликаємо колбек
        if self.on_save_callback:
            self.on_save_callback()

        # Показуємо повідомлення
        messagebox.showinfo("Успіх", "Налаштування збережено!")

        # Закриваємо вікно
        self.window.destroy()

    def _apply_autostart(self):
        """Застосування налаштувань автозапуску"""
        try:
            from core.autostart import AutostartManager
            autostart = AutostartManager()

            if self.autostart_var.get():
                autostart.enable()
            else:
                autostart.disable()
        except Exception as e:
            print(f"Помилка налаштування автозапуску: {e}")

    def _reset_to_defaults(self):
        """Скидання налаштувань до значень за замовчуванням"""
        if messagebox.askyesno(
            "Підтвердження",
            "Скинути всі налаштування до значень за замовчуванням?"
        ):
            self.config.reset_to_defaults()
            self._load_settings()
            messagebox.showinfo("Успіх", "Налаштування скинуто!")
