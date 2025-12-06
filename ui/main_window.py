# -*- coding: utf-8 -*-
"""
Головне вікно TomatoTimer
"""

import tkinter as tk
from tkinter import ttk, font
from core.timer import PomodoroTimer, TimerState
from core.sound_manager import SoundManager
from core.tips_manager import TipsManager
from utils.config_manager import ConfigManager
from ui.tray_icon import TrayIcon


class MainWindow:
    def __init__(self, root: tk.Tk, config_manager: ConfigManager):
        """
        Ініціалізація головного вікна

        Args:
            root: Кореневий tk віджет
            config_manager: Менеджер конфігурації
        """
        self.root = root
        self.config = config_manager

        # Налаштування вікна
        self.root.title("TomatoTimer")
        self.root.geometry("420x500")
        self.root.resizable(False, False)

        # Ініціалізуємо компоненти
        work_duration = self.config.get("work_duration", 25)
        break_duration = self.config.get("break_duration", 5)
        long_break_duration = self.config.get("long_break_duration", 10)
        pomodoros_until_long_break = self.config.get("pomodoros_until_long_break", 4)

        self.timer = PomodoroTimer(work_duration, break_duration, long_break_duration, pomodoros_until_long_break)
        self.sound_manager = SoundManager()
        self.tips_manager = TipsManager()

        # Встановлюємо гучність зі збережених налаштувань
        volume = self.config.get("volume", 50)
        self.sound_manager.set_volume(volume)

        # Референс на вікно перерви
        self.break_window = None

        # ID для оновлення таймера
        self.timer_id = None

        # Іконка в треї
        self.tray_icon = TrayIcon("TomatoTimer", self._on_tray_click)
        self.tray_icon.start()

        # Налаштовуємо колбеки таймера
        self._setup_timer_callbacks()

        # Створюємо інтерфейс
        self._create_widgets()

        # Оновлюємо відображення
        self._update_display()

    def _setup_timer_callbacks(self):
        """Налаштування колбеків таймера"""
        self.timer.on_tick = self._on_timer_tick
        self.timer.on_work_end = self._on_work_end
        self.timer.on_break_start = self._on_break_start
        self.timer.on_break_end = self._on_break_end
        self.timer.on_state_change = self._on_state_change

    def _create_widgets(self):
        """Створення віджетів інтерфейсу"""
        # Основний контейнер
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Верхня панель з заголовком та іконкою налаштувань
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))

        # Іконка налаштувань (абсолютно справа)
        settings_button = tk.Button(
            header_frame,
            text="⚙",
            command=self._on_settings_click,
            font=("Segoe UI Emoji", 20),
            width=2,
            height=1,
            bg="#f0f0f0",
            relief=tk.FLAT,
            cursor="hand2",
            borderwidth=0
        )
        settings_button.pack(side=tk.RIGHT)

        # Контейнер для іконки та заголовка (по центру)
        title_container = ttk.Frame(header_frame)
        title_container.pack(expand=True)

        # Іконка помідора
        icon_label = ttk.Label(
            title_container,
            text="🍅",
            font=("Segoe UI Emoji", 24)
        )
        icon_label.pack(side=tk.LEFT, padx=(0, 8))

        # Заголовок
        title_label = ttk.Label(
            title_container,
            text="TomatoTimer",
            font=("Arial", 24, "bold")
        )
        title_label.pack(side=tk.LEFT)

        # Індикатор стану
        self.state_label = ttk.Label(
            main_frame,
            text="Готовий до роботи",
            font=("Arial", 14)
        )
        self.state_label.pack(pady=(0, 10))

        # Контейнер для таймера з кнопкою
        timer_container = ttk.Frame(main_frame)
        timer_container.pack(pady=20)

        # Дисплей таймера
        self.timer_label = ttk.Label(
            timer_container,
            text="25:00",
            font=("Arial", 72, "bold")
        )
        self.timer_label.pack(side=tk.LEFT)

        # Кнопка додавання 1 хвилини (праворуч від таймера, зверху)
        self.add_time_button = tk.Button(
            timer_container,
            text="+",
            command=self._on_add_time_click,
            font=("Arial", 10, "bold"),
            width=2,
            height=1,
            bg="#E5E7EB",
            fg="#374151",
            relief=tk.FLAT,
            cursor="hand2",
            state=tk.DISABLED,
            borderwidth=0
        )
        self.add_time_button.pack(side=tk.LEFT, anchor=tk.N, padx=(5, 0))

        # Прогрес-бар
        self.progress = ttk.Progressbar(
            main_frame,
            length=300,
            mode='determinate'
        )
        self.progress.pack(pady=10)

        # Кнопки керування
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(pady=20)

        self.start_button = ttk.Button(
            buttons_frame,
            text="Старт",
            command=self._on_start_click,
            width=12
        )
        self.start_button.grid(row=0, column=0, padx=5)

        self.pause_button = ttk.Button(
            buttons_frame,
            text="Пауза",
            command=self._on_pause_click,
            width=12,
            state=tk.DISABLED
        )
        self.pause_button.grid(row=0, column=1, padx=5)

        self.reset_button = ttk.Button(
            buttons_frame,
            text="Скинути",
            command=self._on_reset_click,
            width=12
        )
        self.reset_button.grid(row=0, column=2, padx=5)

        # Кнопка швидкого переходу до перерви
        self.skip_to_break_button = ttk.Button(
            buttons_frame,
            text="➔ Перерва",
            command=self._on_skip_to_break_click,
            width=12
        )
        self.skip_to_break_button.grid(row=0, column=3, padx=5)

        # Статистика
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(pady=20)

        ttk.Label(
            stats_frame,
            text="Виконано помідорів:",
            font=("Arial", 11)
        ).grid(row=0, column=0, padx=5)

        self.pomodoros_label = ttk.Label(
            stats_frame,
            text="0",
            font=("Arial", 11, "bold")
        )
        self.pomodoros_label.grid(row=0, column=1, padx=5)

    def _on_start_click(self):
        """Обробка натискання кнопки Старт"""
        if self.timer.state == TimerState.IDLE:
            self.timer.start_work()
            self._start_timer_loop()

            # Оновлюємо кнопки
            self.start_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            self.add_time_button.config(state=tk.NORMAL)

        elif self.timer.state == TimerState.PAUSED:
            self.timer.resume()
            self._start_timer_loop()

            # Оновлюємо кнопки
            self.start_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL, text="Пауза")
            self.add_time_button.config(state=tk.NORMAL)

    def _on_pause_click(self):
        """Обробка натискання кнопки Пауза"""
        if self.timer.is_running():
            self.timer.pause()
            self._stop_timer_loop()

            # Оновлюємо кнопки
            self.start_button.config(state=tk.NORMAL)
            self.pause_button.config(text="Продовжити")

    def _on_reset_click(self):
        """Обробка натискання кнопки Скинути"""
        self.timer.reset()
        self._stop_timer_loop()

        # Оновлюємо кнопки
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED, text="Пауза")
        self.add_time_button.config(state=tk.DISABLED)

        # Оновлюємо відображення
        self._update_display()

    def _on_add_time_click(self):
        """Обробка натискання кнопки додавання часу"""
        if self.timer.state in [TimerState.WORK, TimerState.BREAK]:
            self.timer.add_time(60)  # Додаємо 60 секунд (1 хвилину)
            self._update_display()

    def _on_skip_to_break_click(self):
        """Швидкий перехід до перерви"""
        if self.timer.state == TimerState.WORK:
            # Якщо працюємо, моментально переходимо до перерви
            self._stop_timer_loop()
            self.timer.completed_pomodoros += 1
            self._on_work_end()
            self.timer.start_break()
            self._start_timer_loop()
            self.add_time_button.config(state=tk.NORMAL)
        elif self.timer.state == TimerState.IDLE:
            # Якщо неактивний, просто запускаємо перерву
            self.timer.start_break()
            self._start_timer_loop()
            self.add_time_button.config(state=tk.NORMAL)

    def _on_settings_click(self):
        """Відкриття вікна налаштувань"""
        from ui.settings_window import SettingsWindow
        SettingsWindow(self.root, self.config, self._on_settings_saved)

    def _on_settings_saved(self):
        """Колбек після збереження налаштувань"""
        # Оновлюємо тривалість таймера
        work_duration = self.config.get("work_duration", 25)
        break_duration = self.config.get("break_duration", 5)
        long_break_duration = self.config.get("long_break_duration", 10)
        pomodoros_until_long_break = self.config.get("pomodoros_until_long_break", 4)

        self.timer.set_work_duration(work_duration)
        self.timer.set_break_duration(break_duration)
        self.timer.set_long_break_duration(long_break_duration)
        self.timer.set_pomodoros_until_long_break(pomodoros_until_long_break)

        # Оновлюємо гучність
        volume = self.config.get("volume", 50)
        self.sound_manager.set_volume(volume)

        # Оновлюємо відображення
        self._update_display()

    def _start_timer_loop(self):
        """Запуск циклу оновлення таймера"""
        if self.timer_id is None:
            self._timer_loop()

    def _stop_timer_loop(self):
        """Зупинка циклу оновлення таймера"""
        if self.timer_id is not None:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

    def _timer_loop(self):
        """Основний цикл оновлення таймера (викликається кожну секунду)"""
        if self.timer.is_running():
            self.timer.tick()
            # Плануємо наступне оновлення через 1 секунду
            self.timer_id = self.root.after(1000, self._timer_loop)
        else:
            self.timer_id = None

    def _on_timer_tick(self, time_left: int):
        """Колбек при кожному тіку таймера"""
        self._update_display()

        # Оновлюємо час в треї з прогресом та режимом
        if self.tray_icon:
            progress = self.timer.get_progress()
            # Визначаємо режим
            if self.timer.state == TimerState.WORK:
                mode = "work"
            elif self.timer.state == TimerState.BREAK:
                mode = "break"
            else:
                mode = "idle"
            self.tray_icon.update_time(self.timer.get_time_formatted(), progress, mode)

    def _on_work_end(self):
        """Колбек при закінченні робочого часу"""
        # Відтворюємо звук
        sound_file = self.config.get("work_end_sound", "")
        if sound_file:
            self.sound_manager.play_sound(sound_file)
        else:
            self.sound_manager.test_sound()

        # Оновлюємо статистику
        self._update_display()

    def _on_break_start(self):
        """Колбек при початку перерви"""
        # Відкриваємо повноекранне вікно з порадами
        from ui.break_window import BreakWindow
        self.break_window = BreakWindow(
            self.root,
            self.timer,
            self.tips_manager,
            self._on_break_window_closed
        )

    def _on_break_end(self):
        """Колбек при закінченні перерви"""
        # Відтворюємо звук
        sound_file = self.config.get("break_end_sound", "")
        if sound_file:
            self.sound_manager.play_sound(sound_file)
        else:
            self.sound_manager.test_sound()

        # Закриваємо вікно перерви, якщо воно ще відкрите
        if self.break_window:
            self.break_window.close()

        # Оновлюємо кнопки
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        self.add_time_button.config(state=tk.DISABLED)

        # Оновлюємо відображення
        self._update_display()

    def _on_break_window_closed(self):
        """Колбек при закритті вікна перерви"""
        self.break_window = None

    def _on_state_change(self, state: TimerState):
        """Колбек при зміні стану таймера"""
        self._update_display()

    def _on_tray_click(self):
        """Колбек при кліку на іконку в треї"""
        # Відновлюємо вікно, якщо воно згорнуте
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _update_display(self):
        """Оновлення відображення"""
        # Оновлюємо час
        self.timer_label.config(text=self.timer.get_time_formatted())

        # Оновлюємо стан
        if self.timer.state == TimerState.IDLE:
            self.state_label.config(text="Готовий до роботи")
            self.timer_label.config(foreground="black")
            work_duration = self.config.get("work_duration", 25)
            self.timer_label.config(text=f"{work_duration:02d}:00")
            self.progress['value'] = 0

        elif self.timer.state == TimerState.WORK:
            self.state_label.config(text="⏱ Робочий час")
            self.timer_label.config(foreground="#2E7D32")  # Зелений
            self.progress['value'] = self.timer.get_progress() * 100

        elif self.timer.state == TimerState.BREAK:
            if self.timer.is_long_break:
                self.state_label.config(text="🏖 Довга перерва")
            else:
                self.state_label.config(text="☕ Перерва")
            self.timer_label.config(foreground="#FF6F00")  # Помаранчевий
            self.progress['value'] = self.timer.get_progress() * 100

        elif self.timer.state == TimerState.PAUSED:
            self.state_label.config(text="⏸ На паузі")
            self.timer_label.config(foreground="#757575")  # Сірий

        # Оновлюємо статистику
        self.pomodoros_label.config(text=str(self.timer.completed_pomodoros))

    def run(self):
        """Запуск головного циклу додатка"""
        self.root.mainloop()
