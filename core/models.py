from django.db import models


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
    day = models.CharField(max_length=3, choices=Weekday.choices, null=True, blank=True)
    day_of_month = models.PositiveSmallIntegerField(null=True, blank=True)
    month = models.PositiveSmallIntegerField(null=True, blank=True)

    last_done = models.DateField(null=True, blank=True)
    last_note = models.TextField(null=True, blank=True)
    snooze_until = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.name
