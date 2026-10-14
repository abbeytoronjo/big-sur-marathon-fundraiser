import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

FEED_URL = "https://runalyze.com/athlete/abbeyruns/feed"
START_DATE = "2026-08-01"
DATA_FILE = "training-data.json"
HISTORY_FILE = "training-history.json"


def activity_key(activity):
    """Stable de-duplication key based on date and miles, not the mutable title."""
    return json.dumps(
        [activity["date"], round(float(activity["distance"]), 2)],
        separators=(",", ":"),
    )


# Download the public RUNALYZE RSS feed.
request = urllib.request.Request(
    FEED_URL,
    headers={
        "User-Agent": "Mozilla/5.0 (compatible; BigSurTrainingTracker/1.0)"
    },
)

with urllib.request.urlopen(request, timeout=30) as response:
    xml_data = response.read()

root = ET.fromstring(xml_data)

items = [
    element
    for element in root.iter()
    if element.tag.split("}")[-1] == "item"
]

activities = []
today = datetime.utcnow().date()

for item in items:
    title = ""
    content = ""

    for child in item:
        tag = child.tag.split("}")[-1]

        if tag == "title":
            title = child.text or ""
        elif tag == "encoded":
            content = child.text or ""

    # RUNALYZE puts the actual activity date inside content:encoded.
    date_match = re.search(
        r"<b>Date</b>:\s*(\d{2}/\d{2}/\d{4})",
        content,
    )
    if not date_match:
        continue

    try:
        activity_date = datetime.strptime(
            date_match.group(1), "%m/%d/%Y"
        ).date()
    except ValueError:
        continue

    # Ignore future-dated activities and activities before the tracking start.
    if activity_date > today or activity_date.isoformat() < START_DATE:
        continue

    # RUNALYZE's public RSS feed reports distance in miles for this profile.
    distance_match = re.search(
        r"<b>Distance</b>:\s*([\d.,]+)&nbsp;mi",
        content,
        re.IGNORECASE,
    )
    if not distance_match:
        continue

    try:
        distance = float(distance_match.group(1).replace(",", "."))
    except ValueError:
        continue

    activities.append(
        {
            "date": activity_date.isoformat(),
            "title": title.strip(),
            "distance": round(distance, 2),
        }
    )

activities.sort(key=lambda activity: activity["date"], reverse=True)

print(f"Found {len(items)} RSS activity items")
print(f"Parsed {len(activities)} eligible activities since {START_DATE}")

# Do not overwrite valid site data if RUNALYZE changes its feed format unexpectedly.
if not activities:
    raise RuntimeError(
        "No eligible activities could be parsed from RUNALYZE; "
        "refusing to overwrite the existing training totals."
    )

with open(DATA_FILE, "r", encoding="utf-8") as file:
    current_data = json.load(file)

try:
    with open(HISTORY_FILE, "r", encoding="utf-8") as file:
        history = json.load(file)
except FileNotFoundError:
    # Legacy fallback only. The committed history file is initialized from the
    # full RUNALYZE CSV export, so this path should not be used in normal runs.
    baseline_latest = current_data.get("latest_run")
    history = {
        "start_date": START_DATE,
        "baseline_miles": float(current_data["miles"]),
        "baseline_runs": int(current_data["runs"]),
        "seen_keys": [activity_key(activity) for activity in activities],
        "added_activities": [],
        "baseline_latest_run": baseline_latest,
    }

seen_keys = set(history.get("seen_keys", []))
added_activities = list(history.get("added_activities", []))

for activity in activities:
    key = activity_key(activity)
    if key not in seen_keys:
        added_activities.append(activity)
        seen_keys.add(key)
        print(
            "Added new activity: "
            f'{activity["date"]} — {activity["distance"]:.2f} mi — '
            f'{activity["title"]}'
        )

history["seen_keys"] = sorted(seen_keys)
history["added_activities"] = added_activities

# The baseline is verified against the complete RUNALYZE CSV export. Each
# subsequent unseen RSS activity is added once to the cumulative totals.
baseline_miles = float(history["baseline_miles"])
baseline_runs = int(history["baseline_runs"])

total_miles = round(
    baseline_miles
    + sum(float(activity["distance"]) for activity in added_activities),
    2,
)
run_count = baseline_runs + len(added_activities)
latest_run = activities[0]

now = datetime.utcnow().isoformat() + "Z"
history["updated"] = now

data = {
    "start_date": START_DATE,
    "miles": total_miles,
    "runs": run_count,
    "latest_run": latest_run,
    "updated": now,
}

with open(HISTORY_FILE, "w", encoding="utf-8") as file:
    json.dump(history, file, indent=2)

with open(DATA_FILE, "w", encoding="utf-8") as file:
    json.dump(data, file, indent=2)

print(
    f"Training totals: {run_count} runs, {total_miles:.2f} miles "
    f"({len(added_activities)} activities added after the baseline)"
)
print(json.dumps(data, indent=2))
