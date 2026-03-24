# Project Information Sheet — Bitbucket Commits & Time Tracker

## 1. What It Does

A two-step CLI automation tool for daily time logging:

1. **`src/bitbucket_commits.py`** — Calls the Bitbucket REST API, collects all your commits across configured repositories for a given date, formats them, and saves the output to `output/commits_<date>.txt`.
2. **`src/time_tracker.py`** — Reads that text file and uses browser automation (Playwright) to log into the time tracker web app, navigate to the correct date on the calendar, and submit the commits as the day's time entry description (8h 0m).

---

## 2. Design Criteria

| Criteria | Detail |
|---|---|
| **Zero manual input** | Both scripts default to today's date; no arguments needed for the common case |
| **Date-specific runs** | An optional `YYYY-MM-DD` argument lets you backfill past dates |
| **Author-scoped fetching** | Filters by both UUID and nickname to avoid picking up commits from other users in the same workspace |
| **Merge commit exclusion** | Commits starting with `Merge` / `Merged` are skipped — only real work commits are logged |
| **Ticket reference formatting** | Commit messages matching `TICKET-123 ...` are reformatted to `TICKET-123: ...` for consistency |
| **Repo attribution** | Each commit line is suffixed with its source repo name, e.g. `(booq.fo.server).` |
| **Config via `.env`** | All credentials and repo list are externalised — no secrets in code |
| **Paginated API traversal** | Follows Bitbucket's `next` pagination cursor and stops early once commits go before the target date |

---

## 3. Data Flow

```
Bitbucket API
     │
     ▼
src/bitbucket_commits.py  ──►  output/commits_<date>.txt
                                          │
                                          ▼
                              src/time_tracker.py  ──►  Time Tracker Web App
```

---

## 4. Dependencies

| Package | Purpose |
|---|---|
| `requests` | Bitbucket REST API calls |
| `python-dotenv` | Load `configurations/.env` / `configurations/.env.timetracker` files |
| `playwright` (chromium) | Browser automation for the time tracker UI |

---

## 5. Configuration Files

| File | Used by | Contains |
|---|---|---|
| `configurations/.env` | `src/bitbucket_commits.py` | Workspace, username, token, author UUID/nickname, repo list |
| `configurations/.env.timetracker` | `src/time_tracker.py` | Time tracker login credentials |

---

## 6. Known Constraints / Hardcoded Values

- **Hours logged:** always `8h 0m` (hardcoded in `time_tracker.py`)
- **Project name:** `booq platform (Eijsink)` (referenced but not currently used in form submission)
- **Browser:** Chromium, non-headless with `slow_mo=800ms` — runs visibly so you can watch/intervene
