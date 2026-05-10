// ── Crypto ───────────────────────────────────────────────────────────────────
// All key derivation, encryption, and decryption.
// No dependencies on other app files — pure Web Crypto API + helpers.

async function deriveVerificationHash(password) {
  const enc = new TextEncoder();
  const km = await crypto.subtle.importKey(
    "raw", enc.encode(password), "PBKDF2", false, ["deriveBits"]
  );
  const bits = await crypto.subtle.deriveBits(
    { name: "PBKDF2", salt: enc.encode("verification-salt-v1"), iterations: 600000, hash: "SHA-256" },
    km, 256
  );
  return Array.from(new Uint8Array(bits))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

async function deriveEncryptionKey(password, saltHex) {
  const enc = new TextEncoder();
  const km = await crypto.subtle.importKey(
    "raw", enc.encode(password), "PBKDF2", false, ["deriveKey"]
  );
  return crypto.subtle.deriveKey(
    { name: "PBKDF2", salt: hexToBytes(saltHex), iterations: 600000, hash: "SHA-256" },
    km,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt", "decrypt"]
  );
}

async function encrypt(data, key) {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ct = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv },
    key,
    new TextEncoder().encode(JSON.stringify(data))
  );
  return { iv: toB64(iv), ciphertext: toB64(new Uint8Array(ct)) };
}

async function decrypt(ctB64, ivB64, key) {
  const plain = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv: fromB64(ivB64) },
    key,
    fromB64(ctB64)
  );
  return JSON.parse(new TextDecoder().decode(plain));
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function hexToBytes(hex) {
  const b = new Uint8Array(hex.length / 2);
  for (let i = 0; i < hex.length; i += 2)
    b[i / 2] = parseInt(hex.slice(i, i + 2), 16);
  return b;
}

function toB64(bytes) {
  return btoa(String.fromCharCode(...bytes));
}

function fromB64(b64) {
  return Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
}

// Escapes a string for safe insertion into innerHTML
function esc(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
