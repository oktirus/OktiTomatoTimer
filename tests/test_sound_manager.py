# -*- coding: utf-8 -*-
"""
Тести менеджера звуку (без реального відтворення). Запуск: python -m unittest
"""

import unittest
from unittest import mock

from core.sound_manager import SoundManager


def make_manager(library: str) -> SoundManager:
    with mock.patch.object(SoundManager, "_init_sound_library"):
        manager = SoundManager()
    manager.sound_library = library
    return manager


class SoundManagerTest(unittest.TestCase):
    def test_disabled_manager_plays_nothing(self):
        manager = make_manager("system")
        manager.disable()
        with mock.patch.object(manager, "_play_system_beep") as beep, \
                mock.patch.object(manager, "play_sound") as play:
            manager.test_sound()
            manager.test_sound("file.wav")
        beep.assert_not_called()
        play.assert_not_called()

    def test_enabled_manager_beeps_without_file(self):
        manager = make_manager("system")
        with mock.patch.object(manager, "_play_system_beep") as beep:
            manager.test_sound(None)
        beep.assert_called_once()

    def test_capabilities_per_backend(self):
        self.assertEqual(make_manager("system").supported_extensions(), [".wav"])
        self.assertFalse(make_manager("system").supports_volume())
        self.assertIn(".mp3", make_manager("pygame").supported_extensions())
        self.assertTrue(make_manager("pygame").supports_volume())

    def test_volume_is_clamped(self):
        manager = make_manager("system")
        manager.set_volume(150)
        self.assertEqual(manager.get_volume(), 100)
        manager.set_volume(-5)
        self.assertEqual(manager.get_volume(), 0)


if __name__ == "__main__":
    unittest.main()
