# -*- coding: utf-8 -*-
"""
Сторінка налаштувань TomatoTimer. Як у налаштуваннях Windows 11, зміни застосовуються одразу
"""

import logging
import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog, QVBoxLayout, QWidget
from qfluentwidgets import (BodyLabel, ComboBox, FluentIcon, MessageBox, PushButton, PushSettingCard, ScrollArea,
                            SettingCard, SettingCardGroup, Slider, SpinBox, SwitchButton, Theme, TitleLabel,
                            setTheme)
from qfluentwidgets.components.widgets.switch_button import IndicatorPosition

from config.default_settings import DEFAULT_SETTINGS
from core.sound_manager import SoundManager
from utils.config_manager import ConfigManager

log = logging.getLogger(__name__)

THEMES = [("auto", "Як у системі", Theme.AUTO), ("light", "Світла", Theme.LIGHT), ("dark", "Темна", Theme.DARK)]
SYSTEM_SOUND = "Системний звук"


def apply_theme(key: str):
    setTheme(next((theme for k, _, theme in THEMES if k == key), Theme.AUTO))


class SettingsPage(ScrollArea):
    def __init__(self, config: ConfigManager, sound_manager: SoundManager, on_change=None, parent=None):
        """
        Args:
            config: Менеджер конфігурації
            sound_manager: Спільний менеджер звуку (для перевірки звуку і списку форматів)
            on_change: Колбек після будь-якої зміни (головне вікно застосовує нові значення)
        """
        super().__init__(parent)
        self.setObjectName("settingsPage")
        self.config = config
        self.sound_manager = sound_manager
        self.on_change = on_change
        self.controls = {}  # ключ налаштування -> функція, що показує значення в контролі
        self._loading = True  # контроли випускають сигнали ще під час створення

        self.view = QWidget(self)
        self.view.setObjectName("view")
        layout = QVBoxLayout(self.view)
        layout.setContentsMargins(36, 24, 36, 36)
        layout.setSpacing(24)
        layout.addWidget(TitleLabel("Налаштування", self.view))

        timer_group = SettingCardGroup("Таймер", self.view)
        timer_group.addSettingCard(self._spin_card(FluentIcon.STOP_WATCH, "Робота", "work_duration", 1, 60))
        timer_group.addSettingCard(self._spin_card(FluentIcon.CAFE, "Перерва", "break_duration", 1, 30))
        timer_group.addSettingCard(self._spin_card(FluentIcon.CALENDAR, "Довга перерва", "long_break_duration", 5, 60))
        timer_group.addSettingCard(self._spin_card(
            FluentIcon.SYNC, "Цикл", "pomodoros_until_long_break", 2, 10, " пом.",
            "Скільки помідорів до довгої перерви"))
        timer_group.addSettingCard(self._switch_card(
            FluentIcon.PLAY, "Автостарт роботи", "auto_start_work", "Починати роботу одразу після перерви"))
        layout.addWidget(timer_group)

        break_group = SettingCardGroup("Перерва", self.view)
        break_group.addSettingCard(self._switch_card(
            FluentIcon.FULL_SCREEN, "На весь екран", "fullscreen_break", "Інакше перерва відкривається у вікні"))
        break_group.addSettingCard(self._switch_card(
            FluentIcon.HEART, "Поради", "show_tips", "Вправи для розминки під час перерви"))
        layout.addWidget(break_group)

        sound_group = SettingCardGroup("Звук", self.view)
        sound_group.addSettingCard(self._switch_card(FluentIcon.VOLUME, "Звукові сигнали", "sound_enabled"))
        sound_group.addSettingCard(self._volume_card())
        sound_group.addSettingCard(self._sound_card("Кінець роботи", "work_end_sound"))
        sound_group.addSettingCard(self._sound_card("Кінець перерви", "break_end_sound"))
        layout.addWidget(sound_group)

        system_group = SettingCardGroup("Система", self.view)
        system_group.addSettingCard(self._switch_card(
            FluentIcon.POWER_BUTTON, "Автозапуск", "autostart_enabled", "Запускати разом з Windows",
            after=self._apply_autostart))
        system_group.addSettingCard(self._theme_card())
        reset_card = PushSettingCard("Скинути", FluentIcon.CANCEL, "Скинути налаштування",
                                     "Повернути всі значення за замовчуванням", self.view)
        reset_card.clicked.connect(self._reset_to_defaults)
        system_group.addSettingCard(reset_card)
        layout.addWidget(system_group)

        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.enableTransparentBackground()
        self.load(self.config.get_all())

    # --- Картки ---

    def _card(self, icon, title, content=None):
        return SettingCard(icon, title, content, self.view)

    def _add_control(self, card, widget):
        card.hBoxLayout.addWidget(widget, 0, Qt.AlignRight)
        card.hBoxLayout.addSpacing(16)

    def _spin_card(self, icon, title, key, minimum, maximum, suffix=" хв", content=None):
        card = self._card(icon, title, content)
        spin = SpinBox(card)
        spin.setRange(minimum, maximum)
        spin.setSuffix(suffix)
        spin.setFixedWidth(150)
        spin.valueChanged.connect(lambda value: self._set(key, value))
        self._add_control(card, spin)
        self.controls[key] = spin.setValue
        return card

    def _switch_card(self, icon, title, key, content=None, after=None):
        card = self._card(icon, title, content)
        switch = SwitchButton(card, IndicatorPosition.RIGHT)
        switch.setOnText("Увімкнено")
        switch.setOffText("Вимкнено")

        def changed(checked):
            self._set(key, checked)
            if after:
                after(checked)

        switch.checkedChanged.connect(changed)
        self._add_control(card, switch)
        self.controls[key] = switch.setChecked
        return card

    def _volume_card(self):
        supported = self.sound_manager.supports_volume()
        card = self._card(FluentIcon.MUSIC, "Гучність",
                          None if supported else "Працює лише з pygame; зараз звук іде через winsound")
        value_label = BodyLabel(card)
        slider = Slider(Qt.Horizontal, card)
        slider.setRange(0, 100)
        slider.setMinimumWidth(140)
        slider.setEnabled(supported)

        def changed(value):
            value_label.setText(f"{value}%")
            self._set("volume", value)

        slider.valueChanged.connect(changed)
        test = PushButton(FluentIcon.PLAY, "Перевірити", card)
        test.clicked.connect(self._test_sound)
        for widget in (value_label, slider, test):
            card.hBoxLayout.addWidget(widget, 0, Qt.AlignRight)
            card.hBoxLayout.addSpacing(12)
        card.hBoxLayout.addSpacing(4)
        self.controls["volume"] = lambda value: (slider.setValue(value), value_label.setText(f"{value}%"))
        return card

    def _sound_card(self, title, key):
        card = PushSettingCard("Вибрати файл", FluentIcon.MEGAPHONE, title, SYSTEM_SOUND, self.view)
        reset = PushButton("Системний", card)
        card.hBoxLayout.insertWidget(card.hBoxLayout.count() - 2, reset, 0, Qt.AlignRight)
        card.hBoxLayout.insertSpacing(card.hBoxLayout.count() - 2, 8)

        def show(path):
            card.setContent(os.path.basename(path) if path else SYSTEM_SOUND)
            card.setToolTip(path or "")

        def choose():
            patterns = " ".join(f"*{ext}" for ext in self.sound_manager.supported_extensions())
            path, _ = QFileDialog.getOpenFileName(self, f"Звук: {title.lower()}", "", f"Звукові файли ({patterns})")
            if path:
                self._set(key, path)
                show(path)

        def use_system():
            self._set(key, "")
            show("")

        card.clicked.connect(choose)
        reset.clicked.connect(use_system)
        self.controls[key] = show
        return card

    def _theme_card(self):
        card = self._card(FluentIcon.BRUSH, "Тема")
        combo = ComboBox(card)
        combo.addItems([label for _, label, _ in THEMES])
        combo.setFixedWidth(150)

        def changed(index):
            key = THEMES[index][0]
            self._set("theme", key)
            apply_theme(key)

        combo.currentIndexChanged.connect(changed)
        self._add_control(card, combo)
        self.controls["theme"] = lambda key: combo.setCurrentIndex(
            next((i for i, (k, _, _) in enumerate(THEMES) if k == key), 0))
        return card

    # --- Дії ---

    def load(self, values: dict):
        """Показати значення у контролах (без повторного збереження)"""
        self._loading = True
        try:
            for key, setter in self.controls.items():
                setter(values.get(key, DEFAULT_SETTINGS.get(key)))
        finally:
            self._loading = False

    def _set(self, key, value):
        if self._loading:
            return
        self.config.set(key, value)
        if self.on_change:
            self.on_change()

    def _apply_autostart(self, enabled: bool):
        if self._loading:
            return
        try:
            from core.autostart import AutostartManager
            autostart = AutostartManager()
            autostart.enable() if enabled else autostart.disable()
        except Exception:
            log.exception("Помилка налаштування автозапуску")

    def _test_sound(self):
        sound = self.config.get("work_end_sound") or None
        self.sound_manager.test_sound(sound)

    def _reset_to_defaults(self):
        box = MessageBox("Скинути налаштування?",
                         "Усі значення повернуться до стандартних. Статистика за сьогодні збережеться.",
                         self.window())
        box.yesButton.setText("Скинути")
        box.cancelButton.setText("Скасувати")
        if not box.exec():
            return

        stats = {key: self.config.get(key) for key in ("stats_date", "completed_pomodoros")}
        self.config.update({**DEFAULT_SETTINGS, **stats})
        self.load(self.config.get_all())
        apply_theme(self.config.get("theme"))
        self._apply_autostart(self.config.get("autostart_enabled"))
        if self.on_change:
            self.on_change()
