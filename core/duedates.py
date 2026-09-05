"""Due-date calculation for Task, per the rules in _docs/plan.md.

Kept free of any dependency on models.py (recurrence/schedule values are matched as plain
strings, matching the TextChoices values on Task) so it can be unit tested in isolation.
"""

import calendar
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

WEEKDAY_INDEX = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}

OVERDUE = "overdue"
DUE_TODAY = "due_today"
DUE_SOON = "due_soon"
NOT_DUE = "not_due"


def _clamp_day(year, month, day):
    last_day_of_month = calendar.monthrange(year, month)[1]
    return min(day, last_day_of_month)


def _most_recent_weekly(target_weekday, ref):
    offset = (ref.weekday() - target_weekday) % 7
    return ref - timedelta(days=offset)


def _next_weekly(target_weekday, ref):
    return _most_recent_weekly(target_weekday, ref) + timedelta(days=7)


def _most_recent_monthly(day_of_month, ref):
    candidate = date(ref.year, ref.month, _clamp_day(ref.year, ref.month, day_of_month))
    if candidate <= ref:
        return candidate
    prev_month_end = ref.replace(day=1) - timedelta(days=1)
    return date(prev_month_end.year, prev_month_end.month, _clamp_day(prev_month_end.year, prev_month_end.month, day_of_month))


def _next_monthly(day_of_month, ref):
    candidate = date(ref.year, ref.month, _clamp_day(ref.year, ref.month, day_of_month))
    if candidate > ref:
        return candidate
    next_month_start = ref.replace(day=1) + relativedelta(months=1)
    return date(next_month_start.year, next_month_start.month, _clamp_day(next_month_start.year, next_month_start.month, day_of_month))


def _most_recent_yearly(month, day, ref):
    candidate = date(ref.year, month, _clamp_day(ref.year, month, day))
    if candidate <= ref:
        return candidate
    return date(ref.year - 1, month, _clamp_day(ref.year - 1, month, day))


def _next_yearly(month, day, ref):
    candidate = date(ref.year, month, _clamp_day(ref.year, month, day))
    if candidate > ref:
        return candidate
    return date(ref.year + 1, month, _clamp_day(ref.year + 1, month, day))


def _most_recent_occurrence(task, ref):
    if task.schedule == "weekly":
        return _most_recent_weekly(WEEKDAY_INDEX[task.day], ref)
    if task.schedule == "monthly":
        return _most_recent_monthly(task.day_of_month, ref)
    if task.schedule == "yearly":
        return _most_recent_yearly(task.month, task.day_of_month, ref)
    raise ValueError(f"Unknown schedule: {task.schedule!r}")


def _next_occurrence(task, ref):
    if task.schedule == "weekly":
        return _next_weekly(WEEKDAY_INDEX[task.day], ref)
    if task.schedule == "monthly":
        return _next_monthly(task.day_of_month, ref)
    if task.schedule == "yearly":
        return _next_yearly(task.month, task.day_of_month, ref)
    raise ValueError(f"Unknown schedule: {task.schedule!r}")


def _interval_due_date(task, today):
    if task.last_done is None:
        return today
    if task.every_days is not None:
        return task.last_done + relativedelta(days=task.every_days)
    if task.every_months is not None:
        return task.last_done + relativedelta(months=task.every_months)
    if task.every_years is not None:
        return task.last_done + relativedelta(years=task.every_years)
    raise ValueError(f"Interval task '{task.name}' has no every_days/every_months/every_years set")


def _fixed_due_date(task, today):
    occurrence = _most_recent_occurrence(task, today)
    if task.last_done is None or task.last_done < occurrence:
        return occurrence
    return _next_occurrence(task, occurrence)


def compute_due_date(task, today=None):
    """The recurrence-computed due date, ignoring any snooze_until override."""
    today = today or date.today()
    if task.recurrence_type == "interval":
        return _interval_due_date(task, today)
    if task.recurrence_type == "fixed":
        return _fixed_due_date(task, today)
    raise ValueError(f"Unknown recurrence_type: {task.recurrence_type!r}")


def effective_due_date(task, today=None):
    """The due date actually used for status: snooze_until, when set, overrides the computed date."""
    if task.snooze_until is not None:
        return task.snooze_until
    return compute_due_date(task, today)


def get_status(task, today=None, lookahead_days=7):
    """One of OVERDUE, DUE_TODAY, DUE_SOON, NOT_DUE, based on the task's effective due date."""
    today = today or date.today()
    due = effective_due_date(task, today)
    if due < today:
        return OVERDUE
    if due == today:
        return DUE_TODAY
    if due <= today + timedelta(days=lookahead_days):
        return DUE_SOON
    return NOT_DUE
