// ── Entries ───────────────────────────────────────────────────────────────────
// Vault CRUD, search/filter, and rendering.
// Depends on: app.js (state), crypto.js (decrypt, encrypt, esc)

async function loadEntries() {
  const el = document.getElementById("entries-body");
  el.innerHTML = '<div class="loading">Loading…</div>';

  try {
    const res = await fetch(`${API_URL}/entries`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    if (!res.ok) throw new Error("Fetch failed");

    const { entries } = await res.json();

    const decrypted = await Promise.all(
      entries.map(async (e) => {
        const plain = await decrypt(e.encrypted_data, e.iv, encryptionKey);
        return { id: e.id, ...plain };
      })
    );

    allEntries = decrypted;
    filterEntries(); // re-apply any active search after a reload
  } catch (e) {
    el.innerHTML = '<div class="err">Could not load entries — ' + e.message + "</div>";
  }
}

// ── Search ────────────────────────────────────────────────────────────────────

function filterEntries() {
  const q = document.getElementById("search").value.trim().toLowerCase();
  if (!q) {
    renderEntries(allEntries);
    return;
  }
  const filtered = allEntries.filter((e) =>
    (e.site || "").toLowerCase().includes(q) ||
    (e.username || "").toLowerCase().includes(q) ||
    (e.description || "").toLowerCase().includes(q)
  );
  renderEntries(filtered);
}

function renderEntries(entries) {
  const el = document.getElementById("entries-body");
  document.getElementById("entry-count").textContent =
    entries.length === allEntries.length
      ? entries.length
      : `${entries.length} / ${allEntries.length}`;

  if (entries.length === 0) {
    const msg = allEntries.length === 0
      ? "No entries yet — add your first password above"
      : "No entries match your search";
    el.innerHTML = `<div class="empty">${msg}</div>`;
    return;
  }

  const rows = entries
    .map(
      (e) => `
      <tr>
        <td>${esc(e.site || "—")}</td>
        <td>${esc(e.username || "—")}</td>
        <td>
          <div class="pw-cell">
            <span class="pw-text" id="pw-${e.id}">••••••••</span>
            <button class="reveal-btn" onclick="toggleReveal('${e.id}')" title="Show/hide">👁</button>
            <button class="copy-btn" onclick="copyPw('${e.id}')" title="Copy">⎘</button>
          </div>
        </td>
        <td class="muted">${esc(e.description || "")}</td>
        <td>
          <button class="btn btn-danger" onclick="deleteEntry('${e.id}')">Delete</button>
        </td>
      </tr>`
    )
    .join("");

  el.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Site / App</th>
          <th>Username</th>
          <th>Password</th>
          <th>Description</th>
          <th></th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>`;
}

// ── Add entry ─────────────────────────────────────────────────────────────────

function toggleAddForm() {
  const card = document.getElementById("add-card");
  card.style.display = card.style.display === "none" ? "block" : "none";
  if (card.style.display === "block") {
    document.getElementById("f-site").focus();
  }
}

function cancelAdd() {
  document.getElementById("add-card").style.display = "none";
  ["f-site", "f-user", "f-pass", "f-desc"].forEach(
    (id) => (document.getElementById(id).value = "")
  );
  document.getElementById("save-error").textContent = "";
}

async function saveEntry() {
  const site = document.getElementById("f-site").value.trim();
  const username = document.getElementById("f-user").value.trim();
  const password = document.getElementById("f-pass").value;
  const description = document.getElementById("f-desc").value.trim();
  const errEl = document.getElementById("save-error");
  const btn = document.getElementById("save-btn");

  errEl.textContent = "";
  if (!site || !username || !password) {
    errEl.textContent = "Site, username and password are required";
    return;
  }

  btn.disabled = true;
  btn.textContent = "Saving…";

  try {
    const { iv, ciphertext } = await encrypt(
      { site, username, password, description },
      encryptionKey
    );

    const res = await fetch(`${API_URL}/entries`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${authToken}`,
      },
      body: JSON.stringify({ encrypted_data: ciphertext, iv }),
    });

    if (!res.ok) throw new Error("Save failed");

    cancelAdd();
    await loadEntries();
    showToast("Entry saved ✓");
  } catch (e) {
    errEl.textContent = e.message;
  } finally {
    btn.disabled = false;
    btn.textContent = "Save";
  }
}

// ── Delete entry ──────────────────────────────────────────────────────────────

async function deleteEntry(id) {
  if (!confirm("Delete this entry? This cannot be undone.")) return;

  try {
    await fetch(`${API_URL}/entries/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${authToken}` },
    });
    await loadEntries();
    showToast("Entry deleted");
  } catch (e) {
    alert("Delete failed: " + e.message);
  }
}

// ── Password reveal / copy ────────────────────────────────────────────────────
// Passwords are looked up from allEntries in memory rather than stored in the
// DOM — this avoids any issue with special characters in onclick attributes
// and keeps plaintext passwords out of the page source.

function toggleReveal(id) {
  const entry = allEntries.find((e) => e.id === id);
  const el = document.getElementById(`pw-${id}`);
  el.textContent = el.textContent === "••••••••" ? (entry ? entry.password : "") : "••••••••";
}

async function copyPw(id) {
  const entry = allEntries.find((e) => e.id === id);
  if (!entry) return;
  try {
    await navigator.clipboard.writeText(entry.password);
    showToast("Password copied ✓");
  } catch {
    alert("Copy failed — use the reveal button instead");
  }
}

// ── Toast ─────────────────────────────────────────────────────────────────────

function showToast(msg) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 2500);
}
