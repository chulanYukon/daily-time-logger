import re
import pytest
from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch, call

from bitbucket_commits import fetch_commits


def make_commit(msg, date_str, nickname="shamin", uuid="{user-uuid-123}"):
    return {
        "type": "commit",
        "date": date_str,
        "message": msg,
        "author": {
            "user": {
                "uuid": uuid,
                "nickname": nickname,
            }
        },
    }


def api_response(values, next_url=None):
    mock = MagicMock()
    mock.raise_for_status = MagicMock()
    mock.json.return_value = {"values": values, "next": next_url}
    return mock


TARGET_DATE = date(2026, 3, 18)
DATE_ON_TARGET = "2026-03-18T10:00:00+00:00"
DATE_BEFORE_TARGET = "2026-03-17T10:00:00+00:00"
DATE_AFTER_TARGET = "2026-03-19T10:00:00+00:00"

AUTH = ("user", "token")
WORKSPACE = "my-workspace"
REPO = "my-repo"
AUTHOR_UUID = "user-uuid-123"
AUTHOR_NICKNAME = "shamin"


class TestFetchCommits:
    def test_returns_matching_commits(self):
        commit = make_commit("PROJ-1 fix bug", DATE_ON_TARGET)
        with patch("bitbucket_commits.requests.get", return_value=api_response([commit])):
            result = fetch_commits(WORKSPACE, REPO, AUTH, TARGET_DATE, AUTHOR_UUID, AUTHOR_NICKNAME)

        assert len(result) == 1
        assert result[0]["message"] == "PROJ-1 fix bug"
        assert result[0]["nickname"] == "shamin"

    def test_skips_merge_commits_starting_with_Merged(self):
        commits = [
            make_commit("Merged PR #42", DATE_ON_TARGET),
            make_commit("PROJ-2 real work", DATE_ON_TARGET),
        ]
        with patch("bitbucket_commits.requests.get", return_value=api_response(commits)):
            result = fetch_commits(WORKSPACE, REPO, AUTH, TARGET_DATE, AUTHOR_UUID, AUTHOR_NICKNAME)

        assert len(result) == 1
        assert result[0]["message"] == "PROJ-2 real work"

    def test_skips_merge_commits_starting_with_Merge(self):
        commits = [
            make_commit("Merge branch 'main'", DATE_ON_TARGET),
        ]
        with patch("bitbucket_commits.requests.get", return_value=api_response(commits)):
            result = fetch_commits(WORKSPACE, REPO, AUTH, TARGET_DATE, AUTHOR_UUID, AUTHOR_NICKNAME)

        assert result == []

    def test_skips_commits_with_no_user(self):
        commit = {
            "type": "commit",
            "date": DATE_ON_TARGET,
            "message": "PROJ-3 something",
            "author": {},  # no "user" key
        }
        with patch("bitbucket_commits.requests.get", return_value=api_response([commit])):
            result = fetch_commits(WORKSPACE, REPO, AUTH, TARGET_DATE, AUTHOR_UUID, AUTHOR_NICKNAME)

        assert result == []

    def test_skips_commits_with_wrong_nickname(self):
        commit = make_commit("PROJ-4 other person", DATE_ON_TARGET, nickname="otherdev")
        with patch("bitbucket_commits.requests.get", return_value=api_response([commit])):
            result = fetch_commits(WORKSPACE, REPO, AUTH, TARGET_DATE, AUTHOR_UUID, AUTHOR_NICKNAME)

        assert result == []

    def test_stops_early_when_commit_date_before_target(self):
        commits = [
            make_commit("PROJ-5 earlier commit", DATE_BEFORE_TARGET),
        ]
        with patch("bitbucket_commits.requests.get", return_value=api_response(commits)) as mock_get:
            result = fetch_commits(WORKSPACE, REPO, AUTH, TARGET_DATE, AUTHOR_UUID, AUTHOR_NICKNAME)

        assert result == []
        mock_get.assert_called_once()  # should not follow next pages

    def test_ignores_commits_after_target_date(self):
        commits = [
            make_commit("PROJ-6 future commit", DATE_AFTER_TARGET),
            make_commit("PROJ-7 on target", DATE_ON_TARGET),
        ]
        with patch("bitbucket_commits.requests.get", return_value=api_response(commits)):
            result = fetch_commits(WORKSPACE, REPO, AUTH, TARGET_DATE, AUTHOR_UUID, AUTHOR_NICKNAME)

        assert len(result) == 1
        assert result[0]["message"] == "PROJ-7 on target"

    def test_follows_pagination(self):
        page1_commit = make_commit("PROJ-8 first page", DATE_ON_TARGET)
        page2_commit = make_commit("PROJ-9 second page", DATE_ON_TARGET)

        page1 = api_response([page1_commit], next_url="https://api.bitbucket.org/2.0/next")
        page2 = api_response([page2_commit])

        with patch("bitbucket_commits.requests.get", side_effect=[page1, page2]):
            result = fetch_commits(WORKSPACE, REPO, AUTH, TARGET_DATE, AUTHOR_UUID, AUTHOR_NICKNAME)

        assert len(result) == 2
        assert result[0]["message"] == "PROJ-8 first page"
        assert result[1]["message"] == "PROJ-9 second page"

    def test_raises_on_http_error(self):
        import requests as req
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = req.HTTPError("401 Unauthorized")

        with patch("bitbucket_commits.requests.get", return_value=mock_response):
            with pytest.raises(req.HTTPError):
                fetch_commits(WORKSPACE, REPO, AUTH, TARGET_DATE, AUTHOR_UUID, AUTHOR_NICKNAME)

    def test_returns_empty_when_no_commits(self):
        with patch("bitbucket_commits.requests.get", return_value=api_response([])):
            result = fetch_commits(WORKSPACE, REPO, AUTH, TARGET_DATE, AUTHOR_UUID, AUTHOR_NICKNAME)

        assert result == []

    def test_result_contains_expected_fields(self):
        commit = make_commit("PROJ-10 check fields", DATE_ON_TARGET)
        with patch("bitbucket_commits.requests.get", return_value=api_response([commit])):
            result = fetch_commits(WORKSPACE, REPO, AUTH, TARGET_DATE, AUTHOR_UUID, AUTHOR_NICKNAME)

        assert result[0]["type"] == "commit"
        assert result[0]["nickname"] == "shamin"
        assert result[0]["author_uuid"] == "{user-uuid-123}"
        assert result[0]["date"] == DATE_ON_TARGET


class TestCommitMessageFormatting:
    """Tests for the regex used in __main__ to format commit messages."""

    PATTERN = re.compile(r'^([A-Z]+-\d+)\s')

    def _format(self, message):
        return re.sub(self.PATTERN, r'\1: ', message)

    def test_ticket_prefix_gets_colon_added(self):
        assert self._format("PROJ-123 fix the thing") == "PROJ-123: fix the thing"

    def test_multi_letter_project_prefix(self):
        assert self._format("ABCDE-99 some work") == "ABCDE-99: some work"

    def test_no_transformation_when_no_ticket_prefix(self):
        assert self._format("general cleanup") == "general cleanup"

    def test_already_has_colon_no_double_colon(self):
        # The regex requires a space, not colon, so "PROJ-1: msg" is unchanged
        assert self._format("PROJ-1: already formatted") == "PROJ-1: already formatted"

    def test_lowercase_prefix_not_transformed(self):
        assert self._format("proj-1 lowercase") == "proj-1 lowercase"

    def test_multiline_message_only_first_line_matched(self):
        msg = "PROJ-5 first line\nsome details"
        result = self._format(msg)
        assert result.startswith("PROJ-5: first line")
