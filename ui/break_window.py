# -*- coding: utf-8 -*-
"""
Вікно перерви TomatoTimer: перекриває всі екрани (або показується поверх інших вікон)
і пропонує пораду для розминки
"""

from PySide6.QtCore import QObject, Qt, QTimer
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import QVBoxLayout, QWidget
from qfluentwidgets import (BodyLabel, CaptionLabel, FluentIcon, MessageBox, ProgressRing, PushButton,
                            SubtitleLabel, TitleLabel, isDarkTheme, setFont)

from core.timer import PomodoroTimer, TimerState
from core.tips_manager import TipsManager
from ui.style import digits_font, phase_colors


class _Surface(QWidget):
    """Одне вікно перерви; Esc і закриття передаються власнику як запит завершити перерву"""

    def __init__(self, owner: "BreakWindow", flags):
        super().__init__(None, flags)
        self.owner = owner
        self.closing = False
        self.setObjectName("breakSurface")
        self.setStyleSheet(f"#breakSurface {{ background-color: {'#202020' if isDarkTheme() else '#F3F3F3'}; }}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.owner.request_skip()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        if self.closing:
            event.accept()
        else:
            event.ignore()
            self.owner.request_skip()


class BreakWindow(QObject):
    def __init__(self, parent, timer: PomodoroTimer, tips_manager: TipsManager, on_close_callback=None,
                 on_skip_callback=None, fullscreen: bool = True, show_tips: bool = True):
        """
        Args:
            parent: Головне вікно (для власності Qt-об'єкта)
            timer: Об'єкт таймера
            tips_manager: Менеджер порад
            on_close_callback: Колбек при закритті
            on_skip_callback: Колбек, коли користувач підтвердив дострокове завершення перерви
            fullscreen: Перекрити всі екрани чи показати звичайне вікно поверх інших
            show_tips: Показувати поради
        """
        super().__init__(parent)
        self.timer = timer
        self.tips_manager = tips_manager
        self.on_close_callback = on_close_callback
        self.on_skip_callback = on_skip_callback
        self.fullscreen = fullscreen
        self.current_tip = self.tips_manager.get_random_tip() if show_tips else None
        self.surfaces = []

        if fullscreen:
            flags = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
            primary = QGuiApplication.primaryScreen()
            # Основний екран першим: на ньому контент
            for screen in [primary] + [s for s in QGuiApplication.screens() if s is not primary]:
                surface = _Surface(self, flags)
                surface.setScreen(screen)
                surface.setGeometry(screen.geometry())
                self.surfaces.append(surface)
        else:
            surface = _Surface(self, Qt.Window | Qt.WindowStaysOnTopHint)
            surface.setWindowTitle("Перерва")
            self.surfaces.append(surface)

        self.window = self.surfaces[0]
        self._create_content(self.window)

        for surface in self.surfaces:
            if fullscreen:
                surface.showFullScreen()
            else:
                surface.show()
        self.window.raise_()
        self.window.activateWindow()

        self.poll = QTimer(self)
        self.poll.timeout.connect(self._update_timer)
        self.poll.start(500)

    def _create_content(self, surface: QWidget):
        layout = QVBoxLayout(surface)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)
        layout.setContentsMargins(48, 40, 48, 40)

        # На весь екран читаємо з відстані, тож шрифти більші
        scale = 1.6 if self.fullscreen else 1.0
        title = TitleLabel("Довга перерва" if self.timer.is_long_break else "Перерва", surface)
        setFont(title, int(28 * scale), QFont.DemiBold)
        layout.addWidget(title, 0, Qt.AlignHCenter)

        size = 320 if self.fullscreen else 200
        self.ring = ProgressRing(surface, useAni=False)
        self.ring.setFixedSize(size, size)
        self.ring.setStrokeWidth(12)
        self.ring.setRange(0, 1000)
        self.ring.setTextVisible(True)
        self.ring.setFont(digits_font(size // 4))
        self.ring.setCustomBarColor(*phase_colors(TimerState.BREAK))
        layout.addWidget(self.ring, 0, Qt.AlignHCenter)

        if self.current_tip:
            tip = QWidget(surface)
            tip.setFixedWidth(int(520 * scale))
            tip_layout = QVBoxLayout(tip)
            tip_layout.setContentsMargins(0, 16, 0, 0)
            tip_layout.setSpacing(6)
            self.tip_title = SubtitleLabel(tip)
            self.tip_text = BodyLabel(tip)
            self.tip_text.setWordWrap(True)
            self.tip_duration = CaptionLabel(tip)
            setFont(self.tip_title, int(20 * scale), QFont.DemiBold)
            setFont(self.tip_text, int(14 * scale))
            setFont(self.tip_duration, int(12 * scale))
            for widget in (self.tip_title, self.tip_text, self.tip_duration):
                tip_layout.addWidget(widget)
            layout.addWidget(tip, 0, Qt.AlignHCenter)

            next_button = PushButton(FluentIcon.SYNC, "Інша порада", surface)
            next_button.clicked.connect(self._show_next_tip)
            layout.addWidget(next_button, 0, Qt.AlignHCenter)
            self._fill_tip()

        hint = CaptionLabel("Натисніть Esc, щоб завершити перерву раніше", surface)
        hint.setTextColor("#6E6E6E", "#A0A0A0")
        layout.addWidget(hint, 0, Qt.AlignHCenter)

        self._update_ring()

    def _fill_tip(self):
        self.tip_title.setText(self.current_tip.get("title", "Порада"))
        self.tip_text.setText(self.current_tip.get("description", ""))
        duration = self.current_tip.get("duration", "")
        self.tip_duration.setText(f"Тривалість: {duration}" if duration else "")

    def _show_next_tip(self):
        self.current_tip = self.tips_manager.get_random_tip()
        self._fill_tip()

    def _update_ring(self):
        self.ring.setFormat(self.timer.get_time_formatted())
        self.ring.setValue(int(self.timer.get_progress() * 1000))

    def _update_timer(self):
        # Пауза під час перерви не закриває вікно
        if self.timer.state in (TimerState.BREAK, TimerState.PAUSED) and self.timer.time_left > 0:
            self._update_ring()
        else:
            self.close()

    def request_skip(self):
        """Запит на дострокове завершення перерви з підтвердженням"""
        box = MessageBox("Завершити перерву?", "Таймер одразу перейде до наступного кроку.", self.window)
        box.yesButton.setText("Завершити")
        box.cancelButton.setText("Відпочивати далі")
        if box.exec():
            self.confirm_skip()

    def confirm_skip(self):
        if self.on_skip_callback:
            self.on_skip_callback()
        self.close()

    def close(self):
        if not self.surfaces:
            return

        self.poll.stop()
        for surface in self.surfaces:
            surface.closing = True
            surface.close()
            surface.deleteLater()
        self.surfaces = []

        if self.on_close_callback:
            self.on_close_callback()
