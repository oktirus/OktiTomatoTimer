# -*- coding: utf-8 -*-
"""
Інтеграційні тести вікон (PySide6, платформа offscreen: вікна не з'являються на екрані).
Трей, звук і слухач системної теми замінені заглушками. Запуск: python -m unittest
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import shutil
import tempfile
import unittest
from datetime import date
from unittest import mock

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication
from qfluentwidgets import Theme, qconfig, setTheme

from config.default_settings import DEFAULT_SETTINGS
from core.timer import TimerState
from utils.config_manager import ConfigManager

APP = QApplication.instance() or QApplication([])


class FakeTray:
    def __init__(self, *args, **kwargs):
        self.available = True
        self.notifications = []

    def start(self): pass
    def stop(self): pass
    def update_time(self, *args): pass
    def notify(self, message): self.notifications.append(message)
    def is_available(self): return self.available


class FakeSound:
    def __init__(self):
        self.played = []
        self.enabled = True
        self.volume = 50

    def test_sound(self, sound_file=None): self.played.append(sound_file)
    def set_volume(self, volume): self.volume = volume
    def get_volume(self): return self.volume
    def enable(self): self.enabled = True
    def disable(self): self.enabled = False
    def is_enabled(self): return self.enabled
    def supports_volume(self): return True
    def supported_extensions(self): return [".wav"]


def confirm(answer: bool):
    """Підміна MessageBox: діалог одразу повертає відповідь"""
    box = mock.MagicMock()
    box.return_value.exec.return_value = answer
    return box


class UiTestCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.config = ConfigManager(self.dir)
        # Вікно перерви у звичайному режимі, щоб тест не перекривав екрани
        self.config.set("fullscreen_break", False)
        self.apps = []

    def tearDown(self):
        with mock.patch("ui.main_window.QApplication.quit"):
            for app in self.apps:
                app.quit()
                app.deleteLater()
        # deleteLater поза циклом подій сам не спрацює, а живі вікна сповільнюють кожен setTheme
        APP.sendPostedEvents(None, QEvent.DeferredDelete)
        if qconfig.theme != Theme.LIGHT:
            setTheme(Theme.LIGHT)
        shutil.rmtree(self.dir, ignore_errors=True)

    def make_app(self):
        from ui.main_window import MainWindow
        with mock.patch("ui.main_window.TrayIcon", FakeTray), \
                mock.patch("ui.main_window.SoundManager", FakeSound), \
                mock.patch("ui.main_window.SystemThemeListener"):
            app = MainWindow(self.config)
        app.timer.work_duration = app.timer.break_duration = app.timer.long_break_duration = 5
        self.apps.append(app)
        return app


class MainWindowTest(UiTestCase):
    def setUp(self):
        super().setUp()
        self.app = self.make_app()
        self.timer = self.app.timer

    def finish_phase(self):
        """Доводить поточну фазу до кінця через справжній цикл таймера"""
        self.app._stop_timer_loop()
        self.timer.time_left = 1
        self.app._timer_loop()
        APP.processEvents()

    def test_idle_buttons(self):
        self.assertEqual(self.app.primary_button.text(), "Почати")
        self.assertGreaterEqual(self.app.primary_button.minimumWidth(), 200)
        self.assertEqual(self.app.primary_button.height(), 44)
        self.assertFalse(self.app.add_time_button.isEnabled())
        self.assertTrue(self.app.skip_to_break_button.isEnabled())
        self.assertFalse(self.app.reset_button.isEnabled())

    def test_tabs_switch_between_timer_and_settings(self):
        self.app.show()
        APP.processEvents()
        self.assertFalse(self.app.navigationInterface.isVisible())
        self.assertTrue(self.app.tabs.isVisible())
        self.assertEqual(self.app.tabs.currentRouteKey(), "timerPage")

        self.app.tabs.widget("settingsPage").click()
        APP.processEvents()
        self.assertIs(self.app.stackedWidget.currentWidget(), self.app.settings_page)
        self.assertEqual(self.app.tabs.currentRouteKey(), "settingsPage")

        self.app.tabs.widget("timerPage").click()
        APP.processEvents()
        self.assertIs(self.app.stackedWidget.currentWidget(), self.app.timer_page)

    def test_primary_button_starts_pauses_and_resumes(self):
        self.app.primary_button.click()
        self.assertEqual(self.timer.state, TimerState.WORK)
        self.assertEqual(self.app.primary_button.text(), "Пауза")
        self.assertTrue(self.app.tick_timer.isActive())

        self.app.primary_button.click()
        self.assertEqual(self.timer.state, TimerState.PAUSED)
        self.assertEqual(self.app.primary_button.text(), "Продовжити")
        self.assertFalse(self.app.tick_timer.isActive())

        self.app.primary_button.click()
        self.assertEqual(self.timer.state, TimerState.WORK)
        self.assertTrue(self.app.tick_timer.isActive())

    def test_ring_shows_time_and_progress(self):
        self.app.primary_button.click()
        self.timer.tick()
        ring = self.app.timer_page.ring
        self.assertEqual(ring.format(), self.timer.get_time_formatted())
        self.assertEqual(ring.value(), int(self.timer.get_progress() * 1000))

    def test_work_end_opens_break_and_counts_pomodoro(self):
        self.app.primary_button.click()
        self.finish_phase()
        self.assertEqual(self.timer.state, TimerState.BREAK)
        self.assertIsNotNone(self.app.break_window)
        self.assertEqual(ConfigManager(self.dir).get("completed_pomodoros"), 1)
        self.assertEqual(self.app.sound_manager.played, [None])
        self.assertFalse(self.app.skip_to_break_button.isEnabled())
        self.assertIn("1 помідор", self.app.timer_page.stats_label.text())

    def test_natural_break_end_goes_idle_with_sound(self):
        self.app.skip_to_break_button.click()
        self.timer.tick()
        self.assertEqual(self.app.sound_manager.played, [], "звук лише в кінці перерви")
        self.finish_phase()
        self.assertEqual(self.timer.state, TimerState.IDLE)
        self.assertIsNone(self.app.break_window)
        self.assertFalse(self.app.tick_timer.isActive())
        self.assertEqual(self.app.sound_manager.played, [None])

    def test_auto_start_keeps_timer_running(self):
        self.timer.set_auto_start_work(True)
        self.app.skip_to_break_button.click()
        self.finish_phase()
        self.assertEqual(self.timer.state, TimerState.WORK)
        self.assertTrue(self.app.tick_timer.isActive())
        self.assertEqual(self.app.primary_button.text(), "Пауза")

    def test_skip_from_work_counts_once(self):
        self.app.primary_button.click()
        self.app.skip_to_break_button.click()
        self.assertEqual(self.timer.completed_pomodoros, 1)
        self.assertEqual(self.config.get("completed_pomodoros"), 1)
        self.assertEqual(self.timer.state, TimerState.BREAK)

    def test_skip_from_idle_does_not_count(self):
        self.app.skip_to_break_button.click()
        self.assertEqual(self.timer.state, TimerState.BREAK)
        self.assertEqual(self.config.get("completed_pomodoros"), 0)
        self.assertEqual(self.app.sound_manager.played, [])

    def test_confirmed_skip_ends_break_silently(self):
        self.app.skip_to_break_button.click()
        with mock.patch("ui.break_window.MessageBox", confirm(True)):
            self.app.break_window.request_skip()
        self.assertEqual(self.timer.state, TimerState.IDLE)
        self.assertIsNone(self.app.break_window)
        self.assertEqual(self.app.sound_manager.played, [])

    def test_cancelled_skip_keeps_break(self):
        self.app.skip_to_break_button.click()
        with mock.patch("ui.break_window.MessageBox", confirm(False)):
            self.app.break_window.request_skip()
        self.assertEqual(self.timer.state, TimerState.BREAK)
        self.assertIsNotNone(self.app.break_window)

    def test_escape_and_close_request_confirmation(self):
        self.app.skip_to_break_button.click()
        surface = self.app.break_window.window
        with mock.patch.object(self.app.break_window, "request_skip") as request:
            surface.keyPressEvent(QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Escape, Qt.NoModifier))
            surface.close()
        self.assertEqual(request.call_count, 2)
        self.assertTrue(surface.isVisible())

    def test_fullscreen_break_covers_every_screen(self):
        self.config.set("fullscreen_break", True)
        self.app.skip_to_break_button.click()
        self.assertEqual(len(self.app.break_window.surfaces), len(APP.screens()))
        self.assertIs(self.app.break_window.window.screen(), APP.primaryScreen())

    def test_tips_hidden_when_disabled(self):
        self.config.set("show_tips", False)
        self.app.skip_to_break_button.click()
        self.assertIsNone(self.app.break_window.current_tip)

    def test_next_tip_changes_text(self):
        self.app.skip_to_break_button.click()
        window = self.app.break_window
        first = window.tip_title.text()
        for _ in range(5):
            window._show_next_tip()
            if window.tip_title.text() != first:
                break
        self.assertNotEqual(window.tip_title.text(), first)

    def test_sound_setting_applied(self):
        self.config.set("sound_enabled", False)
        self.app._on_settings_saved()
        self.assertFalse(self.app.sound_manager.is_enabled())

    def test_close_hides_to_tray_and_hints_once(self):
        self.app.show()
        self.app.close()
        self.app.close()
        self.assertFalse(self.app.isVisible())
        self.assertFalse(self.app._quitting)
        self.assertEqual(len(self.app.tray_icon.notifications), 1)

    def test_close_without_tray_quits(self):
        self.app.tray_icon.available = False
        with mock.patch("ui.main_window.QApplication.quit") as quit_app:
            self.app.close()
        quit_app.assert_called_once()


class StatsTest(UiTestCase):
    def test_new_day_resets_counter(self):
        self.config.update({"stats_date": "2000-01-01", "completed_pomodoros": 7})
        app = self.make_app()
        self.assertEqual(self.config.get("completed_pomodoros"), 0)
        self.assertIn("0 помідорів", app.timer_page.stats_label.text())

    def test_same_day_keeps_counter(self):
        self.config.update({"stats_date": date.today().isoformat(), "completed_pomodoros": 3})
        self.make_app()
        self.assertEqual(self.config.get("completed_pomodoros"), 3)

    def test_ukrainian_plural(self):
        from ui.main_window import pomodoros_text
        self.assertEqual([pomodoros_text(n) for n in (1, 2, 5, 11, 21, 22, 25)],
                         ["1 помідор", "2 помідори", "5 помідорів", "11 помідорів",
                          "21 помідор", "22 помідори", "25 помідорів"])


class SettingsPageTest(UiTestCase):
    def setUp(self):
        super().setUp()
        self.app = self.make_app()
        self.page = self.app.settings_page

    def test_change_is_saved_and_applied_immediately(self):
        self.page.controls["work_duration"](45)
        self.page.controls["auto_start_work"](True)
        self.assertEqual(ConfigManager(self.dir).get("work_duration"), 45)
        self.assertEqual(self.app.timer.work_duration, 45 * 60)
        self.assertTrue(self.app.timer.auto_start_work)
        self.assertEqual(self.app.timer_page.ring.format(), "45:00")

    def test_out_of_range_value_is_clamped(self):
        self.page.controls["work_duration"](500)
        self.assertEqual(self.config.get("work_duration"), 60)

    def test_load_does_not_write_config(self):
        with mock.patch.object(self.config, "set") as config_set:
            self.page.load({**DEFAULT_SETTINGS, "work_duration": 33})
        config_set.assert_not_called()

    def test_reset_requires_confirmation_and_keeps_stats(self):
        self.config.update({"work_duration": 40, "completed_pomodoros": 2})
        with mock.patch("ui.settings_page.MessageBox", confirm(False)):
            self.page._reset_to_defaults()
        self.assertEqual(self.config.get("work_duration"), 40)

        with mock.patch("ui.settings_page.MessageBox", confirm(True)), \
                mock.patch("core.autostart.AutostartManager"):
            self.page._reset_to_defaults()
        self.assertEqual(ConfigManager(self.dir).get("work_duration"), 25)
        self.assertEqual(self.config.get("completed_pomodoros"), 2)
        self.assertEqual(self.app.timer.work_duration, 25 * 60)

    def test_theme_choice_is_saved_and_applied(self):
        self.page.controls["theme"]("dark")
        self.assertEqual(self.config.get("theme"), "dark")
        self.assertEqual(qconfig.theme, Theme.DARK)

    @mock.patch("core.autostart.AutostartManager")
    def test_autostart_switch_updates_system(self, autostart):
        self.page.controls["autostart_enabled"](True)
        autostart.return_value.enable.assert_called_once()
        self.assertTrue(self.config.get("autostart_enabled"))


if __name__ == "__main__":
    unittest.main()
