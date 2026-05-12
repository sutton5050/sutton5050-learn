// ── Dashboard Vault ───────────────────────────────────────────────────────────
// Credential-copy mode for the dashboard.
// When the toggle is on, clicking a card fetches the matching password from the
// vault, copies it to the clipboard, then navigates to the site.
//
// Depends on: /passwords/crypto.js (deriveVerificationHash, deriveEncryptionKey,
//             encrypt, decrypt)

let dashApiUrl = "";
let dashSalt = "";
let dashToken = "";
let dashEncKey = null;
let _pendingApp = null;  // app waiting for auth to complete
let _pendingHref = "";   // href held while add-modal is open

// ── Init ──────────────────────────────────────────────────────────────────────
// Restore toggle state immediately (sync) so there's no visible flash,
// then fetch the API URL and encryption salt in the background.

const _toggleOn = localStorage.getItem("credMode") === "1";
document.getElementById("mode-toggle").checked = _toggleOn;
document.getElementById("toggle-label").textContent = _toggleOn ? "Need credentials" : "Logged in";

(async () => {
  try {
    const cfg = await fetch("/passwords/config.json").then((r) => r.json());
    dashApiUrl = cfg.apiUrl.replace(/\/$/, "");
    const authCfg = await fetch(`${dashApiUrl}/auth/config`).then((r) => r.json());
    dashSalt = authCfg.encryption_salt;
  } catch (e) {
    console.warn("Vault API unreachable:", e.message);
  }
})();

// ── Toggle ────────────────────────────────────────────────────────────────────

function onToggleChange() {
  const on = document.getElementById("mode-toggle").checked;
  document.getElementById("toggle-label").textContent = on ? "Need credentials" : "Logged in";
  localStorage.setItem("credMode", on ? "1" : "0");
}

// ── Card click handler ────────────────────────────────────────────────────────
// Called by the delegated click listener in cards.js.
// If toggle is off: returns immediately so normal <a> navigation takes over.
// If toggle is on:  prevents navigation and runs the credential flow.

async function handleCardClick(event, app) {
  if (app.noCredentials) return;

  const on = document.getElementById("mode-toggle").checked;
  if (!on) return;

  event.preventDefault();

  if (!dashApiUrl) {
    showDashToast("Vault API unavailable — opening site anyway");
    setTimeout(() => { window.location.href = app.href; }, 1200);
    return;
  }

  if (!dashToken || !dashEncKey) {
    _pendingApp = app;
    openAuthModal();
    return;
  }

  await doCredentialFlow(app);
}

// ── Credential flow ───────────────────────────────────────────────────────────

async function doCredentialFlow(app) {
  try {
    const entry = await findCredential(app.search);
    if (entry) {
      await navigator.clipboard.writeText(entry.password);
      showDashToast("Password copied ✓");
      setTimeout(() => { window.location.href = app.href; }, 700);
    } else {
      openAddModal(app);
    }
  } catch (e) {
    showDashToast("Could not fetch credentials — opening site anyway");
    setTimeout(() => { window.location.href = app.href; }, 1200);
  }
}

// ── Auth modal ────────────────────────────────────────────────────────────────

function openAuthModal() {
  document.getElementById("modal-pw").value = "";
  document.getElementById("modal-error").textContent = "";
  document.getElementById("modal-unlock-btn").disabled = false;
  document.getElementById("modal-unlock-btn").textContent = "Unlock";
  document.getElementById("auth-modal").style.display = "flex";
  setTimeout(() => document.getElementById("modal-pw").focus(), 50);
}

function closeAuthModal() {
  document.getElementById("auth-modal").style.display = "none";
  _pendingApp = null;
}

async function modalUnlock() {
  const pw = document.getElementById("modal-pw").value;
  const errEl = document.getElementById("modal-error");
  const btn = document.getElementById("modal-unlock-btn");
  errEl.textContent = "";

  if (!pw) { errEl.textContent = "Enter your master password"; return; }
  if (!dashSalt) { errEl.textContent = "API not ready — reload the page"; return; }

  btn.disabled = true;
  btn.textContent = "Unlocking…";

  try {
    const verHash = await deriveVerificationHash(pw);
    const res = await fetch(`${dashApiUrl}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ verification_hash: verHash }),
    });

    if (!res.ok) {
      errEl.textContent = "Incorrect password";
      btn.disabled = false;
      btn.textContent = "Unlock";
      return;
    }

    const { token } = await res.json();
    dashToken = token;
    dashEncKey = await deriveEncryptionKey(pw, dashSalt);

    document.getElementById("auth-modal").style.display = "none";
    document.getElementById("modal-pw").value = "";

    if (_pendingApp) {
      const app = _pendingApp;
      _pendingApp = null;
      await doCredentialFlow(app);
    }
  } catch (e) {
    errEl.textContent = "Login failed — " + e.message;
    btn.disabled = false;
    btn.textContent = "Unlock";
  }
}

// ── Add credentials modal ─────────────────────────────────────────────────────

function openAddModal(app) {
  _pendingHref = app.href;
  document.getElementById("add-modal-title").textContent = `Add credentials for ${app.title}`;
  document.getElementById("add-site").value = app.title;
  document.getElementById("add-user").value = "";
  document.getElementById("add-pass").value = "";
  document.getElementById("add-error").textContent = "";
  document.getElementById("add-save-btn").disabled = false;
  document.getElementById("add-save-btn").textContent = "Save & Continue";
  document.getElementById("add-modal").style.display = "flex";
  setTimeout(() => document.getElementById("add-user").focus(), 50);
}

async function modalSaveAndGo() {
  const site = document.getElementById("add-site").value.trim();
  const username = document.getElementById("add-user").value.trim();
  const password = document.getElementById("add-pass").value;
  const errEl = document.getElementById("add-error");
  const btn = document.getElementById("add-save-btn");

  errEl.textContent = "";
  if (!username || !password) {
    errEl.textContent = "Username and password are required";
    return;
  }

  btn.disabled = true;
  btn.textContent = "Saving…";

  try {
    const { iv, ciphertext } = await encrypt(
      { site, username, password, description: "" },
      dashEncKey
    );
    const res = await fetch(`${dashApiUrl}/entries`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${dashToken}`,
      },
      body: JSON.stringify({ encrypted_data: ciphertext, iv }),
    });
    if (!res.ok) throw new Error("Save failed");

    await navigator.clipboard.writeText(password);
    showDashToast("Saved & password copied ✓");
    document.getElementById("add-modal").style.display = "none";
    setTimeout(() => { window.location.href = _pendingHref; }, 700);
  } catch (e) {
    errEl.textContent = e.message;
    btn.disabled = false;
    btn.textContent = "Save & Continue";
  }
}

function modalSkip() {
  document.getElementById("add-modal").style.display = "none";
  window.location.href = _pendingHref;
}

// ── Vault API helpers ─────────────────────────────────────────────────────────

async function findCredential(searchTerm) {
  const res = await fetch(`${dashApiUrl}/entries`, {
    headers: { Authorization: `Bearer ${dashToken}` },
  });
  if (!res.ok) throw new Error("Fetch failed");
  const { entries } = await res.json();

  const decrypted = await Promise.all(
    entries.map(async (e) => {
      const plain = await decrypt(e.encrypted_data, e.iv, dashEncKey);
      return { id: e.id, ...plain };
    })
  );

  const q = searchTerm.toLowerCase();
  return (
    decrypted.find(
      (e) =>
        (e.site || "").toLowerCase().includes(q) ||
        (e.description || "").toLowerCase().includes(q)
    ) || null
  );
}

// ── Toast ─────────────────────────────────────────────────────────────────────

function showDashToast(msg) {
  const el = document.getElementById("dash-toast");
  el.textContent = msg;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 2500);
}
