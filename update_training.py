import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

FEED_URL = "https://runalyze.com/athlete/abbeyruns/feed"
START_DATE = "2026-08-01"

# Download the public RUNALYZE RSS feed
with urllib.request.urlopen(FEED_URL) as response:
    xml_data = response.read()

root = ET.fromstring(xml_data)

activities = []

for item in root.findall(".//item"):
    title = item.findtext("title", "")
    description = item.findtext("description", "")
    pub_date = item.findtext("pubDate", "")

    if not pub_date:
        continue

    try:
        activity_date = datetime.strptime(
            pub_date[:25],
            "%a, %d %b %Y %H:%M:%S"
        ).date()
    except ValueError:
        continue

    if activity_date.isoformat() < START_DATE:
        continue

    # Look for a distance value in the activity description.
    distance = None

    for line in description.replace("<br>", "\n").splitlines():
        line = line.strip()

        if "Distance" in line:
            parts = line.replace(",", "").split()
            for i, part in enumerate(parts):
                if part.lower() in ("mi", "miles") and i > 0:
                    try:
                        distance = float(parts[i - 1])
                        break
                    except ValueError:
                        pass

    if distance is not None:
        activities.append({
            "date": activity_date.isoformat(),
            "title": title,
            "distance": distance,
        })

# Sort newest first
activities.sort(key=lambda x: x["date"], reverse=True)

total_miles = round(sum(a["distance"] for a in activities), 2)
run_count = len(activities)

latest_run = activities[0] if activities else None

data = {
    "start_date": START_DATE,
    "miles": total_miles,
    "runs": run_count,
    "latest_run": latest_run,
    "updated": datetime.utcnow().isoformat() + "Z",
}

with open("training-data.json", "w") as file:
    json.dump(data, file, indent=2)

print(json.dumps(data, indent=2))
