/**
 * E-Career Autofill — Greenhouse ATS content script
 *
 * Pre-fills Greenhouse application forms with data from the user's E-Career
 * profile. The user MUST click "Submit" themselves — we never auto-submit.
 */

const API_BASE = "https://jobs.usamif.com/api/v1";

const FIELD_MAP = {
  first_name: ['input[name="first_name"]', '#first_name'],
  last_name: ['input[name="last_name"]', '#last_name'],
  email: ['input[name="email"]', '#email'],
  phone: ['input[name="phone"]', '#phone'],
  location: ['input[name="location"]', '#job_application_location'],
  linkedin_profile: ['input[name="job_application[urls][LinkedIn]"]', 'input[data-source="LinkedIn"]'],
  website: ['input[name="job_application[urls][Portfolio]"]', 'input[data-source="Portfolio"]'],
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
    first_name: profile.first_name,
    last_name: profile.last_name,
    email: profile.email,
    phone: profile.phone,
    linkedin_profile: profile.linkedin_url,
    website: profile.portfolio_url,
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
