import pytest
from datetime import date
from unittest.mock import mock_open, patch

from time_tracker import read_description


class TestReadDescription:
    TARGET_DATE = date(2026, 3, 18)

    def test_reads_and_returns_file_content(self):
        content = "PROJ-1: fix bug (my-repo).\nPROJ-2: add feature (other-repo)."
        with patch("builtins.open", mock_open(read_data=content)):
            result = read_description(self.TARGET_DATE)

        assert result == "PROJ-1: fix bug (my-repo).\nPROJ-2: add feature (other-repo)."

    def test_filters_empty_lines(self):
        content = "PROJ-1: fix bug (my-repo).\n\n\nPROJ-2: add feature (other-repo).\n"
        with patch("builtins.open", mock_open(read_data=content)):
            result = read_description(self.TARGET_DATE)

        assert result == "PROJ-1: fix bug (my-repo).\nPROJ-2: add feature (other-repo)."

    def test_filters_whitespace_only_lines(self):
        # Lines that are only spaces/tabs are excluded; non-empty lines keep their content as-is
        content = "PROJ-1: fix bug (my-repo).\n   \nPROJ-2: add feature (other-repo)."
        with patch("builtins.open", mock_open(read_data=content)):
            result = read_description(self.TARGET_DATE)

        assert result == "PROJ-1: fix bug (my-repo).\nPROJ-2: add feature (other-repo)."

    def test_returns_empty_string_for_blank_file(self):
        with patch("builtins.open", mock_open(read_data="")):
            result = read_description(self.TARGET_DATE)

        assert result == ""

    def test_returns_empty_string_for_whitespace_only_file(self):
        with patch("builtins.open", mock_open(read_data="\n\n   \n")):
            result = read_description(self.TARGET_DATE)

        assert result == ""

    def test_opens_correct_filename_for_date(self):
        with patch("builtins.open", mock_open(read_data="content")) as mock_file:
            read_description(date(2026, 3, 18))

        mock_file.assert_called_once_with("commits_2026-03-18.txt", "r", encoding="utf-8")

    def test_raises_file_not_found_when_missing(self):
        with patch("builtins.open", side_effect=FileNotFoundError):
            with pytest.raises(FileNotFoundError):
                read_description(self.TARGET_DATE)

    def test_single_line_content(self):
        content = "PROJ-42: single commit (my-repo)."
        with patch("builtins.open", mock_open(read_data=content)):
            result = read_description(self.TARGET_DATE)

        assert result == "PROJ-42: single commit (my-repo)."

    def test_strips_leading_and_trailing_whitespace(self):
        content = "\n  PROJ-1: fix bug (my-repo).\n"
        with patch("builtins.open", mock_open(read_data=content)):
            result = read_description(self.TARGET_DATE)

        assert result == "PROJ-1: fix bug (my-repo)."
