# Backlog — Building the App in Django

## Adapting the spec

`_docs/plan.md` specifies a CLI tool backed by a hand-edited `tasks.yaml` file. For this homework
we're building the same task-tracking idea as a Django web app instead:

- **`tasks.yaml` → `Task` model** — data lives in the database; the Django admin replaces
  hand-editing the YAML file.
- **CLI commands (`tasks due`, `tasks done`, `tasks snooze`, `tasks list`) → views** — the same
  actions become pages/buttons in the app.
- **Notification digest & Windows Task Scheduler** — out of scope for this backlog; listed as a
  stretch goal at the end since it's not core to learning Django basics.

The due-date logic (interval vs. fixed recurrence, snooze override, overdue/due-today/upcoming
buckets) carries over unchanged — only where it lives changes.

## Backlog

1. **`Task` model** (`core/models.py`) — fields for `name`, recurrence type (`interval`/`fixed`),
   the recurrence parameters (`every_days`/`every_months`/`every_years` or
   `schedule`/`day`/`day_of_month`/`month`), `last_done`, `last_note`, `snooze_until`. Run
   `makemigrations` / `migrate`.

2. **Register `Task` in the admin** (`core/admin.py`) — gives an immediate way to create/edit
   tasks without building forms first, matching the original spec's "hand-edited data" feel.

3. **Due-date calculation logic** — a module or model method that computes each task's next due
   date and overdue/due-today/upcoming status, per the rules in `plan.md` (calendar-correct
   interval math, fixed-schedule anchoring, `snooze_until` overriding both).

4. **"Task list" view** — lists all tasks with their computed next-due date (equivalent to
   `tasks list`).

5. **"Due tasks" view** — same list, filtered/grouped into Overdue → Due today → Due within N
   days (equivalent to `tasks due --days N`).

6. **"Mark done" action** — a view (button/form) that sets `last_done` to today, optionally saves
   a note, and clears `snooze_until` (equivalent to `tasks done`).

7. **"Snooze" action** — a view (button/form) that sets `snooze_until` to a chosen date
   (equivalent to `tasks snooze`).

8. **URL routing** (`core/urls.py`, wired into `config/urls.py`) — routes for the list, due, done,
   and snooze views.

9. **Templates** — a base template plus pages for the task list and due list, with the three
   status buckets visibly distinguished.

10. **Unit tests** — cover the due-date logic for both recurrence types and the snooze override,
    since that's the trickiest part of the spec to get right.

## Stretch goals (not required for the core homework)

- Recreate the `tasks digest` notification pipeline (email/desktop) as a Django management
  command.
- Config equivalent to `config.yaml` (e.g. `lookahead_days`) via Django settings or a model.
