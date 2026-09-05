from pathlib import Path

import yaml
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.models import Task

RECURRENCE_FIELDS = ["every_days", "every_months", "every_years", "schedule", "day", "day_of_month", "month"]


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
            fields = {field: recurrence.get(field) for field in RECURRENCE_FIELDS}
            fields["recurrence_type"] = recurrence["type"]
            fields["last_done"] = entry.get("last_done")
            fields["last_note"] = entry.get("last_note")
            fields["snooze_until"] = entry.get("snooze_until")

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
