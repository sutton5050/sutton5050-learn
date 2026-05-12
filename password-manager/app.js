// ── State ─────────────────────────────────────────────────────────────────────
// Shared across auth.js and entries.js via the browser's global scope.
// The encryptionKey is a CryptoKey object — it never leaves JS memory.

let API_URL = "";
let encryptionSalt = "";
let encryptionKey = null;
let authToken = "";
let allEntries = [];

// ── Boot ──────────────────────────────────────────────────────────────────────
// Runs immediately on page load. Fetches the API URL from config.json
// (written by CI) and the encryption salt from the API.

(async () => {
  try {
    const cfg = await fetch("config.json").then((r) => r.json());
    API_URL = cfg.apiUrl.replace(/\/$/, "");
    const authCfg = await fetch(`${API_URL}/auth/config`).then((r) => r.json());
    encryptionSalt = authCfg.encryption_salt;
  } catch (e) {
    document.getElementById("login-error").textContent =
      "Could not reach API — check config.json";
  }
})();
