import json
import re
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "https://fundraisers.hakuapp.com/abbey-toronjo"
OUTPUT = Path("fundraising-data.json")


def extract_raised(text: str) -> float:
    text = re.sub(r"\s+", " ", text).strip()

    patterns = [
        r"\$\s*([\d,]+(?:\.\d{1,2})?)\s*(?:raised|raise[d]? so far)",
        r"(?:raised|raise[d]? so far)\s*[:\-]?\s*\$\s*([\d,]+(?:\.\d{1,2})?)",
        r"\$\s*([\d,]+(?:\.\d{1,2})?)\s*(?=raised)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return float(match.group(1).replace(",", ""))

    # Fall back to examining short snippets around the word "raised".
    for match in re.finditer(r"raised", text, flags=re.IGNORECASE):
        snippet = text[max(0, match.start() - 180): match.end() + 180]
        amount = re.search(r"\$\s*([\d,]+(?:\.\d{1,2})?)", snippet)
        if amount:
            return float(amount.group(1).replace(",", ""))

    raise RuntimeError("Could not find the live fundraising amount on the Haku page. No data was written.")


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1200})
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(5000)
    body_text = page.locator("body").inner_text()
    raised = extract_raised(body_text)
    browser.close()

payload = {
    "raised": raised,
    "updated": datetime.now(timezone.utc).isoformat(),
    "source": URL,
}

OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(f"Updated fundraising total: ${raised:,.2f}")
