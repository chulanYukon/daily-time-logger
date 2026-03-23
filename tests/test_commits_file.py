import os
import re
import pytest
from datetime import date

from time_tracker import read_description

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture(autouse=True)
def change_to_fixtures_dir(monkeypatch):
    """Make read_description look for .txt files inside the fixtures folder."""
    monkeypatch.chdir(FIXTURES_DIR)


class TestReadDescriptionWithFixtureFiles:

    def test_reads_content_from_real_file(self):
        result = read_description(date(2026, 3, 18))

        assert "BP-11266: remove unwanted file (booq.bo.engine.back-end)." in result
        assert "resolve conflicts (booq.bo.engine.back-end)." in result

    def test_returns_correct_number_of_lines(self):
        result = read_description(date(2026, 3, 18))

        assert len(result.splitlines()) == 2

    def test_no_empty_lines_in_result(self):
        result = read_description(date(2026, 3, 18))

        for line in result.splitlines():
            assert line.strip() != ""

    def test_ticket_lines_have_colon_after_ticket_number(self):
        result = read_description(date(2026, 3, 19))

        ticket_lines = [l for l in result.splitlines() if re.match(r'^[A-Z]+-\d+', l)]
        for line in ticket_lines:
            assert re.match(r'^[A-Z]+-\d+: ', line), f"Missing colon in: {line}"

    def test_every_line_ends_with_repo_suffix(self):
        result = read_description(date(2026, 3, 18))

        for line in result.splitlines():
            assert re.search(r'\([^)]+\)\.$', line), f"Missing repo suffix in: {line}"

    def test_no_merge_commits_in_file(self):
        result = read_description(date(2026, 3, 18))

        for line in result.splitlines():
            assert not line.startswith("Merged"), f"Merge commit found: {line}"
            assert not line.startswith("Merge "), f"Merge commit found: {line}"

    def test_returns_empty_string_for_empty_file(self):
        result = read_description(date(2026, 3, 20))

        assert result == ""

    def test_multiple_commits_joined_by_newline(self):
        result = read_description(date(2026, 3, 19))

        assert "\n" in result
        assert len(result.splitlines()) == 3

    def test_raises_file_not_found_for_missing_date(self):
        with pytest.raises(FileNotFoundError):
            read_description(date(2026, 1, 1))
