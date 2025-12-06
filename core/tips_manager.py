# -*- coding: utf-8 -*-
"""
Менеджер порад для TomatoTimer
Відповідає за завантаження та вибір порад для перерв
"""

import json
import os
import random
from typing import List, Dict, Optional
from collections import deque


class TipsManager:
    def __init__(self, tips_file: str = None):
        """
        Ініціалізація менеджера порад

        Args:
            tips_file: Шлях до файлу з порадами
        """
        if tips_file is None:
            # Шлях за замовчуванням
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            tips_file = os.path.join(current_dir, "data", "tips.json")

        self.tips_file = tips_file
        self.tips: List[Dict] = []
        self.recent_tips: deque = deque(maxlen=5)  # Останні 5 показаних порад
        self.current_tip_index: int = 0

        # Завантажуємо поради
        self.load_tips()

    def load_tips(self):
        """Завантаження порад з файлу"""
        try:
            if os.path.exists(self.tips_file):
                with open(self.tips_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.tips = data.get('tips', [])

                if not self.tips:
                    # Якщо файл порожній, використовуємо базову пораду
                    self.tips = self._get_default_tips()
            else:
                # Файл не існує, створюємо з базовими порадами
                self.tips = self._get_default_tips()
                self._save_tips()

        except Exception as e:
            print(f"Помилка завантаження порад: {e}")
            self.tips = self._get_default_tips()

    def _save_tips(self):
        """Збереження порад у файл"""
        try:
            # Створюємо директорію, якщо не існує
            os.makedirs(os.path.dirname(self.tips_file), exist_ok=True)

            with open(self.tips_file, 'w', encoding='utf-8') as f:
                json.dump({"tips": self.tips}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Помилка збереження порад: {e}")

    def _get_default_tips(self) -> List[Dict]:
        """Отримання базових порад на випадок помилки"""
        return [
            {
                "id": 1,
                "title": "Розтяжка шиї",
                "description": "Акуратно нахиліть голову вправо, затримайтесь на 5 секунд, потім вліво.",
                "duration": "30 секунд"
            },
            {
                "id": 2,
                "title": "Обертання плечима",
                "description": "Зробіть 10 кругових рухів плечима вперед, потім 10 назад.",
                "duration": "40 секунд"
            },
            {
                "id": 3,
                "title": "Правило 20-20-20",
                "description": "Подивіться на об'єкт на відстані 6 метрів впродовж 20 секунд.",
                "duration": "20 секунд"
            }
        ]

    def get_random_tip(self) -> Dict:
        """
        Отримання випадкової поради (без повторення останніх 5)

        Returns:
            Dict: Порада з полями title, description, duration
        """
        if not self.tips:
            return self._get_default_tips()[0]

        # Створюємо список доступних порад (без нещодавно показаних)
        available_tips = [
            tip for tip in self.tips
            if tip.get('id') not in self.recent_tips
        ]

        # Якщо всі поради були показані, скидаємо історію
        if not available_tips:
            self.recent_tips.clear()
            available_tips = self.tips.copy()

        # Вибираємо випадкову пораду
        tip = random.choice(available_tips)

        # Додаємо до історії
        self.recent_tips.append(tip.get('id'))

        return tip

    def get_tip_by_index(self, index: int) -> Optional[Dict]:
        """
        Отримання поради за індексом

        Args:
            index: Індекс поради

        Returns:
            Dict або None
        """
        if 0 <= index < len(self.tips):
            return self.tips[index]
        return None

    def get_all_tips(self) -> List[Dict]:
        """Отримання всіх порад"""
        return self.tips.copy()

    def add_tip(self, title: str, description: str, duration: str = ""):
        """
        Додавання нової поради

        Args:
            title: Заголовок поради
            description: Опис поради
            duration: Тривалість виконання
        """
        new_id = max([tip.get('id', 0) for tip in self.tips], default=0) + 1

        new_tip = {
            "id": new_id,
            "title": title,
            "description": description,
            "duration": duration
        }

        self.tips.append(new_tip)
        self._save_tips()

    def remove_tip(self, tip_id: int) -> bool:
        """
        Видалення поради за ID

        Args:
            tip_id: ID поради

        Returns:
            bool: True якщо порада була видалена
        """
        original_length = len(self.tips)
        self.tips = [tip for tip in self.tips if tip.get('id') != tip_id]

        if len(self.tips) < original_length:
            self._save_tips()
            return True

        return False

    def format_tip(self, tip: Dict) -> str:
        """
        Форматування поради для відображення

        Args:
            tip: Порада

        Returns:
            str: Відформатований текст
        """
        title = tip.get('title', 'Порада')
        description = tip.get('description', '')
        duration = tip.get('duration', '')

        formatted = f"{title}\n\n{description}"

        if duration:
            formatted += f"\n\nТривалість: {duration}"

        return formatted

    def get_tips_count(self) -> int:
        """Отримання кількості порад"""
        return len(self.tips)
