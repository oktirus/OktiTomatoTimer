# -*- coding: utf-8 -*-
"""
Налаштування за замовчуванням для TomatoTimer
"""

DEFAULT_SETTINGS = {
    # Налаштування таймера
    "work_duration": 25,  # хвилини
    "break_duration": 5,  # хвилини
    "long_break_duration": 10,  # хвилини
    "pomodoros_until_long_break": 4,
    "auto_start_work": False,

    # Звукові налаштування
    "volume": 50,  # 0-100
    "sound_enabled": True,
    "work_end_sound": "",  # порожньо = системний звук
    "break_end_sound": "",

    # Система
    "autostart_enabled": False,
    "theme": "auto",  # auto (як у Windows), light, dark

    # Налаштування перерви
    "fullscreen_break": True,
    "show_tips": True,

    # Статистика за день
    "stats_date": "",
    "completed_pomodoros": 0,
}
