# Bitbucket Commits & Time Tracker

Two scripts that together automate daily time tracking: fetch your Bitbucket commits for a given date, then submit them as a time entry to the time tracker.

See the [Information Sheet](information-sheet.md) for additional details.

## Scripts

### `bitbucket_commits.py`
Fetches commits authored by you across configured repos for a given date and writes them to a `commits_<date>.txt` file. Merge commits are excluded.

### `time_tracker.py`
Reads the commits file and submits a time log entry via browser automation (Playwright).

## Setup

### 1. Install dependencies

```bash
pip install requests python-dotenv playwright
playwright install chromium
```

### 2. Configure environment variables

Create a `.env` file for Bitbucket:

```env
BITBUCKET_WORKSPACE=your-workspace
BITBUCKET_USERNAME=your-username
BITBUCKET_TOKEN=your-app-password
BITBUCKET_AUTHOR_UUID=your-author-uuid
BITBUCKET_AUTHOR_NICKNAME=your-nickname
BITBUCKET_REPOS=repo-one,repo-two,repo-three
```

Create a `.env.timetracker` file for the time tracker:

```env
TIMETRACKER_USERNAME=your-email
TIMETRACKER_PASSWORD=your-password
```

## Usage

```bash
# Fetch commits for today
python bitbucket_commits.py

# Fetch commits for a specific date
python bitbucket_commits.py 2026-03-18

# Submit time entry for today (requires commits_<today>.txt)
python time_tracker.py

# Submit time entry for a specific date
python time_tracker.py 2026-03-18
```

## Typical workflow

```bash
python bitbucket_commits.py        # generates commits_<date>.txt
python time_tracker.py              # submits it to the time tracker
```
