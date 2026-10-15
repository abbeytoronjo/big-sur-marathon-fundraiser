// Fundraising settings
const GOAL = 2000;

// Load the live total written by the GitHub Actions Haku updater.
fetch("fundraising-data.json", { cache: "no-store" })
  .then(response => {
    if (!response.ok) throw new Error(`Fundraising data request failed: ${response.status}`);
    return response.json();
  })
  .then(data => {
    const raised = Number(data.raised) || 0;
    const raisedEl = document.getElementById("raised");
    const progressBar = document.getElementById("progress-bar");

    if (raisedEl) raisedEl.textContent = `$${raised.toLocaleString()}`;
    if (progressBar) {
      progressBar.style.width = `${Math.min((raised / GOAL) * 100, 100)}%`;
    }
  })
  .catch(error => {
    console.error("Could not load live fundraising data:", error);
  });

// Race countdown target: April 25, 2027
const raceDate = new Date("2027-04-25T07:00:00-07:00");

function updateCountdown() {
  const diff = Math.max(0, raceDate.getTime() - Date.now());
  const totalSeconds = Math.floor(diff / 1000);
  const days = Math.floor(totalSeconds / 86400);
  const hours = Math.floor((totalSeconds % 86400) / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  const values = {
    "countdown-days": days.toLocaleString(),
    "countdown-hours": String(hours).padStart(2, "0"),
    "countdown-minutes": String(minutes).padStart(2, "0"),
    "countdown-seconds": String(seconds).padStart(2, "0")
  };
  Object.entries(values).forEach(([id, value]) => {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  });
}
updateCountdown();
setInterval(updateCountdown, 1000);

// RUNALYZE training stats
fetch("training-data.json")
  .then(response => response.json())
  .then(data => {
    document.getElementById("total-miles").textContent =
      data.miles.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

    document.getElementById("run-count").textContent =
      data.runs.toLocaleString();

    if (data.latest_run) {
      document.getElementById("last-run").textContent =
        `${data.latest_run.distance.toFixed(2)} mi`;

      const lastRunDate = document.getElementById("last-run-date");
      if (lastRunDate) {
        const date = new Date(`${data.latest_run.date}T12:00:00`);
        lastRunDate.textContent = date.toLocaleDateString(undefined, {
          month: "short",
          day: "numeric"
        });
      }
    }
  })
  .catch(error => {
    console.error("Could not load RUNALYZE training data:", error);
  });

// Donor acknowledgement: gold course + numbered bibs.
// Donor names come from donors.json (hand-edited, oldest first). The raised total comes from fundraising-data.json.
function renderDonors(list, raised) {
  const track = document.getElementById("course-track");
  if (!track) return;
  const prog = document.getElementById("course-progress");
  const marks = document.getElementById("course-marks");
  const wall = document.getElementById("bibs");
  const NS = "http://www.w3.org/2000/svg";
  const L = track.getTotalLength();
  const clamp = v => Math.max(0, Math.min(1, v));
  const mk = (tag, attrs, text) => {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (text) e.textContent = text;
    return e;
  };
  marks.replaceChildren();
  wall.replaceChildren();
  const latest = [];
  let cum = 0;
  list.forEach((d, i) => {
    const entry = typeof d === "string" ? { name: d } : (d || {});
    cum += amountOf(entry);
    const name = String(entry.name || "").trim() || "Anonymous";
    const p = track.getPointAtLength(L * clamp(cum / GOAL));
    const isLatest = i >= list.length - 2;
    if (isLatest) {
      latest.push(`#${i + 1} ${name}`);
      const up = i % 2 === 0, w = 104, sy = up ? p.y - 52 : p.y + 26;
      const sx = Math.max(4, Math.min(676 - w, p.x - w / 2));
      marks.appendChild(mk("line", { class: "course-stem", x1: p.x, y1: p.y, x2: p.x, y2: up ? sy + 24 : sy }));
      marks.appendChild(mk("rect", { class: "course-sign", x: sx, y: sy, width: w, height: 24, rx: 4 }));
      marks.appendChild(mk("text", { class: "course-text", x: sx + w / 2, y: sy + 16, "text-anchor": "middle" }, `#${i + 1} ${name}`.slice(0, 16)));
    }
    marks.appendChild(mk("circle", { class: "course-dot", cx: p.x, cy: p.y, r: isLatest ? 6 : 4.5 }));
    const bib = document.createElement("div");
    bib.className = "bib";
    const s = document.createElement("small"); s.textContent = "Big Sur 2027";
    const b = document.createElement("b"); b.textContent = `#${i + 1}`;
    const n = document.createElement("span"); n.textContent = name;
    bib.append(s, b, n);
    wall.appendChild(bib);
  });
  const frac = clamp(raised / GOAL);
  prog.style.display = frac > 0 ? "" : "none";
  prog.setAttribute("stroke-dasharray", `${L * frac} ${L}`);
  const empty = document.createElement("div");
  empty.className = "bib bib-empty";
  empty.textContent = "Your name here";
  wall.appendChild(empty);
  const count = list.length;
  if (count > 0) {
    document.getElementById("donors-title").textContent = `Cheered on by ${count} ${count === 1 ? "person" : "people"} so far.`;
    document.getElementById("donors-sub").textContent = `$${raised.toLocaleString()} raised, mile ${(frac * 26.2).toFixed(1)} of 26.2`;
    document.getElementById("course-latest").textContent = `Latest: ${latest.reverse().join(", ")}`;
  }
}

// Dollar amount from an entry; tolerates "$100", "100", or a missing amount.
function amountOf(entry) {
  return Number(String(entry && entry.amount != null ? entry.amount : 0).replace(/[^0-9.]/g, "")) || 0;
}

// Load the hand-edited donor list and the live total, then draw the section.
// donors.json can be a plain list, or { "donors": [...] }. Names alone are fine.
Promise.allSettled([
  fetch("fundraising-data.json", { cache: "no-store" }).then(r => r.json()),
  fetch("donors.json", { cache: "no-store" }).then(r => r.json())
]).then(([fund, donors]) => {
  if (donors.status !== "fulfilled") console.error("Could not read donors.json (check for typos in the file):", donors.reason);
  const raw = donors.status === "fulfilled" ? donors.value : [];
  const list = Array.isArray(raw) ? raw : (raw && Array.isArray(raw.donors) ? raw.donors : []);
  const listed = list.reduce((sum, d) => sum + amountOf(typeof d === "string" ? {} : d), 0);
  const live = fund.status === "fulfilled" ? Number(fund.value.raised) || 0 : 0;
  renderDonors(list, Math.max(live, listed));
});
