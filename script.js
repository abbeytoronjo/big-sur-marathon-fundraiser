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
  const now = new Date();
  const diff = raceDate - now;
  const days = Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
  const el = document.getElementById("countdown-days");
  if (el) el.textContent = days.toLocaleString();
}
updateCountdown();
setInterval(updateCountdown, 60 * 60 * 1000);

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
