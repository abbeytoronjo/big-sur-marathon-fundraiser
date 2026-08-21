// Fundraising settings
const GOAL = 2000;

// Update this number as donations come in. We can automate this later if a usable fundraising-data source is available.
const RAISED = 0;

document.getElementById("raised").textContent = `$${RAISED.toLocaleString()}`;
document.getElementById("progress-bar").style.width = `${Math.min((RAISED / GOAL) * 100, 100)}%`;

// Race countdown target: April 25, 2027
const raceDate = new Date("2027-04-25T07:00:00-07:00");

function updateCountdown() {
  const now = new Date();
  const diff = raceDate - now;
  const days = Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
  const el = document.getElementById("countdown-days");
  if (el) el.textContent = days.toLocaleString();
}
updateCountdown();
setInterval(updateCountdown, 60 * 60 * 1000);

// Placeholder Strava stats until OAuth/API is connected.
document.getElementById("total-miles").textContent = "—";
document.getElementById("run-count").textContent = "—";
document.getElementById("last-run").textContent = "—";
