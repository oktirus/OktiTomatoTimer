# -*- coding: utf-8 -*-
"""
Налаштування за замовчуванням для TomatoTimer
"""

DEFAULT_SETTINGS = {
    # Налаштування таймера
    "work_duration": 25,  # хвилини
    "break_duration": 5,  # хвилини

    # Звукові налаштування
    "volume": 50,  # 0-100
    "sound_enabled": True,
    "work_end_sound": "default_work_end.wav",
    "break_end_sound": "default_break_end.wav",

    # Налаштування інтерфейсу
    "language": "uk",  # українська
    "theme": "light",  # light або dark

    # Автозапуск
    "autostart_enabled": False,

    # Налаштування блокування екрану
    "fullscreen_break": True,
    "show_tips": True,
    "allow_skip_break": False,  # дозволити пропуск перерви

    # Статистика
    "track_statistics": True,
    "completed_pomodoros": 0,
}
