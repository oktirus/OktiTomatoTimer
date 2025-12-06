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
    def __init__(self, work_duration: int = 25, break_duration: int = 5, long_break_duration: int = 10, pomodoros_until_long_break: int = 4):
        """
        Ініціалізація таймера

        Args:
            work_duration: Тривалість робочого часу (хвилини)
            break_duration: Тривалість перерви (хвилини)
            long_break_duration: Тривалість довгої перерви (хвилини)
            pomodoros_until_long_break: Кількість помідорів до довгої перерви
        """
        self.work_duration = work_duration * 60  # Переводимо в секунди
        self.break_duration = break_duration * 60
        self.long_break_duration = long_break_duration * 60
        self.pomodoros_until_long_break = pomodoros_until_long_break

        self.state = TimerState.IDLE
        self.time_left = 0  # Залишок часу в секундах
        self.completed_pomodoros = 0
        self.is_long_break = False  # Прапорець для довгої перерви

        # Колбеки для подій
        self.on_tick: Optional[Callable[[int], None]] = None
        self.on_work_start: Optional[Callable[[], None]] = None
        self.on_work_end: Optional[Callable[[], None]] = None
        self.on_break_start: Optional[Callable[[], None]] = None
        self.on_break_end: Optional[Callable[[], None]] = None
        self.on_state_change: Optional[Callable[[TimerState], None]] = None

    def start_work(self):
        """Початок робочого часу"""
        self.state = TimerState.WORK
        self.time_left = self.work_duration

        if self.on_work_start:
            self.on_work_start()

        if self.on_state_change:
            self.on_state_change(self.state)

    def start_break(self):
        """Початок перерви"""
        self.state = TimerState.BREAK

        # Перевіряємо, чи це час для довгої перерви
        if self.completed_pomodoros > 0 and self.completed_pomodoros % self.pomodoros_until_long_break == 0:
            self.time_left = self.long_break_duration
            self.is_long_break = True
        else:
            self.time_left = self.break_duration
            self.is_long_break = False

        self.completed_pomodoros += 1

        if self.on_break_start:
            self.on_break_start()

        if self.on_state_change:
            self.on_state_change(self.state)

    def pause(self):
        """Пауза таймера"""
        if self.state in [TimerState.WORK, TimerState.BREAK]:
            self.state = TimerState.PAUSED

            if self.on_state_change:
                self.on_state_change(self.state)

    def resume(self):
        """Відновлення таймера після паузи"""
        if self.state == TimerState.PAUSED:
            # Визначаємо, до якого стану повертатись
            if self.time_left > 0:
                # Якщо час залишився, повертаємось до попереднього стану
                # Це буде або WORK, або BREAK
                if hasattr(self, '_previous_state'):
                    self.state = self._previous_state
                else:
                    self.state = TimerState.WORK

            if self.on_state_change:
                self.on_state_change(self.state)

    def reset(self):
        """Скидання таймера"""
        self.state = TimerState.IDLE
        self.time_left = 0

        if self.on_state_change:
            self.on_state_change(self.state)

    def tick(self):
        """
        Оновлення таймера (викликається щосекунди)

        Returns:
            bool: True якщо таймер активний, False якщо завершився
        """
        if self.state not in [TimerState.WORK, TimerState.BREAK]:
            return False

        if self.time_left > 0:
            self.time_left -= 1

            if self.on_tick:
                self.on_tick(self.time_left)

            return True
        else:
            # Час закінчився
            if self.state == TimerState.WORK:
                # Закінчився робочий час
                if self.on_work_end:
                    self.on_work_end()

                # Автоматично починаємо перерву
                self.start_break()

            elif self.state == TimerState.BREAK:
                # Закінчилась перерва
                if self.on_break_end:
                    self.on_break_end()

                # Повертаємось до стану очікування
                self.state = TimerState.IDLE
                self.time_left = 0

                if self.on_state_change:
                    self.on_state_change(self.state)

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
        Отримання прогресу таймера у відсотках

        Returns:
            float: Прогрес від 0.0 до 1.0
        """
        if self.state == TimerState.WORK:
            total = self.work_duration
        elif self.state == TimerState.BREAK:
            total = self.break_duration
        else:
            return 0.0

        if total == 0:
            return 0.0

        return 1.0 - (self.time_left / total)

    def is_running(self) -> bool:
        """Перевірка чи таймер активний"""
        return self.state in [TimerState.WORK, TimerState.BREAK]

    def is_paused(self) -> bool:
        """Перевірка чи таймер на паузі"""
        return self.state == TimerState.PAUSED

    def add_time(self, seconds: int = 60):
        """
        Додавання додаткового часу до поточного таймера

        Args:
            seconds: Кількість секунд для додавання (за замовчуванням 60 = 1 хвилина)
        """
        if self.state in [TimerState.WORK, TimerState.BREAK]:
            self.time_left += seconds
            if self.on_tick:
                self.on_tick(self.time_left)
