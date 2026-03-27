# Test Suite — Daily Time Logger

## Setup

Install test dependencies:

```bash
pip install -r tests/requirements.txt
```

---

## Running Tests

### Run all tests
```bash
python -m pytest tests/ -v
```

### Run a specific test file
```bash
python -m pytest tests/test_time_tracker.py -v
python -m pytest tests/test_bitbucket_commits.py -v
python -m pytest tests/test_commits_file.py -v
```

### Run a single test by name
```bash
python -m pytest tests/test_time_tracker.py::TestReadDescription::test_reads_and_returns_file_content -v
```

### Run tests matching a keyword
```bash
python -m pytest tests/ -k "merge" -v
```

---

## Test Files

### `test_time_tracker.py` — Unit tests for `read_description()`

Uses `mock_open` to simulate file I/O without touching the filesystem.

| Test | Description |
|------|-------------|
| `test_reads_and_returns_file_content` | Returns file content as a joined string |
| `test_filters_empty_lines` | Blank lines between commits are stripped |
| `test_filters_whitespace_only_lines` | Lines with only spaces/tabs are excluded |
| `test_returns_empty_string_for_blank_file` | Empty file returns `""` |
| `test_returns_empty_string_for_whitespace_only_file` | Whitespace-only file returns `""` |
| `test_opens_correct_filename_for_date` | Opens `commits_YYYY-MM-DD.txt` for the given date |
| `test_raises_file_not_found_when_missing` | Raises `FileNotFoundError` when file is absent |
| `test_single_line_content` | Single commit line returned correctly |
| `test_strips_leading_and_trailing_whitespace` | Leading/trailing newlines around content are stripped |

---

### `test_bitbucket_commits.py` — Unit tests for `fetch_commits()` and commit message formatting

Uses `unittest.mock.patch` to mock `requests.get` — no real HTTP calls are made.

#### `TestFetchCommits`

| Test | Description |
|------|-------------|
| `test_returns_matching_commits` | Returns commits that match the target date and author |
| `test_skips_merge_commits_starting_with_Merged` | Filters out `Merged PR #...` commits |
| `test_skips_merge_commits_starting_with_Merge` | Filters out `Merge branch '...'` commits |
| `test_skips_commits_with_no_user` | Skips commits with no `user` field in author |
| `test_skips_commits_with_wrong_nickname` | Skips commits from other authors |
| `test_stops_early_when_commit_date_before_target` | Stops pagination when a commit predates the target date |
| `test_ignores_commits_after_target_date` | Skips commits dated after the target day |
| `test_follows_pagination` | Follows the `next` URL across multiple pages |
| `test_raises_on_http_error` | Propagates `requests.HTTPError` on bad responses |
| `test_returns_empty_when_no_commits` | Returns `[]` when the API has no commits |
| `test_result_contains_expected_fields` | Each result has `type`, `nickname`, `author_uuid`, `date` |

#### `TestCommitMessageFormatting`

Tests the regex `^([A-Z]+-\d+)\s` used to insert `: ` after ticket numbers.

| Test | Description |
|------|-------------|
| `test_ticket_prefix_gets_colon_added` | `PROJ-123 fix` → `PROJ-123: fix` |
| `test_multi_letter_project_prefix` | Works with longer prefixes like `ABCDE-99` |
| `test_no_transformation_when_no_ticket_prefix` | Plain messages are left unchanged |
| `test_already_has_colon_no_double_colon` | Already-formatted messages are not double-formatted |
| `test_lowercase_prefix_not_transformed` | Lowercase prefixes are not matched |
| `test_multiline_message_only_first_line_matched` | Only the first line is transformed |

---

### `test_commits_file.py` — Integration tests using real fixture files

Uses a `monkeypatch` fixture (`autouse=True`) to change the working directory to `tests/fixtures/` before each test, so `read_description()` reads real `.txt` files.

#### Fixture files required

Place these in `tests/fixtures/` before running:

| File | Used by |
|------|---------|
| `commits_2026-03-18.txt` | Most tests — expects 2 non-empty, non-merge lines with repo suffixes |
| `commits_2026-03-19.txt` | `test_ticket_lines_have_colon_after_ticket_number`, `test_multiple_commits_joined_by_newline` — expects 3 lines with ticket prefixes |
| `commits_2026-03-20.txt` | `test_returns_empty_string_for_empty_file` — must be an empty file |

#### Tests

| Test | Description |
|------|-------------|
| `test_reads_content_from_real_file` | Checks that known commit messages exist in the result |
| `test_returns_correct_number_of_lines` | File for 2026-03-18 has exactly 2 lines |
| `test_no_empty_lines_in_result` | No line in the result is blank |
| `test_ticket_lines_have_colon_after_ticket_number` | Lines starting with `PROJ-123` must have `: ` after the ticket |
| `test_every_line_ends_with_repo_suffix` | Every line ends with `(repo-name).` |
| `test_no_merge_commits_in_file` | No line starts with `Merged` or `Merge ` |
| `test_returns_empty_string_for_empty_file` | Empty fixture file returns `""` |
| `test_multiple_commits_joined_by_newline` | File for 2026-03-19 has exactly 3 lines joined by `\n` |
| `test_raises_file_not_found_for_missing_date` | Missing date raises `FileNotFoundError` |

---

## Configuration

`conftest.py` adds `src/` to `sys.path` so all test files can import `time_tracker` and `bitbucket_commits` directly without installing the package.
