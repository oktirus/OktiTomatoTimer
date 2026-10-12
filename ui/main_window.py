# -*- coding: utf-8 -*-
"""
Головне вікно TomatoTimer (PySide6 + Fluent Widgets)
"""

import time
from datetime import date

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (BodyLabel, CaptionLabel, FluentIcon, FluentWindow, PrimaryPushButton,
                            ProgressRing, SegmentedWidget, SubtitleLabel, SystemThemeListener,
                            TransparentPushButton)

from core.sound_manager import SoundManager
from core.timer import PomodoroTimer, TimerState
from core.tips_manager import TipsManager
from ui.settings_page import SettingsPage
from ui.style import digits_font, phase_colors
from ui.tray_icon import TrayIcon, app_icon
from utils.config_manager import ConfigManager


def pomodoros_text(count: int) -> str:
    """Українська множина: 1 помідор, 2 помідори, 5 помідорів"""
    if count % 10 == 1 and count % 100 != 11:
        word = "помідор"
    elif count % 10 in (2, 3, 4) and count % 100 not in (12, 13, 14):
        word = "помідори"
    else:
        word = "помідорів"
    return f"{count} {word}"


class TimerPage(QWidget):
    """Сторінка таймера: кільце з часом, головна дія і другорядні дії"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("timerPage")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)

        self.ring = ProgressRing(self, useAni=False)
        self.ring.setFixedSize(240, 240)
        self.ring.setStrokeWidth(10)
        self.ring.setRange(0, 1000)
        self.ring.setTextVisible(True)
        self.ring.setFont(digits_font(56))
        layout.addWidget(self.ring, 0, Qt.AlignHCenter)

        self.state_label = SubtitleLabel(self)
        layout.addWidget(self.state_label, 0, Qt.AlignHCenter)

        self.cycle_label = CaptionLabel(self)
        self.cycle_label.setTextColor("#6E6E6E", "#A0A0A0")
        layout.addWidget(self.cycle_label, 0, Qt.AlignHCenter)
        layout.addSpacing(12)

        self.primary_button = PrimaryPushButton(FluentIcon.PLAY, "Почати", self)
        self.primary_button.setMinimumWidth(200)
        self.primary_button.setFixedHeight(44)
        layout.addWidget(self.primary_button, 0, Qt.AlignHCenter)

        actions = QHBoxLayout()
        actions.setSpacing(4)
        self.add_time_button = TransparentPushButton(FluentIcon.ADD, "1 хв", self)
        self.skip_to_break_button = TransparentPushButton(FluentIcon.CAFE, "Перерва", self)
        self.reset_button = TransparentPushButton(FluentIcon.RETURN, "Скинути", self)
        for button in (self.add_time_button, self.skip_to_break_button, self.reset_button):
            actions.addWidget(button)
        layout.addLayout(actions)
        layout.addSpacing(12)

        self.stats_label = BodyLabel(self)
        layout.addWidget(self.stats_label, 0, Qt.AlignHCenter)


class MainWindow(FluentWindow):
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config = config_manager

        self.setWindowTitle("TomatoTimer")
        self.setWindowIcon(app_icon())
        self.resize(580, 640)
        self.setMinimumSize(500, 580)

        self.timer = PomodoroTimer(
            self.config.get("work_duration"),
            self.config.get("break_duration"),
            self.config.get("long_break_duration"),
            self.config.get("pomodoros_until_long_break"),
            self.config.get("auto_start_work"),
        )
        self.sound_manager = SoundManager()
        self.tips_manager = TipsManager()
        self._apply_sound_settings()

        self.break_window = None
        self._quitting = False
        self._tray_hint_shown = False

        # Тік раз на секунду; затримка рахується від годинника, тож похибка не накопичується
        self.tick_timer = QTimer(self)
        self.tick_timer.setSingleShot(True)
        self.tick_timer.setTimerType(Qt.PreciseTimer)
        self.tick_timer.timeout.connect(self._timer_loop)
        self._next_tick_at = 0.0

        self.tray_icon = TrayIcon("TomatoTimer", on_click=self._show_window, on_exit=self.quit, parent=self)
        self.tray_icon.start()

        self.theme_listener = SystemThemeListener(self)
        self.theme_listener.start()

        self.timer_page = TimerPage(self)
        self.settings_page = SettingsPage(self.config, self.sound_manager, self._on_settings_saved, self)
        self.navigationInterface.setReturnButtonVisible(False)  # сторінок лише дві, історія не потрібна
        self.addSubInterface(self.timer_page, FluentIcon.STOP_WATCH, "Таймер")
        self.addSubInterface(self.settings_page, FluentIcon.SETTING, "Налаштування")
        self.navigationInterface.hide()
        self.titleBar.hBoxLayout.setContentsMargins(16, 0, 0, 0)

        self.tabs = SegmentedWidget(self)
        self.tabs.addItem("timerPage", "Таймер", icon=FluentIcon.STOP_WATCH)
        self.tabs.addItem("settingsPage", "Налаштування", icon=FluentIcon.SETTING)
        self.tabs.setCurrentItem("timerPage")
        self.tabs.currentItemChanged.connect(self._switch_tab)
        self.stackedWidget.currentChanged.connect(
            lambda index: self.tabs.setCurrentItem(self.stackedWidget.widget(index).objectName()))

        tabs_row = QHBoxLayout()
        tabs_row.setContentsMargins(0, 8, 0, 4)
        tabs_row.addStretch()
        tabs_row.addWidget(self.tabs)
        tabs_row.addStretch()
        content = QVBoxLayout()
        content.setSpacing(0)
        content.setContentsMargins(0, 0, 0, 0)
        content.addLayout(tabs_row)
        self.widgetLayout.removeWidget(self.stackedWidget)
        content.addWidget(self.stackedWidget, 1)
        self.widgetLayout.addLayout(content)

        page = self.timer_page
        self.primary_button = page.primary_button
        self.add_time_button = page.add_time_button
        self.skip_to_break_button = page.skip_to_break_button
        self.reset_button = page.reset_button
        self.primary_button.clicked.connect(self._on_primary_click)
        self.add_time_button.clicked.connect(self._on_add_time_click)
        self.skip_to_break_button.clicked.connect(self._on_skip_to_break_click)
        self.reset_button.clicked.connect(self._on_reset_click)

        self._setup_timer_callbacks()
        self._reset_stats_if_new_day()
        self._update_display()

    def _switch_tab(self, route_key: str):
        page = self.timer_page if route_key == "timerPage" else self.settings_page
        self.switchTo(page)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.titleBar.setGeometry(0, 0, self.width(), self.titleBar.height())

    def _setup_timer_callbacks(self):
        self.timer.on_tick = self._on_timer_tick
        self.timer.on_work_end = self._on_work_end
        self.timer.on_break_start = self._on_break_start
        self.timer.on_break_end = self._on_break_end
        self.timer.on_state_change = self._on_state_change

    # --- Дії ---

    def _on_primary_click(self):
        """Почати / пауза / продовжити"""
        if self.timer.state == TimerState.IDLE:
            self.timer.start_work()
            self._start_timer_loop()
        elif self.timer.is_running():
            self.timer.pause()
            self._stop_timer_loop()
        else:
            self.timer.resume()
            self._start_timer_loop()

    def _on_reset_click(self):
        self._stop_timer_loop()
        self.timer.reset()

    def _on_add_time_click(self):
        self.timer.add_time(60)

    def _on_skip_to_break_click(self):
        if self.timer.state == TimerState.WORK:
            self.timer.complete_work()
        elif self.timer.state == TimerState.IDLE:
            self.timer.start_break()
        self._start_timer_loop()

    def _on_settings_saved(self):
        """Застосування налаштувань (нові тривалості діють з наступної фази)"""
        self.timer.set_work_duration(self.config.get("work_duration"))
        self.timer.set_break_duration(self.config.get("break_duration"))
        self.timer.set_long_break_duration(self.config.get("long_break_duration"))
        self.timer.set_pomodoros_until_long_break(self.config.get("pomodoros_until_long_break"))
        self.timer.set_auto_start_work(self.config.get("auto_start_work"))
        self._apply_sound_settings()
        self._update_display()

    def _apply_sound_settings(self):
        self.sound_manager.set_volume(self.config.get("volume"))
        if self.config.get("sound_enabled"):
            self.sound_manager.enable()
        else:
            self.sound_manager.disable()

    # --- Цикл таймера ---

    def _start_timer_loop(self):
        if not self.tick_timer.isActive() and self.timer.is_running():
            self._next_tick_at = time.monotonic() + 1
            self.tick_timer.start(1000)

    def _stop_timer_loop(self):
        self.tick_timer.stop()

    def _timer_loop(self):
        if not self.timer.is_running():
            return

        self.timer.tick()

        # Колбеки всередині tick() могли вже запустити новий цикл
        if self.timer.is_running() and not self.tick_timer.isActive():
            self._next_tick_at += 1
            self.tick_timer.start(max(0, int((self._next_tick_at - time.monotonic()) * 1000)))

    # --- Колбеки таймера ---

    def _on_timer_tick(self, time_left: int):
        # Звук кінця перерви — лише коли вона дійшла до нуля, а не завершена вручну
        if time_left == 0 and self.timer.state == TimerState.BREAK:
            self.sound_manager.test_sound(self.config.get("break_end_sound") or None)
        self._update_display()

    def _on_work_end(self):
        self.sound_manager.test_sound(self.config.get("work_end_sound") or None)
        self._add_pomodoro_to_stats()

    def _on_break_start(self):
        from ui.break_window import BreakWindow
        if self.break_window:
            self.break_window.close()
        self.break_window = BreakWindow(
            self,
            self.timer,
            self.tips_manager,
            on_close_callback=self._on_break_window_closed,
            on_skip_callback=self.timer.finish_break,
            fullscreen=self.config.get("fullscreen_break"),
            show_tips=self.config.get("show_tips"),
        )

    def _on_break_end(self):
        """Таймер уже в IDLE або WORK"""
        if self.break_window:
            self.break_window.close()
        self._start_timer_loop()

    def _on_break_window_closed(self):
        self.break_window = None

    def _on_state_change(self, state: TimerState):
        self._update_display()

    # --- Вікно і трей ---

    def _show_window(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        """Хрестик згортає в трей, якщо він доступний"""
        if self._quitting or not self.tray_icon.is_available():
            self._shutdown()
            event.accept()
            QApplication.quit()
            return

        event.ignore()
        self.hide()
        if not self._tray_hint_shown:
            self.tray_icon.notify("TomatoTimer працює у треї. Вийти можна через меню іконки.")
            self._tray_hint_shown = True

    def quit(self):
        """Повне завершення програми"""
        self._quitting = True
        self.close()

    def _shutdown(self):
        self._stop_timer_loop()
        if self.break_window:
            self.break_window.close()
        self.tray_icon.stop()
        self.theme_listener.terminate()
        self.theme_listener.wait(1000)

    # --- Статистика ---

    def _reset_stats_if_new_day(self):
        today = date.today().isoformat()
        if self.config.get("stats_date") != today:
            self.config.update({"stats_date": today, "completed_pomodoros": 0})

    def _add_pomodoro_to_stats(self):
        self._reset_stats_if_new_day()
        self.config.set("completed_pomodoros", self.config.get("completed_pomodoros", 0) + 1)

    # --- Відображення ---

    def _update_display(self):
        state = self.timer.state
        page = self.timer_page

        if state == TimerState.IDLE:
            state_text = "Готовий до роботи"
            time_text = f"{self.config.get('work_duration'):02d}:00"
        else:
            time_text = self.timer.get_time_formatted()
            if state == TimerState.WORK:
                state_text = "Робота"
            elif state == TimerState.BREAK:
                state_text = "Довга перерва" if self.timer.is_long_break else "Перерва"
            else:
                state_text = "Пауза"

        progress = self.timer.get_progress()
        page.ring.setCustomBarColor(*phase_colors(self.timer._previous_state if state == TimerState.PAUSED else state))
        page.ring.setFormat(time_text)
        page.ring.setValue(int(progress * 1000))
        page.state_label.setText(state_text)

        every = self.timer.pomodoros_until_long_break
        left = every - self.timer.completed_pomodoros % every
        page.cycle_label.setText(f"До довгої перерви: {pomodoros_text(left)}")
        page.stats_label.setText(f"Сьогодні: {pomodoros_text(self.config.get('completed_pomodoros', 0))}")

        self._update_buttons()

        mode = {TimerState.WORK: "work", TimerState.BREAK: "break"}.get(state, "idle")
        self.tray_icon.update_time(time_text, progress, mode)

    def _update_buttons(self):
        """Стан кнопок визначається лише станом таймера"""
        state = self.timer.state
        if state == TimerState.IDLE:
            self.primary_button.setText("Почати")
            self.primary_button.setIcon(FluentIcon.PLAY)
        elif state == TimerState.PAUSED:
            self.primary_button.setText("Продовжити")
            self.primary_button.setIcon(FluentIcon.PLAY)
        else:
            self.primary_button.setText("Пауза")
            self.primary_button.setIcon(FluentIcon.PAUSE)

        self.add_time_button.setEnabled(self.timer.is_running())
        self.skip_to_break_button.setEnabled(state in (TimerState.IDLE, TimerState.WORK))
        self.reset_button.setEnabled(state != TimerState.IDLE)
