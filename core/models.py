from django.db import models

from . import duedates


class Task(models.Model):
    class RecurrenceType(models.TextChoices):
        INTERVAL = "interval", "Interval"
        FIXED = "fixed", "Fixed"

    class Schedule(models.TextChoices):
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"
        YEARLY = "yearly", "Yearly"

    class Weekday(models.TextChoices):
        MONDAY = "mon", "Monday"
        TUESDAY = "tue", "Tuesday"
        WEDNESDAY = "wed", "Wednesday"
        THURSDAY = "thu", "Thursday"
        FRIDAY = "fri", "Friday"
        SATURDAY = "sat", "Saturday"
        SUNDAY = "sun", "Sunday"

    name = models.CharField(max_length=200, unique=True)

    recurrence_type = models.CharField(max_length=10, choices=RecurrenceType.choices)

    # recurrence_type == "interval": exactly one of these is set
    every_days = models.PositiveIntegerField(null=True, blank=True)
    every_months = models.PositiveIntegerField(null=True, blank=True)
    every_years = models.PositiveIntegerField(null=True, blank=True)

    # recurrence_type == "fixed"
    schedule = models.CharField(max_length=10, choices=Schedule.choices, null=True, blank=True)
    day = models.CharField(max_length=3, choices=Weekday.choices, null=True, blank=True)  # schedule == "weekly"
    day_of_month = models.PositiveSmallIntegerField(null=True, blank=True)  # schedule == "monthly" or "yearly"
    month = models.PositiveSmallIntegerField(null=True, blank=True)  # schedule == "yearly"

    last_done = models.DateField(null=True, blank=True)
    last_note = models.TextField(null=True, blank=True)
    snooze_until = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.name

    def get_due_date(self, today=None):
        """The recurrence-computed due date, ignoring any snooze_until override."""
        return duedates.compute_due_date(self, today)

    def get_effective_due_date(self, today=None):
        """The due date actually used for status: snooze_until, when set, overrides the computed date."""
        return duedates.effective_due_date(self, today)

    def get_status(self, today=None, lookahead_days=7):
        """One of duedates.OVERDUE, DUE_TODAY, DUE_SOON, NOT_DUE."""
        return duedates.get_status(self, today, lookahead_days)
