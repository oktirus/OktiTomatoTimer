# -*- coding: utf-8 -*-
"""
Іконка TomatoTimer у системному треї (QSystemTrayIcon)
"""

import logging

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QIcon, QPainter, QPen, QPixmap, QColor
from PySide6.QtWidgets import QSystemTrayIcon
from qfluentwidgets import Action, FluentIcon, SystemTrayMenu

log = logging.getLogger(__name__)

MODE_COLORS = {"work": "#E5483B", "break": "#3FAE6C", "idle": "#FFFFFF"}


def ring_icon(progress: float, mode: str) -> QIcon:
    """Іконка-кільце: сірий фон і кольорова дуга прогресу фази"""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    rect = QRectF(6, 6, 52, 52)

    painter.setPen(QPen(QColor(255, 255, 255, 110), 8))
    painter.drawEllipse(rect)
    if progress > 0:
        painter.setPen(QPen(QColor(MODE_COLORS.get(mode, "#FFFFFF")), 8, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(rect, 90 * 16, -int(360 * 16 * progress))
    elif mode == "idle":
        painter.setBrush(QColor(MODE_COLORS["work"]))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(20, 20, 24, 24))

    painter.end()
    return QIcon(pixmap)


def app_icon() -> QIcon:
    """Іконка застосунку: томат із листочком"""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor("#D9412F"))
    painter.drawEllipse(QRectF(6, 12, 52, 48))
    painter.setBrush(QColor("#3C8C4E"))
    painter.drawEllipse(QRectF(22, 4, 20, 14))
    painter.end()
    return QIcon(pixmap)


class TrayIcon:
    """Обгортка над QSystemTrayIcon з тим самим інтерфейсом, що й раніше"""

    def __init__(self, app_name="TomatoTimer", on_click=None, on_exit=None, parent=None):
        self.app_name = app_name
        self.on_click = on_click
        self.on_exit = on_exit
        self.icon = None

        if not QSystemTrayIcon.isSystemTrayAvailable():
            log.info("Системний трей недоступний")
            return

        self.icon = QSystemTrayIcon(ring_icon(0.0, "idle"), parent)
        self.icon.setToolTip(app_name)

        self.menu = SystemTrayMenu(parent=parent)
        self.menu.addActions([
            Action(FluentIcon.HOME, "Відкрити", triggered=self._on_open),
            Action(FluentIcon.CLOSE, "Вийти", triggered=self._on_exit),
        ])
        self.icon.setContextMenu(self.menu)
        self.icon.activated.connect(self._on_activated)

    def start(self):
        if self.icon:
            self.icon.show()
            log.info("Іконка в треї запущена")

    def stop(self):
        if self.icon:
            self.icon.hide()

    def is_available(self) -> bool:
        """Чи працює іконка в треї (є куди згорнути вікно)"""
        return self.icon is not None

    def update_time(self, time_text, progress=0.0, mode="idle"):
        if self.icon:
            self.icon.setIcon(ring_icon(progress, mode))
            self.icon.setToolTip(f"{self.app_name}: {time_text}")

    def notify(self, message: str):
        if self.icon:
            self.icon.showMessage(self.app_name, message, QSystemTrayIcon.Information, 4000)

    def _on_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self._on_open()

    def _on_open(self):
        if self.on_click:
            self.on_click()

    def _on_exit(self):
        self.stop()
        if self.on_exit:
            self.on_exit()
