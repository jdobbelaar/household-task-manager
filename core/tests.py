from datetime import date

from django.test import TestCase

from core import duedates
from core.models import Task


def make_task(**kwargs):
    """An unsaved Task with every recurrence field defaulted to None, overridden by kwargs."""
    defaults = {
        "name": "Test task",
        "recurrence_type": None,
        "every_days": None,
        "every_months": None,
        "every_years": None,
        "schedule": None,
        "day": None,
        "day_of_month": None,
        "month": None,
        "last_done": None,
        "last_note": None,
        "snooze_until": None,
    }
    defaults.update(kwargs)
    return Task(**defaults)


class IntervalDueDateTests(TestCase):
    def test_due_immediately_when_never_done(self):
        task = make_task(recurrence_type="interval", every_days=30, last_done=None)
        today = date(2026, 6, 15)
        self.assertEqual(duedates.compute_due_date(task, today), today)

    def test_every_days(self):
        task = make_task(recurrence_type="interval", every_days=180, last_done=date(2026, 3, 15))
        self.assertEqual(duedates.compute_due_date(task), date(2026, 9, 11))

    def test_every_months_is_calendar_correct(self):
        # Jan 31 + 1 month clamps to Feb 28 (2026 is not a leap year), not "Mar 3"
        task = make_task(recurrence_type="interval", every_months=1, last_done=date(2026, 1, 31))
        self.assertEqual(duedates.compute_due_date(task), date(2026, 2, 28))

    def test_every_years(self):
        task = make_task(recurrence_type="interval", every_years=1, last_done=date(2024, 11, 23))
        self.assertEqual(duedates.compute_due_date(task), date(2025, 11, 23))

    def test_overdue_when_past_due(self):
        task = make_task(recurrence_type="interval", every_days=10, last_done=date(2026, 1, 1))
        self.assertEqual(duedates.get_status(task, today=date(2026, 2, 1)), duedates.OVERDUE)


class FixedWeeklyDueDateTests(TestCase):
    def test_most_recent_occurrence_when_never_done(self):
        # 2026-09-05 is a Saturday; the most recent Monday on/before it is 2026-08-31
        task = make_task(recurrence_type="fixed", schedule="weekly", day="mon", last_done=None)
        self.assertEqual(duedates.compute_due_date(task, date(2026, 9, 5)), date(2026, 8, 31))

    def test_next_occurrence_once_current_one_is_done(self):
        task = make_task(recurrence_type="fixed", schedule="weekly", day="mon", last_done=date(2026, 8, 31))
        self.assertEqual(duedates.compute_due_date(task, date(2026, 9, 5)), date(2026, 9, 7))
        self.assertEqual(duedates.get_status(task, today=date(2026, 9, 5), lookahead_days=7), duedates.DUE_SOON)

    def test_overdue_when_occurrence_was_missed(self):
        task = make_task(recurrence_type="fixed", schedule="weekly", day="mon", last_done=date(2026, 8, 17))
        self.assertEqual(duedates.get_status(task, today=date(2026, 9, 5)), duedates.OVERDUE)


class FixedMonthlyDueDateTests(TestCase):
    def test_clamps_to_last_day_of_shorter_month(self):
        # day_of_month=31 in November (30 days): this month's occurrence clamps to Nov 30,
        # which hasn't happened yet by the 15th, so the most recent occurrence is Oct 31.
        task = make_task(recurrence_type="fixed", schedule="monthly", day_of_month=31, last_done=None)
        self.assertEqual(duedates.compute_due_date(task, date(2026, 11, 15)), date(2026, 10, 31))

    def test_next_occurrence_once_current_one_is_done(self):
        task = make_task(recurrence_type="fixed", schedule="monthly", day_of_month=1, last_done=date(2026, 8, 1))
        self.assertEqual(duedates.compute_due_date(task, date(2026, 8, 15)), date(2026, 9, 1))


class FixedYearlyDueDateTests(TestCase):
    def test_clamps_feb29_in_a_non_leap_year(self):
        task = make_task(recurrence_type="fixed", schedule="yearly", month=2, day_of_month=29, last_done=None)
        self.assertEqual(duedates.compute_due_date(task, date(2026, 6, 1)), date(2026, 2, 28))

    def test_falls_back_to_previous_year_before_this_years_occurrence(self):
        task = make_task(recurrence_type="fixed", schedule="yearly", month=11, day_of_month=1, last_done=None)
        self.assertEqual(duedates.compute_due_date(task, date(2026, 9, 5)), date(2025, 11, 1))


class SnoozeOverrideTests(TestCase):
    def test_snooze_overrides_an_interval_due_date(self):
        task = make_task(
            recurrence_type="interval", every_days=1, last_done=date(2020, 1, 1), snooze_until=date(2030, 1, 1)
        )
        self.assertEqual(duedates.effective_due_date(task, today=date(2026, 9, 5)), date(2030, 1, 1))
        self.assertEqual(duedates.get_status(task, today=date(2026, 9, 5)), duedates.NOT_DUE)

    def test_snooze_overrides_an_overdue_fixed_task(self):
        task = make_task(
            recurrence_type="fixed", schedule="yearly", month=1, day_of_month=1, last_done=None,
            snooze_until=date(2026, 9, 10),
        )
        self.assertEqual(duedates.get_status(task, today=date(2026, 9, 5), lookahead_days=7), duedates.DUE_SOON)

    def test_compute_due_date_ignores_snooze(self):
        # compute_due_date is the raw recurrence date; only effective_due_date/get_status apply snooze
        task = make_task(
            recurrence_type="interval", every_days=1, last_done=date(2020, 1, 1), snooze_until=date(2030, 1, 1)
        )
        self.assertNotEqual(duedates.compute_due_date(task, today=date(2026, 9, 5)), date(2030, 1, 1))


class StatusBucketBoundaryTests(TestCase):
    def test_due_today_boundary(self):
        task = make_task(recurrence_type="interval", every_days=1, last_done=None)
        self.assertEqual(duedates.get_status(task, today=date(2026, 9, 5)), duedates.DUE_TODAY)

    def test_due_soon_boundary_is_inclusive(self):
        # due date lands exactly lookahead_days away from today
        task = make_task(recurrence_type="interval", every_days=1, last_done=date(2026, 8, 29))
        self.assertEqual(duedates.get_status(task, today=date(2026, 8, 23), lookahead_days=7), duedates.DUE_SOON)

    def test_not_due_beyond_lookahead_window(self):
        task = make_task(recurrence_type="interval", every_days=30, last_done=date(2026, 9, 1))
        self.assertEqual(duedates.get_status(task, today=date(2026, 9, 5), lookahead_days=7), duedates.NOT_DUE)


class TaskModelMethodTests(TestCase):
    def test_model_methods_delegate_to_duedates(self):
        task = Task.objects.create(
            name="Delegation check", recurrence_type="interval", every_days=10, last_done=date(2026, 1, 1)
        )
        self.assertEqual(task.get_due_date(today=date(2026, 1, 20)), date(2026, 1, 11))
        self.assertEqual(task.get_status(today=date(2026, 1, 20)), duedates.OVERDUE)
