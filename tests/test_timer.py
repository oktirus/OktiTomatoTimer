# -*- coding: utf-8 -*-
"""
Тести логіки таймера. Запуск: python -m unittest
"""

import unittest

from core.timer import PomodoroTimer, TimerState


def run_phase(timer: PomodoroTimer) -> int:
    """Тікає до завершення поточної фази, повертає кількість тіків"""
    phase, ticks = timer.state, 0
    while timer.state == phase:
        timer.tick()
        ticks += 1
    return ticks


class PomodoroTimerTest(unittest.TestCase):
    def test_long_break_after_every_nth_pomodoro(self):
        timer = PomodoroTimer(1, 1, 3, pomodoros_until_long_break=4)
        breaks = []
        for _ in range(8):
            timer.start_work()
            run_phase(timer)
            breaks.append("L" if timer.is_long_break else "s")
        self.assertEqual("".join(breaks), "sssLsssL")
        self.assertEqual(timer.completed_pomodoros, 8)

    def test_phase_lasts_exactly_its_duration(self):
        timer = PomodoroTimer(25, 5)
        timer.start_work()
        self.assertEqual(run_phase(timer), 25 * 60)
        self.assertEqual(timer.state, TimerState.BREAK)
        self.assertEqual(run_phase(timer), 5 * 60)
        self.assertEqual(timer.state, TimerState.IDLE)

    def test_pause_in_break_resumes_break(self):
        timer = PomodoroTimer()
        timer.start_break()
        timer.pause()
        timer.resume()
        self.assertEqual(timer.state, TimerState.BREAK)

    def test_pause_in_work_resumes_work(self):
        timer = PomodoroTimer()
        timer.start_work()
        timer.pause()
        self.assertFalse(timer.tick())
        timer.resume()
        self.assertEqual(timer.state, TimerState.WORK)

    def test_progress_uses_current_phase_duration(self):
        timer = PomodoroTimer(1, 1, 10)
        timer.start_break(long_break=True)
        self.assertEqual(timer.get_progress(), 0.0)
        timer.tick()
        self.assertAlmostEqual(timer.get_progress(), 1 / 600)

    def test_progress_stays_in_range_after_add_time(self):
        timer = PomodoroTimer(1)
        timer.start_work()
        timer.add_time(60)
        self.assertGreaterEqual(timer.get_progress(), 0.0)
        run_phase(timer)
        self.assertEqual(timer.state, TimerState.BREAK)

    def test_complete_work_counts_once(self):
        timer = PomodoroTimer()
        timer.start_work()
        timer.complete_work()
        self.assertEqual(timer.completed_pomodoros, 1)
        self.assertEqual(timer.state, TimerState.BREAK)

    def test_break_from_idle_does_not_count_pomodoro(self):
        timer = PomodoroTimer()
        timer.start_break()
        self.assertEqual(timer.completed_pomodoros, 0)
        self.assertFalse(timer.is_long_break)

    def test_auto_start_work_listener_sees_work_state(self):
        timer = PomodoroTimer(1, 1, auto_start_work=True)
        seen = []
        timer.on_break_end = lambda: seen.append(timer.state)
        timer.start_break()
        run_phase(timer)
        self.assertEqual(seen, [TimerState.WORK])

    def test_break_end_without_auto_start_goes_idle(self):
        timer = PomodoroTimer(1, 1)
        seen = []
        timer.on_break_end = lambda: seen.append(timer.state)
        timer.start_break()
        timer.finish_break()
        self.assertEqual(seen, [TimerState.IDLE])

    def test_break_start_listener_sees_break_state(self):
        timer = PomodoroTimer()
        seen = []
        timer.on_break_start = lambda: seen.append(timer.state)
        timer.start_break()
        self.assertEqual(seen, [TimerState.BREAK])


if __name__ == "__main__":
    unittest.main()
