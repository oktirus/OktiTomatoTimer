# -*- coding: utf-8 -*-
"""
Спільні візуальні константи TomatoTimer (Fluent / Windows 11)
"""

from PySide6.QtGui import QColor, QFont

from core.timer import TimerState

# Акцент застосунку: томатний червоний (контраст з білим текстом кнопки ≥ 4.5:1)
ACCENT = "#C8372D"

# Колір фази: (світла тема, темна тема)
PHASE_COLORS = {
    TimerState.WORK: ("#C8372D", "#FF6B5E"),
    TimerState.BREAK: ("#2E7D4F", "#5FCB8A"),
    TimerState.PAUSED: ("#8A8A8A", "#9E9E9E"),
    TimerState.IDLE: ("#8A8A8A", "#9E9E9E"),
}


def phase_colors(state: TimerState):
    light, dark = PHASE_COLORS[state]
    return QColor(light), QColor(dark)


def digits_font(pixel_size: int) -> QFont:
    """Шрифт цифр таймера: дисплейне накреслення системного шрифту Windows 11"""
    font = QFont(["Segoe UI Variable Display", "Segoe UI"])
    font.setPixelSize(pixel_size)
    font.setWeight(QFont.DemiBold)
    return font
