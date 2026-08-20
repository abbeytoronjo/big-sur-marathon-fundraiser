// Fundraising settings
const GOAL = 2000;

// Change this number as donations come in, or later connect it to your fundraising platform API.
const RAISED = 0;

document.getElementById("raised").textContent = `$${RAISED.toLocaleString()}`;
document.getElementById("progress-bar").style.width = `${Math.min((RAISED / GOAL) * 100, 100)}%`;

// Race countdown target: April 25, 2027
const raceDate = new Date("2027-04-25T07:00:00-07:00");

// Placeholder Strava stats until OAuth/API is connected.
document.getElementById("total-miles").textContent = "—";
document.getElementById("run-count").textContent = "—";
document.getElementById("last-run").textContent = "—";
