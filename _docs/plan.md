# Household Task Manager — Specification

## Overview
A local Python CLI tool for tracking recurring household tasks (e.g. "clean gutters every 180 days", "trash every Monday"). Single user, no accounts. Tasks are stored in a plain YAML file the user edits by hand; the CLI is used only to view what's due and to mark tasks done/snoozed. A scheduled daily digest emails (or, as fallback, desktop-notifies) a summary of what's due.

## Non-goals (v1)
- No multi-user support, accounts, or task assignment
- No categories/tags or priority levels (flat list)
- No full completion history/log (only last completion + optional note)
- No mobile app or hosted/cloud component
- No in-CLI task creation/editing commands (file is hand-edited)

## Data file — `tasks.yaml`
One entry per task. Task `name` is the unique identifier (CLI matches on exact name, or unambiguous case-insensitive prefix).

```yaml
tasks:
  - name: "Take out trash"
    recurrence:
      type: fixed
      schedule: weekly
      day: mon          # mon..sun
    last_done: 2026-09-01
    last_note: null
    snooze_until: null

  - name: "Replace furnace filter"
    recurrence:
      type: fixed
      schedule: monthly
      day_of_month: 1
    last_done: 2026-08-01
    last_note: null
    snooze_until: null

  - name: "Clean gutters"
    recurrence:
      type: interval
      every_days: 180
    last_done: 2026-03-15
    last_note: "used the leaf blower attachment"
    snooze_until: null

  - name: "Kia Niro annual service"
    recurrence:
      type: interval
      every_years: 1        # interval also accepts every_months / every_years
    last_done: 2024-11-23
    last_note: null
    snooze_until: null

  - name: "Change smoke detector batteries"
    recurrence:
      type: fixed
      schedule: yearly
      month: 11
      day: 1
    last_done: null
    last_note: null
    snooze_until: null
```

Supported `recurrence.type`:
- **`interval`**: exactly one of `every_days: N`, `every_months: N`, or `every_years: N`. Next due = `last_done + N` (days/months/years, using calendar-correct addition — e.g. `dateutil.relativedelta` — not a fixed day count, so month/year intervals don't drift). If `last_done` is null, task is due immediately.
- **`fixed`**: `schedule: weekly|monthly|yearly` with `day` (weekday name, weekly), `day_of_month` (1–31, monthly), or `month`+`day` (yearly). Due dates are calendar-anchored, independent of `last_done`.

## Due-date logic

**Interval tasks:** next due = `last_done + every_days`. Overdue if next due < today.

**Fixed tasks:** compute the most recent scheduled occurrence that is `<= today`. If `last_done` is null or `last_done <` that occurrence date, the task is **overdue** (flagged until completed — missed occurrences are not silently skipped). If `last_done >=` that occurrence, the task is not due; next due = the next future occurrence.

**Snooze / override (`snooze_until`):** when set, this date *replaces* the computed due date entirely — the task's overdue/due-today/upcoming status is determined by comparing `snooze_until` to today, not by the recurrence calculation above. (This deliberately covers two related uses: pushing a task out a few days because you're not getting to it yet, and pinning an authoritative due date — e.g. a fixed-schedule task whose `last_done` doesn't cleanly align with the last occurrence, or a task timed to a real-world condition like soil temperature rather than a strict calendar date.) `snooze_until` is cleared automatically when the task is marked done, at which point normal recurrence calculation resumes from the new `last_done`.

**Status buckets** (for `tasks due` and the digest), in this order: **Overdue** → **Due today** → **Due within N days** (default N=7, configurable via `--days` flag or config default).

## CLI commands

- **`tasks due [--days N]`** — list tasks in the three buckets above, using each task's effective due date (`snooze_until` if set, otherwise the computed date). Default N=7.
- **`tasks done <name> [--note "text"] [--date YYYY-MM-DD]`** — set `last_done` to today (or given date), set `last_note` if provided, clear `snooze_until`. Completing early (before a task is actually due) is allowed and simply resets the cycle from that date.
- **`tasks snooze <name> (--days N | --date YYYY-MM-DD)`** — set `snooze_until` to today+N, or to an explicit date. This is also how you pin an override due date by hand via the CLI, equivalent to editing `snooze_until` directly in the file.
- **`tasks list`** — list all tasks with computed next-due date, for a full overview.
- **`tasks digest`** — compute the due list and send it via the notification pipeline below. Intended to be run on a schedule, not interactively.

Name matching: exact match first; if not found, case-insensitive unambiguous prefix/substring match; otherwise error listing close matches.

## Notification pipeline (`tasks digest`)
1. Build the due-list body (same content as `tasks due`, default N days).
2. If there's nothing overdue/due/upcoming, do nothing (no empty digests).
3. Try sending via **Gmail SMTP** (`smtp.gmail.com:587`, TLS) using an address + [Gmail App Password](https://myaccount.google.com/apppasswords) read from environment variables (`HOUSEHOLD_TASKS_GMAIL_USER`, `HOUSEHOLD_TASKS_GMAIL_APP_PASSWORD`) — not stored in the YAML/config file. Sends to self.
4. If email fails (missing credentials, network error, SMTP error), fall back to a **Windows toast notification** (via `plyer` or `win10toast`) summarizing the counts (e.g. "3 overdue, 1 due today") — full detail isn't practical in a toast, so it just prompts the user to run `tasks due`.
5. Log the outcome (success/method used/failure) to a small log file for troubleshooting.

## Config file — `config.yaml`
```yaml
data_file: tasks.yaml
lookahead_days: 7
email:
  enabled: true
  to: your_address@gmail.com
desktop_fallback: true
```
(Credentials are env vars, not in this file, per above.)

## Scheduling the digest
Use **Windows Task Scheduler** to run `python digest.py` (or a packaged `.exe`) once daily at a fixed time. Spec deliverable should include a short README section with the exact `schtasks`/Task Scheduler steps once built.

## Tech stack
- Python 3.x
- `PyYAML` for the data/config files
- Standard library `smtplib`/`email` for Gmail sending
- `plyer` (or `win10toast`) for Windows desktop notification fallback
- `click` or `argparse` for the CLI

## Open items for the coding agent to decide/confirm during build
- Exact CLI output formatting (table vs. plain list)
- Log file location and rotation (keep minimal)
- Whether to validate `tasks.yaml` on load and give friendly errors for malformed entries (recommended, since it's hand-edited)
