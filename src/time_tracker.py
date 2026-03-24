import os
import re
import sys
from datetime import date
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv(".env.timetracker")

TIMETRACKER_URL = "https://timetracker.yukon.software/login.aspx"
PROJECT_NAME = "booq platform (Eijsink)"
HOURS = "8"
MINUTES = "0"


def read_description(target_date: date) -> str:
    commits_file = f"output/commits_{target_date}.txt"
    with open(commits_file, "r", encoding="utf-8") as f:
        content = f.read()
    lines = [line for line in content.splitlines() if line.strip()]
    return "\n".join(lines).strip()


def submit_timetracker(description: str, target_date: date):
    username = os.getenv("TIMETRACKER_USERNAME")
    password = os.getenv("TIMETRACKER_PASSWORD")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=800)
        page = browser.new_page()

        # Login
        page.goto(TIMETRACKER_URL)
        page.wait_for_load_state("networkidle")
        page.get_by_placeholder("Email").fill(username)
        page.get_by_placeholder("Password").fill(password)
        page.get_by_role("button", name="Login").click()
        page.wait_for_url(lambda url: "login" not in url.lower(), timeout=15000)

        # Click Log Hours
        page.get_by_text("Log Hours").first.click()
        page.wait_for_load_state("networkidle")

        # Click the target date in the calendar — exclude "off" cells (overflow days from adjacent months)
        day = str(target_date.day)
        page.locator("table td:not(.off)").filter(has_text=re.compile(f"^{day}$")).first.click()

        # Set hours and minutes
        page.locator("#vFORMWORKHOURLOGHOURS").fill(HOURS)
        page.locator("#vFORMWORKHOURLOGMINUTES").fill(MINUTES)

        # Fill description
        page.locator("textarea").fill(description)

        # Click Confirm
        page.locator("#BTNSAVE").click()
        page.wait_for_load_state("networkidle")

        browser.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_date = date.fromisoformat(sys.argv[1])
    else:
        target_date = date.today()

    description = read_description(target_date)
    if not description:
        print("No commits found. Nothing to submit.")
        sys.exit(1)

    print(f"Submitting time entry for {target_date}:")
    print(description)
    print()
    submit_timetracker(description, target_date)
