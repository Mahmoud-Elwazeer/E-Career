/**
 * E-Career Autofill — Lever ATS content script
 *
 * Pre-fills Lever application forms with data from the user's E-Career
 * profile. The user MUST click "Submit" themselves — we never auto-submit.
 *
 * Lever application pages: https://jobs.lever.co/{company}/{posting-id}/apply
 * Form uses <input> fields inside .application-form or .postings-btn-wrapper.
 */

const API_BASE = "https://jobs.usamif.com/api/v1";

const FIELD_MAP = {
  full_name: ['input[name="name"]', 'input[placeholder*="Full name"]', 'input[placeholder*="full name"]'],
  email: ['input[name="email"]', 'input[type="email"]'],
  phone: ['input[name="phone"]', 'input[type="tel"]'],
  current_company: ['input[name="org"]', 'input[placeholder*="Current company"]', 'input[placeholder*="company"]'],
  location: ['input[name="location"]', 'input[placeholder*="Location"]', 'input[placeholder*="location"]'],
  linkedin: ['input[name="urls[LinkedIn]"]', 'input[placeholder*="LinkedIn"]'],
  portfolio: ['input[name="urls[Portfolio]"]', 'input[placeholder*="Portfolio"]', 'input[placeholder*="Website"]'],
};

function findField(selectors) {
  for (const sel of selectors) {
    const el = document.querySelector(sel);
    if (el) return el;
  }
  return null;
}

function fillField(el, value) {
  if (!el || !value) return false;
  const nativeSet = Object.getOwnPropertyDescriptor(
    window.HTMLInputElement.prototype, "value"
  ).set;
  nativeSet.call(el, value);
  el.dispatchEvent(new Event("input", { bubbles: true }));
  el.dispatchEvent(new Event("change", { bubbles: true }));
  return true;
}

async function fetchProfile(token) {
  const res = await fetch(`${API_BASE}/auth/extension/profile/`, {
    headers: { Authorization: `ExtToken ${token}` },
  });
  if (!res.ok) return null;
  const data = await res.json();
  return data.data || data;
}

function createBanner(filled) {
  const banner = document.createElement("div");
  banner.style.cssText =
    "position:fixed;top:12px;right:12px;z-index:99999;padding:12px 18px;" +
    "background:#2563eb;color:#fff;border-radius:10px;font-family:system-ui;" +
    "font-size:14px;box-shadow:0 4px 12px rgba(0,0,0,.15);display:flex;" +
    "align-items:center;gap:8px;";
  banner.textContent = `E-Career: ${filled} fields pre-filled. Review & submit manually.`;

  const close = document.createElement("button");
  close.textContent = "×";
  close.style.cssText = "background:none;border:none;color:#fff;font-size:18px;cursor:pointer;padding:0 0 0 8px;";
  close.onclick = () => banner.remove();
  banner.appendChild(close);

  document.body.appendChild(banner);
  setTimeout(() => banner.remove(), 8000);
}

async function main() {
  const { eck_token: token } = await chrome.storage.local.get("eck_token");
  if (!token) return;

  const profile = await fetchProfile(token);
  if (!profile) return;

  const mapping = {
    full_name: profile.name || `${profile.first_name || ""} ${profile.last_name || ""}`.trim(),
    email: profile.email,
    current_company: profile.current_company,
    location: profile.location,
    portfolio: profile.portfolio_url,
  };

  let filled = 0;
  for (const [key, value] of Object.entries(mapping)) {
    const selectors = FIELD_MAP[key];
    if (!selectors) continue;
    const el = findField(selectors);
    if (el && !el.value) {
      if (fillField(el, value)) filled++;
    }
  }

  if (filled > 0) {
    createBanner(filled);
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => setTimeout(main, 500));
} else {
  setTimeout(main, 500);
}
