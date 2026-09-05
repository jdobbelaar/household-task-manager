from django.shortcuts import render

from .models import Task


def build_task_rows():
    """All tasks with their effective due date, soonest first."""
    tasks = Task.objects.all()
    rows = [{"task": task, "due_date": task.get_effective_due_date(), "status": task.get_status()} for task in tasks]
    rows.sort(key=lambda row: row["due_date"])
    return rows


def task_list(request):
    return render(request, "core/task_list.html", {"rows": build_task_rows()})
