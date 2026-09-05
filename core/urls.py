from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.due_list, name="due_list"),
    path("tasks/", views.task_list, name="task_list"),
    path("tasks/<int:task_id>/done/", views.mark_done, name="mark_done"),
    path("tasks/<int:task_id>/snooze/", views.snooze, name="snooze"),
]
