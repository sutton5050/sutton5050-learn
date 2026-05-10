// ── Auth ──────────────────────────────────────────────────────────────────────
// Login and sign-out logic.
// Depends on: app.js (state), crypto.js (deriveVerificationHash, deriveEncryptionKey),
//             entries.js (loadEntries)

async function unlock() {
  const pw = document.getElementById("master-pw").value;
  const btn = document.getElementById("unlock-btn");
  const errEl = document.getElementById("login-error");
  errEl.textContent = "";

  if (!pw) { errEl.textContent = "Enter your master password"; return; }
  if (!encryptionSalt) { errEl.textContent = "API not ready — reload the page"; return; }

  btn.disabled = true;
  btn.textContent = "Unlocking…";

  try {
    const verHash = await deriveVerificationHash(pw);

    const res = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ verification_hash: verHash }),
    });

    if (!res.ok) {
      errEl.textContent = "Incorrect password";
      return;
    }

    const { token } = await res.json();
    authToken = token;

    // Derive the AES key — stays in memory only, never written anywhere
    encryptionKey = await deriveEncryptionKey(pw, encryptionSalt);

    document.getElementById("login").style.display = "none";
    document.getElementById("vault").style.display = "block";
    loadEntries();
  } catch (e) {
    errEl.textContent = "Login failed — " + e.message;
  } finally {
    btn.disabled = false;
    btn.textContent = "Unlock";
  }
}

function signOut() {
  authToken = "";
  encryptionKey = null;
  allEntries = [];
  document.getElementById("master-pw").value = "";
  document.getElementById("search").value = "";
  document.getElementById("vault").style.display = "none";
  document.getElementById("login").style.display = "flex";
  document.getElementById("master-pw").focus();
}
