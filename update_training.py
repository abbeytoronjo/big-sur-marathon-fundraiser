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
    """Stable key used to avoid counting the same RSS activity more than once."""
    return json.dumps(
        [
            activity["date"],
            activity["title"].strip(),
            round(float(activity["distance"]), 2),
        ],
        ensure_ascii=False,
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

    # RUNALYZE puts the distance inside content:encoded.
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

activities.sort(key=lambda activity: (activity["date"], activity["title"]), reverse=True)

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

# Bootstrap a cumulative history from the site's existing totals. All activities
# currently in the feed are marked as already included in that baseline, so the
# first run of this version does not double-count them.
try:
    with open(HISTORY_FILE, "r", encoding="utf-8") as file:
        history = json.load(file)
    is_bootstrap = False
except FileNotFoundError:
    history = {
        "start_date": START_DATE,
        "baseline_miles": float(current_data["miles"]),
        "baseline_runs": int(current_data["runs"]),
        "seen_keys": [activity_key(activity) for activity in activities],
        "added_activities": [],
        "baseline_latest_run": current_data.get("latest_run"),
    }
    is_bootstrap = True

if not is_bootstrap:
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

# Totals now start from the existing baseline and add only newly discovered,
# unique activities, so they keep growing even when older runs roll off the RSS feed.
baseline_miles = float(history["baseline_miles"])
baseline_runs = int(history["baseline_runs"])
added_activities = history.get("added_activities", [])

total_miles = round(
    baseline_miles + sum(float(activity["distance"]) for activity in added_activities),
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
