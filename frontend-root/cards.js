// ── App cards ─────────────────────────────────────────────────────────────────
// Add or update entries here to change what appears on the dashboard.
// Set live: true and add an href when an app is ready to use.
// Use icon: "emoji" for emoji, or favicon: "domain.com" to pull the site's icon.

const apps = [
  // ── Communication & Daily ───────────────────────────────────────────────────
  {
    favicon: "whatsapp.com",
    title: "WhatsApp",
    desc: "Messages and chats without picking up your phone.",
    href: "https://web.whatsapp.com",
    live: true,
  },
  {
    favicon: "calendar.google.com",
    title: "Google Calendar",
    desc: "Your schedule at a glance.",
    href: "https://calendar.google.com",
    live: true,
  },

  // ── Productivity & Dev ──────────────────────────────────────────────────────
  {
    favicon: "drive.google.com",
    title: "Google Drive",
    desc: "Files, docs, and everything in between.",
    href: "https://drive.google.com",
    live: true,
  },
  {
    favicon: "github.com",
    title: "GitHub",
    desc: "Repos, pull requests, and code.",
    href: "https://github.com",
    live: true,
  },
  {
    favicon: "aws.amazon.com",
    title: "AWS Console",
    desc: "Manage your cloud infrastructure.",
    href: "https://console.aws.amazon.com",
    live: true,
  },
  {
    icon: "🔐",
    title: "Password Manager",
    desc: "Encrypted password vault — all crypto happens in your browser.",
    href: "/passwords",
    live: true,
  },

  // ── Entertainment ───────────────────────────────────────────────────────────
  {
    favicon: "open.spotify.com",
    title: "Spotify",
    desc: "Music, podcasts, and playlists.",
    href: "https://open.spotify.com",
    live: true,
  },
  {
    favicon: "youtube.com",
    title: "YouTube",
    desc: "Videos, tutorials, and everything else.",
    href: "https://youtube.com",
    live: true,
  },
  {
    favicon: "chess.com",
    title: "Chess.com",
    desc: "Play, learn, and improve your game.",
    href: "https://chess.com",
    live: true,
  },
];

// ── Render ────────────────────────────────────────────────────────────────────

function iconHtml(app) {
  if (app.favicon) {
    return `<img class="card-favicon" src="https://www.google.com/s2/favicons?domain=${app.favicon}&sz=64" alt="${app.title} icon" />`;
  }
  return `<div class="card-icon">${app.icon}</div>`;
}

function renderCards() {
  const grid = document.getElementById("grid");

  grid.innerHTML = apps.map((app) => {
    if (app.live) {
      return `
        <a class="card" href="${app.href}">
          ${iconHtml(app)}
          <div class="card-title">${app.title}</div>
          <div class="card-desc">${app.desc}</div>
          <span class="badge badge-live">Open</span>
        </a>`;
    }
    return `
      <div class="card inactive">
        ${iconHtml(app)}
        <div class="card-title">${app.title}</div>
        <div class="card-desc">${app.desc}</div>
        <span class="badge badge-soon">Coming soon</span>
      </div>`;
  }).join("");
}

renderCards();
