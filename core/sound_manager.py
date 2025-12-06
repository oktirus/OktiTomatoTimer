# -*- coding: utf-8 -*-
"""
Менеджер звуку для TomatoTimer
Відповідає за відтворення звукових сигналів
"""

import os
import platform
from typing import Optional


class SoundManager:
    def __init__(self):
        """Ініціалізація менеджера звуку"""
        self.volume = 50  # 0-100
        self.enabled = True
        self.current_sound_file = None

        # Визначаємо директорію зі звуками
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sounds_dir = os.path.join(current_dir, "data", "sounds")

        # Створюємо директорію, якщо не існує
        os.makedirs(self.sounds_dir, exist_ok=True)

        # Ініціалізуємо бібліотеку для відтворення звуку
        self._init_sound_library()

    def _init_sound_library(self):
        """Ініціалізація бібліотеки для відтворення звуку"""
        # Пріоритет: pygame > playsound > system
        try:
            # Спробуємо використати pygame
            import pygame
            pygame.mixer.init()
            self.sound_library = 'pygame'
            print("[ЗВУК] Використовується: pygame")
        except ImportError:
            try:
                # Спробуємо playsound як альтернативу
                import playsound
                self.sound_library = 'playsound'
                print("[ЗВУК] Використовується: playsound")
            except ImportError:
                # Використовуємо системні звуки
                self.sound_library = 'system'
                print("[ЗВУК] Використовується: системний (winsound/afplay/beep)")

    def play_sound(self, sound_file: str):
        """
        Відтворення звукового файлу

        Args:
            sound_file: Ім'я файлу або повний шлях
        """
        if not self.enabled:
            return

        # Якщо передано лише ім'я файлу, додаємо шлях до директорії звуків
        if not os.path.isabs(sound_file):
            sound_path = os.path.join(self.sounds_dir, sound_file)
        else:
            sound_path = sound_file

        # Перевіряємо існування файлу
        if not os.path.exists(sound_path):
            print(f"Звуковий файл не знайдено: {sound_path}")
            # Відтворюємо системний сигнал
            self._play_system_beep()
            return

        try:
            if self.sound_library == 'pygame':
                self._play_with_pygame(sound_path)
            elif self.sound_library == 'playsound':
                self._play_with_playsound(sound_path)
            else:
                self._play_with_winsound(sound_path)
        except Exception as e:
            print(f"Помилка відтворення звуку: {e}")
            self._play_system_beep()

    def _play_with_pygame(self, sound_path: str):
        """Відтворення звуку через pygame"""
        import pygame

        try:
            sound = pygame.mixer.Sound(sound_path)
            # Встановлюємо гучність (0.0 - 1.0)
            sound.set_volume(self.volume / 100.0)
            sound.play()
        except Exception as e:
            print(f"Помилка pygame: {e}")
            self._play_system_beep()

    def _play_with_playsound(self, sound_path: str):
        """Відтворення звуку через playsound"""
        try:
            from playsound import playsound
            # playsound не підтримує регулювання гучності
            # але простий у використанні
            playsound(sound_path, block=False)
        except Exception as e:
            print(f"Помилка playsound: {e}")
            self._play_system_beep()

    def _play_with_winsound(self, sound_path: str):
        """Відтворення звуку через winsound (Windows, тільки .wav)"""
        import winsound

        try:
            # winsound підтримує тільки .wav файли
            if sound_path.lower().endswith('.wav'):
                winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                # Для інших форматів - системний сигнал
                self._play_system_beep()
        except Exception as e:
            print(f"Помилка winsound: {e}")
            self._play_system_beep()

    def _play_system_beep(self):
        """Відтворення системного сигналу"""
        system = platform.system()

        try:
            if system == 'Windows':
                import winsound
                # Відтворюємо системний звук
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            elif system == 'Darwin':  # macOS
                os.system('afplay /System/Library/Sounds/Glass.aiff')
            else:  # Linux
                os.system('paplay /usr/share/sounds/freedesktop/stereo/complete.oga 2>/dev/null || beep')
        except Exception as e:
            print(f"Помилка відтворення системного сигналу: {e}")

    def set_volume(self, volume: int):
        """
        Встановлення гучності

        Args:
            volume: Гучність від 0 до 100
        """
        self.volume = max(0, min(100, volume))

    def get_volume(self) -> int:
        """Отримання поточної гучності"""
        return self.volume

    def enable(self):
        """Увімкнення звуку"""
        self.enabled = True

    def disable(self):
        """Вимкнення звуку"""
        self.enabled = False

    def toggle(self):
        """Перемикання звуку"""
        self.enabled = not self.enabled

    def is_enabled(self) -> bool:
        """Перевірка чи увімкнений звук"""
        return self.enabled

    def test_sound(self, sound_file: str = None):
        """
        Тестування звуку

        Args:
            sound_file: Файл для тестування (якщо None, використовується системний сигнал)
        """
        if sound_file:
            self.play_sound(sound_file)
        else:
            self._play_system_beep()

    def get_available_sounds(self) -> list:
        """Отримання списку доступних звукових файлів"""
        try:
            if os.path.exists(self.sounds_dir):
                # Фільтруємо лише звукові файли
                sound_extensions = ['.wav', '.mp3', '.ogg', '.aiff']
                files = [
                    f for f in os.listdir(self.sounds_dir)
                    if os.path.splitext(f)[1].lower() in sound_extensions
                ]
                return sorted(files)
        except Exception as e:
            print(f"Помилка читання директорії звуків: {e}")

        return []

    def add_sound_file(self, source_path: str, name: str = None) -> bool:
        """
        Додавання нового звукового файлу

        Args:
            source_path: Шлях до вихідного файлу
            name: Нове ім'я файлу (якщо None, використовується оригінальне)

        Returns:
            bool: True якщо файл успішно додано
        """
        try:
            import shutil

            if not os.path.exists(source_path):
                print(f"Файл не знайдено: {source_path}")
                return False

            if name is None:
                name = os.path.basename(source_path)

            dest_path = os.path.join(self.sounds_dir, name)
            shutil.copy2(source_path, dest_path)
            return True

        except Exception as e:
            print(f"Помилка додавання звукового файлу: {e}")
            return False
