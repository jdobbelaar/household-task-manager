from pathlib import Path

import yaml
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.models import Task


class Command(BaseCommand):
    help = "Load/update Task rows from a tasks.yaml file (see _docs/plan.md for the format)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            default=str(Path(settings.BASE_DIR) / "_docs" / "tasks.yaml"),
            help="Path to the tasks.yaml file (default: _docs/tasks.yaml).",
        )

    def handle(self, *args, **options):
        path = Path(options["file"])
        if not path.exists():
            raise CommandError(f"File not found: {path}")

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        entries = data.get("tasks", [])

        created_count = 0
        updated_count = 0

        for entry in entries:
            recurrence = entry.get("recurrence", {})
            schedule = recurrence.get("schedule")
            # In tasks.yaml, "day" means a weekday name for weekly schedules but a
            # day-of-month number for yearly ones; day_of_month covers both here.
            fields = {
                "recurrence_type": recurrence["type"],
                "every_days": recurrence.get("every_days"),
                "every_months": recurrence.get("every_months"),
                "every_years": recurrence.get("every_years"),
                "schedule": schedule,
                "day": recurrence.get("day") if schedule == "weekly" else None,
                "day_of_month": (
                    recurrence.get("day_of_month")
                    if schedule == "monthly"
                    else recurrence.get("day") if schedule == "yearly" else None
                ),
                "month": recurrence.get("month"),
                "last_done": entry.get("last_done"),
                "last_note": entry.get("last_note"),
                "snooze_until": entry.get("snooze_until"),
            }

            _, created = Task.objects.update_or_create(
                name=entry["name"],
                defaults=fields,
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Loaded {len(entries)} tasks from {path} ({created_count} created, {updated_count} updated).")
        )
