# -*- coding: utf-8 -*-
"""
Повноекранне вікно перерви для TomatoTimer
Блокує екран і показує поради для розминки
"""

import tkinter as tk
from tkinter import ttk, font
from core.timer import PomodoroTimer
from core.tips_manager import TipsManager


class BreakWindow:
    def __init__(self, parent, timer: PomodoroTimer, tips_manager: TipsManager, on_close_callback=None):
        """
        Ініціалізація вікна перерви

        Args:
            parent: Батьківське вікно
            timer: Об'єкт таймера
            tips_manager: Менеджер порад
            on_close_callback: Колбек при закритті
        """
        self.parent = parent
        self.timer = timer
        self.tips_manager = tips_manager
        self.on_close_callback = on_close_callback

        # Створюємо повноекранне вікно
        self.window = tk.Toplevel(parent)
        self.window.title("Перерва")

        # Налаштовуємо повноекранний режим
        self._setup_fullscreen()

        # Отримуємо випадкову пораду
        self.current_tip = self.tips_manager.get_random_tip()

        # ID для оновлення таймера
        self.timer_id = None

        # Створюємо інтерфейс
        self._create_widgets()

        # Запускаємо оновлення таймера
        self._start_timer_update()

        # Обробка закриття вікна
        self.window.protocol("WM_DELETE_WINDOW", self._on_close_attempt)

    def _setup_fullscreen(self):
        """Налаштування повноекранного режиму"""
        # Робимо вікно повноекранним
        self.window.attributes('-fullscreen', True)

        # Вікно завжди поверх інших
        self.window.attributes('-topmost', True)

        # Забираємо декорації вікна
        self.window.overrideredirect(True)

        # Темний фон для зменшення навантаження на очі
        self.window.configure(bg='#1E1E1E')

        # Фокус на вікні
        self.window.focus_force()

        # Захоплюємо всі події клавіатури
        self.window.grab_set()

        # Прив'язуємо клавішу Escape для можливості аварійного виходу
        self.window.bind('<Escape>', self._on_escape_press)

    def _create_widgets(self):
        """Створення віджетів"""
        # Основний контейнер
        main_frame = tk.Frame(self.window, bg='#1E1E1E')
        main_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Заголовок
        title_label = tk.Label(
            main_frame,
            text="☕ Час перерви!",
            font=("Arial", 48, "bold"),
            fg='#FF6F00',
            bg='#1E1E1E'
        )
        title_label.pack(pady=(0, 30))

        # Таймер
        self.timer_label = tk.Label(
            main_frame,
            text="05:00",
            font=("Arial", 96, "bold"),
            fg='#FFFFFF',
            bg='#1E1E1E'
        )
        self.timer_label.pack(pady=20)

        # Рамка для поради
        tip_frame = tk.Frame(
            main_frame,
            bg='#2E2E2E',
            padx=40,
            pady=30,
            relief=tk.RAISED,
            borderwidth=2
        )
        tip_frame.pack(pady=30, padx=50)

        # Заголовок поради
        tip_title = tk.Label(
            tip_frame,
            text=self.current_tip.get('title', 'Порада'),
            font=("Arial", 28, "bold"),
            fg='#4CAF50',
            bg='#2E2E2E',
            wraplength=800
        )
        tip_title.pack(pady=(0, 20))

        # Текст поради
        tip_description = tk.Label(
            tip_frame,
            text=self.current_tip.get('description', ''),
            font=("Arial", 20),
            fg='#E0E0E0',
            bg='#2E2E2E',
            wraplength=900,
            justify=tk.CENTER
        )
        tip_description.pack(pady=10)

        # Тривалість
        duration = self.current_tip.get('duration', '')
        if duration:
            duration_label = tk.Label(
                tip_frame,
                text=f"⏱ {duration}",
                font=("Arial", 16),
                fg='#9E9E9E',
                bg='#2E2E2E'
            )
            duration_label.pack(pady=(15, 0))

        # Кнопка наступної поради
        next_tip_button = tk.Button(
            main_frame,
            text="➡ Наступна порада",
            command=self._show_next_tip,
            font=("Arial", 14),
            bg='#424242',
            fg='#FFFFFF',
            activebackground='#616161',
            activeforeground='#FFFFFF',
            padx=20,
            pady=10,
            relief=tk.RAISED,
            borderwidth=2,
            cursor='hand2'
        )
        next_tip_button.pack(pady=20)

        # Інформація про вихід
        info_label = tk.Label(
            main_frame,
            text="Натисніть Escape для виходу (потребує підтвердження)",
            font=("Arial", 12),
            fg='#757575',
            bg='#1E1E1E'
        )
        info_label.pack(pady=(30, 0))

    def _start_timer_update(self):
        """Запуск оновлення таймера"""
        self._update_timer()

    def _update_timer(self):
        """Оновлення відображення таймера"""
        if self.timer.state.value == "break" and self.timer.time_left > 0:
            # Оновлюємо час
            self.timer_label.config(text=self.timer.get_time_formatted())

            # Плануємо наступне оновлення через 500мс
            self.timer_id = self.window.after(500, self._update_timer)
        else:
            # Перерва закінчилась
            self.close()

    def _show_next_tip(self):
        """Показати наступну пораду"""
        # Отримуємо нову пораду
        self.current_tip = self.tips_manager.get_random_tip()

        # Оновлюємо вікно (перестворюємо віджети)
        for widget in self.window.winfo_children():
            widget.destroy()

        self._create_widgets()

    def _on_escape_press(self, event=None):
        """Обробка натискання Escape"""
        # Створюємо діалог підтвердження
        confirm_window = tk.Toplevel(self.window)
        confirm_window.title("Підтвердження")
        confirm_window.geometry("400x200")
        confirm_window.configure(bg='#2E2E2E')
        confirm_window.attributes('-topmost', True)

        # Центруємо вікно
        confirm_window.update_idletasks()
        screen_width = confirm_window.winfo_screenwidth()
        screen_height = confirm_window.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 200) // 2
        confirm_window.geometry(f"+{x}+{y}")

        # Текст
        message = tk.Label(
            confirm_window,
            text="Ви впевнені, що хочете\nперервати перерву?",
            font=("Arial", 16),
            fg='#FFFFFF',
            bg='#2E2E2E'
        )
        message.pack(pady=30)

        # Кнопки
        buttons_frame = tk.Frame(confirm_window, bg='#2E2E2E')
        buttons_frame.pack(pady=20)

        yes_button = tk.Button(
            buttons_frame,
            text="Так",
            command=lambda: self._confirm_close(confirm_window),
            font=("Arial", 14),
            bg='#F44336',
            fg='#FFFFFF',
            padx=20,
            pady=5,
            width=10
        )
        yes_button.grid(row=0, column=0, padx=10)

        no_button = tk.Button(
            buttons_frame,
            text="Ні",
            command=confirm_window.destroy,
            font=("Arial", 14),
            bg='#4CAF50',
            fg='#FFFFFF',
            padx=20,
            pady=5,
            width=10
        )
        no_button.grid(row=0, column=1, padx=10)

        # Фокус на кнопці "Ні"
        no_button.focus()

    def _confirm_close(self, confirm_window):
        """Підтвердження закриття"""
        confirm_window.destroy()
        self.close()

    def _on_close_attempt(self):
        """Спроба закрити вікно"""
        # Перерва повинна тривати до кінця
        # Показуємо діалог
        self._on_escape_press()

    def close(self):
        """Закриття вікна"""
        # Зупиняємо оновлення таймера
        if self.timer_id is not None:
            self.window.after_cancel(self.timer_id)
            self.timer_id = None

        # Викликаємо колбек
        if self.on_close_callback:
            self.on_close_callback()

        # Знищуємо вікно
        try:
            self.window.destroy()
        except:
            pass
