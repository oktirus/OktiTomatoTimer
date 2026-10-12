# -*- coding: utf-8 -*-
"""
Тести менеджера конфігурації. Запуск: python -m unittest
"""

import json
import os
import shutil
import tempfile
import unittest

from config.default_settings import DEFAULT_SETTINGS
from utils.config_manager import ConfigManager


class ConfigManagerTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.file = os.path.join(self.dir, "settings.json")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def write(self, text):
        with open(self.file, "w", encoding="utf-8") as f:
            f.write(text)

    def read(self):
        with open(self.file, encoding="utf-8") as f:
            return json.load(f)

    def test_missing_file_creates_defaults(self):
        config = ConfigManager(self.dir)
        self.assertEqual(config.get_all(), DEFAULT_SETTINGS)
        self.assertEqual(self.read(), DEFAULT_SETTINGS)

    def test_corrupt_file_is_backed_up_not_overwritten(self):
        self.write("{broken")
        config = ConfigManager(self.dir)
        self.assertEqual(config.get_all(), DEFAULT_SETTINGS)
        with open(self.file + ".bak", encoding="utf-8") as f:
            self.assertEqual(f.read(), "{broken")

    def test_non_object_json_is_treated_as_corrupt(self):
        self.write("[1, 2]")
        config = ConfigManager(self.dir)
        self.assertEqual(config.get_all(), DEFAULT_SETTINGS)
        self.assertTrue(os.path.exists(self.file + ".bak"))

    def test_missing_keys_filled_and_user_values_kept(self):
        self.write(json.dumps({"work_duration": 50}))
        config = ConfigManager(self.dir)
        self.assertEqual(config.get("work_duration"), 50)
        self.assertEqual(config.get("long_break_duration"), DEFAULT_SETTINGS["long_break_duration"])

    def test_old_nonexistent_default_sounds_migrated(self):
        self.write(json.dumps({
            "work_end_sound": "default_work_end.wav",
            "break_end_sound": "C:/sounds/my.wav",
        }))
        config = ConfigManager(self.dir)
        self.assertEqual(config.get("work_end_sound"), "")
        self.assertEqual(config.get("break_end_sound"), "C:/sounds/my.wav")

    def test_legacy_dead_keys_removed_and_theme_follows_system(self):
        self.write(json.dumps({"language": "uk", "theme": "light", "track_statistics": True}))
        config = ConfigManager(self.dir)
        self.assertEqual(config.get("theme"), "auto")
        self.assertNotIn("language", config.get_all())
        self.assertNotIn("track_statistics", config.get_all())

    def test_user_theme_kept_in_new_config(self):
        self.write(json.dumps({"theme": "dark"}))
        self.assertEqual(ConfigManager(self.dir).get("theme"), "dark")

    def test_save_roundtrip_leaves_no_temp_file(self):
        config = ConfigManager(self.dir)
        config.set("work_duration", 42)
        self.assertEqual(ConfigManager(self.dir).get("work_duration"), 42)
        self.assertFalse(os.path.exists(self.file + ".tmp"))

    def test_update_without_save_does_not_touch_disk(self):
        config = ConfigManager(self.dir)
        config.update({"work_duration": 33}, save=False)
        self.assertEqual(self.read()["work_duration"], DEFAULT_SETTINGS["work_duration"])

    def test_failed_save_keeps_previous_file(self):
        config = ConfigManager(self.dir)
        config.set("work_duration", 30)
        config.settings["bad"] = object()  # не серіалізується в JSON
        self.assertFalse(config.save())
        self.assertEqual(self.read()["work_duration"], 30)
        self.assertFalse(os.path.exists(self.file + ".tmp"))


if __name__ == "__main__":
    unittest.main()
