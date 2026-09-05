from django.shortcuts import render

from . import duedates
from .models import Task

DEFAULT_LOOKAHEAD_DAYS = 7


def build_task_rows(lookahead_days=DEFAULT_LOOKAHEAD_DAYS):
    """All tasks with their effective due date and status, soonest first."""
    tasks = Task.objects.all()
    rows = [
        {"task": task, "due_date": task.get_effective_due_date(), "status": task.get_status(lookahead_days=lookahead_days)}
        for task in tasks
    ]
    rows.sort(key=lambda row: row["due_date"])
    return rows


def build_due_buckets(lookahead_days=DEFAULT_LOOKAHEAD_DAYS):
    """Rows due now or soon, grouped into Overdue -> Due today -> Due within N days."""
    rows = build_task_rows(lookahead_days=lookahead_days)
    return {
        "overdue": [row for row in rows if row["status"] == duedates.OVERDUE],
        "due_today": [row for row in rows if row["status"] == duedates.DUE_TODAY],
        "due_soon": [row for row in rows if row["status"] == duedates.DUE_SOON],
    }


def task_list(request):
    return render(request, "core/task_list.html", {"rows": build_task_rows()})


def due_list(request):
    lookahead_days = int(request.GET.get("days", DEFAULT_LOOKAHEAD_DAYS))
    return render(
        request,
        "core/due_list.html",
        {"buckets": build_due_buckets(lookahead_days=lookahead_days), "lookahead_days": lookahead_days},
    )
