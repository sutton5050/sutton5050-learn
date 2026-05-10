// ── App cards ─────────────────────────────────────────────────────────────────
// Add or update entries here to change what appears on the dashboard.
// Set live: true and add an href when an app is ready to use.

const apps = [
  {
    icon: "🔐",
    title: "Password Manager",
    desc: "Encrypted password vault — all crypto happens in your browser.",
    href: "/passwords",
    live: true,
  },
  {
    icon: "📅",
    title: "Google Calendar",
    desc: "Quick view of upcoming events without opening a new tab.",
    live: false,
  },
  {
    icon: "📊",
    title: "Stats & Metrics",
    desc: "Personal dashboard — finance, fitness, or whatever matters next.",
    live: false,
  },
  {
    icon: "🔗",
    title: "Quick Links",
    desc: "Frequently used tools and resources in one place.",
    live: false,
  },
];

// ── Render ────────────────────────────────────────────────────────────────────

function renderCards() {
  const grid = document.getElementById("grid");

  grid.innerHTML = apps.map((app) => {
    if (app.live) {
      return `
        <a class="card" href="${app.href}">
          <div class="card-icon">${app.icon}</div>
          <div class="card-title">${app.title}</div>
          <div class="card-desc">${app.desc}</div>
          <span class="badge badge-live">Open</span>
        </a>`;
    }
    return `
      <div class="card inactive">
        <div class="card-icon">${app.icon}</div>
        <div class="card-title">${app.title}</div>
        <div class="card-desc">${app.desc}</div>
        <span class="badge badge-soon">Coming soon</span>
      </div>`;
  }).join("");
}

renderCards();
