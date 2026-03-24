import os
import re
import sys
from datetime import date, datetime, timezone
import requests
from dotenv import load_dotenv

load_dotenv("configurations/.env")

REPOS = [r.strip() for r in os.getenv("BITBUCKET_REPOS", "").split(",") if r.strip()]


def fetch_commits(workspace, repo, auth, target_date, author_uuid, author_nickname):
    url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo}/commits"
    params = {"pagelen": 100, "q": f'author.uuid="{{{author_uuid}}}"'}
    matched = []

    while url:
        response = requests.get(url, auth=auth, params=params)
        response.raise_for_status()
        data = response.json()

        for c in data.get("values", []):
            commit_date = datetime.fromisoformat(c["date"]).astimezone(timezone.utc).date()
            if commit_date == target_date:
                message = c["message"].strip()
                if message.startswith(("Merged", "Merge")):
                    continue
                user = c["author"].get("user")
                if not user:
                    continue
                nickname = user.get("nickname", "")
                if nickname != author_nickname:
                    continue
                matched.append({
                    "type": c["type"],
                    "date": c["date"],
                    "author_uuid": user["uuid"],
                    "nickname": nickname,
                    "message": message,
                })
            elif commit_date < target_date:
                return matched

        url = data.get("next")
        params = {}

    return matched


if __name__ == "__main__":
    workspace = os.getenv("BITBUCKET_WORKSPACE")
    username = os.getenv("BITBUCKET_USERNAME")
    token = os.getenv("BITBUCKET_TOKEN")
    author_uuid = os.getenv("BITBUCKET_AUTHOR_UUID")
    author_nickname = os.getenv("BITBUCKET_AUTHOR_NICKNAME")

    if len(sys.argv) > 1:
        target_date = date.fromisoformat(sys.argv[1])
    else:
        target_date = date.today()

    auth = (username, token)

    print(f"Fetching commits for date: {target_date}\n")

    all_parts = []
    total = 0

    for repo in REPOS:
        try:
            commits = fetch_commits(workspace, repo, auth, target_date, author_uuid, author_nickname)
            if commits:
                lines = [re.sub(r'^([A-Z]+-\d+)\s', r'\1: ', c['message']) + f" ({repo})." for c in commits]
                all_parts.extend(lines)
                total += len(commits)
                print(f"[OK] {repo} — {len(commits)} commit(s)")
            else:
                print(f"[--] {repo} — no commits")
        except requests.HTTPError as e:
            print(f"[ERROR] {repo} — {e}")

    result = "\n".join(all_parts)

    output_file = f"output/commits_{target_date}.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"\nTotal: {total} commit(s) found. Saved to {output_file}")
