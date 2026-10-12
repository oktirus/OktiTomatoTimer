# -*- coding: utf-8 -*-
"""
Основна логіка таймера для TomatoTimer
"""

from enum import Enum
from typing import Callable, Optional


class TimerState(Enum):
    """Стани таймера"""
    IDLE = "idle"           # Очікування
    WORK = "work"           # Робочий час
    BREAK = "break"         # Перерва
    PAUSED = "paused"       # На паузі


class PomodoroTimer:
    def __init__(self, work_duration: int = 25, break_duration: int = 5, long_break_duration: int = 10, pomodoros_until_long_break: int = 4, auto_start_work: bool = False):
        """
        Ініціалізація таймера

        Args:
            work_duration: Тривалість робочого часу (хвилини)
            break_duration: Тривалість перерви (хвилини)
            long_break_duration: Тривалість довгої перерви (хвилини)
            pomodoros_until_long_break: Кількість помідорів до довгої перерви
            auto_start_work: Автоматичний запуск роботи після перерви
        """
        self.work_duration = work_duration * 60  # Переводимо в секунди
        self.break_duration = break_duration * 60
        self.long_break_duration = long_break_duration * 60
        self.pomodoros_until_long_break = pomodoros_until_long_break
        self.auto_start_work = auto_start_work

        self.state = TimerState.IDLE
        self.time_left = 0  # Залишок часу в секундах
        self.total_time = 0  # Повна тривалість поточної фази (для прогресу)
        self.completed_pomodoros = 0
        self.is_long_break = False  # Прапорець для довгої перерви
        self._previous_state = TimerState.WORK  # Стан, до якого повертаємось після паузи

        # Колбеки для подій
        self.on_tick: Optional[Callable[[int], None]] = None
        self.on_work_start: Optional[Callable[[], None]] = None
        self.on_work_end: Optional[Callable[[], None]] = None
        self.on_break_start: Optional[Callable[[], None]] = None
        self.on_break_end: Optional[Callable[[], None]] = None
        self.on_state_change: Optional[Callable[[TimerState], None]] = None

    def _set_state(self, state: TimerState):
        self.state = state
        if self.on_state_change:
            self.on_state_change(self.state)

    def start_work(self):
        """Початок робочого часу"""
        self.state = TimerState.WORK
        self.time_left = self.total_time = self.work_duration

        if self.on_work_start:
            self.on_work_start()

        self._set_state(TimerState.WORK)

    def start_break(self, long_break: bool = False):
        """Початок перерви"""
        self.state = TimerState.BREAK
        self.is_long_break = long_break
        self.time_left = self.total_time = self.long_break_duration if long_break else self.break_duration

        if self.on_break_start:
            self.on_break_start()

        self._set_state(TimerState.BREAK)

    def complete_work(self):
        """Завершення робочого часу (за таймером або достроково) і перехід до перерви"""
        self.completed_pomodoros += 1

        if self.on_work_end:
            self.on_work_end()

        self.start_break(self.completed_pomodoros % self.pomodoros_until_long_break == 0)

    def finish_break(self):
        """Завершення перерви (за таймером або достроково)"""
        if self.auto_start_work:
            self.start_work()
        else:
            self.time_left = self.total_time = 0
            self._set_state(TimerState.IDLE)

        # Викликаємо після переходу, щоб слухач бачив новий стан
        if self.on_break_end:
            self.on_break_end()

    def pause(self):
        """Пауза таймера"""
        if self.is_running():
            self._previous_state = self.state
            self._set_state(TimerState.PAUSED)

    def resume(self):
        """Відновлення таймера після паузи"""
        if self.state == TimerState.PAUSED:
            self._set_state(self._previous_state)

    def reset(self):
        """Скидання таймера"""
        self.time_left = self.total_time = 0
        self._set_state(TimerState.IDLE)

    def tick(self):
        """
        Оновлення таймера (викликається щосекунди)

        Returns:
            bool: True якщо фаза триває, False якщо таймер неактивний або фаза завершилась
        """
        if not self.is_running():
            return False

        self.time_left = max(0, self.time_left - 1)

        if self.on_tick:
            self.on_tick(self.time_left)

        if self.time_left > 0:
            return True

        if self.state == TimerState.WORK:
            self.complete_work()
        else:
            self.finish_break()

        return False

    def set_work_duration(self, minutes: int):
        """Встановлення тривалості робочого часу"""
        self.work_duration = minutes * 60

    def set_break_duration(self, minutes: int):
        """Встановлення тривалості перерви"""
        self.break_duration = minutes * 60

    def set_long_break_duration(self, minutes: int):
        """Встановлення тривалості довгої перерви"""
        self.long_break_duration = minutes * 60

    def set_pomodoros_until_long_break(self, count: int):
        """Встановлення кількості помідорів до довгої перерви"""
        self.pomodoros_until_long_break = count

    def set_auto_start_work(self, enabled: bool):
        """Встановлення автоматичного запуску роботи після перерви"""
        self.auto_start_work = enabled

    def get_time_formatted(self) -> str:
        """
        Отримання часу у форматі MM:SS

        Returns:
            str: Відформатований час
        """
        minutes = self.time_left // 60
        seconds = self.time_left % 60
        return f"{minutes:02d}:{seconds:02d}"

    def get_progress(self) -> float:
        """
        Отримання прогресу поточної фази

        Returns:
            float: Прогрес від 0.0 до 1.0
        """
        if self.state == TimerState.IDLE or self.total_time <= 0:
            return 0.0

        return 1.0 - (self.time_left / self.total_time)

    def is_running(self) -> bool:
        """Перевірка чи таймер активний"""
        return self.state in (TimerState.WORK, TimerState.BREAK)

    def is_paused(self) -> bool:
        """Перевірка чи таймер на паузі"""
        return self.state == TimerState.PAUSED

    def add_time(self, seconds: int = 60):
        """
        Додавання додаткового часу до поточного таймера

        Args:
            seconds: Кількість секунд для додавання (за замовчуванням 60 = 1 хвилина)
        """
        if self.is_running():
            self.time_left += seconds
            self.total_time += seconds
            if self.on_tick:
                self.on_tick(self.time_left)
