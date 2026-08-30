/**
 * E-Career Autofill — Ashby ATS content script
 *
 * Pre-fills Ashby application forms with data from the user's E-Career
 * profile. The user MUST click "Submit" themselves — we never auto-submit.
 *
 * Ashby application pages: https://jobs.ashbyhq.com/{company}/application?jobId={id}
 * Form renders React inputs inside ._form or [data-testid] containers.
 */

const API_BASE = "https://jobs.usamif.com/api/v1";

const FIELD_MAP = {
  first_name: ['input[name="first_name"]', 'input[name="_systemfield_name"]', 'input[placeholder*="First"]'],
  last_name: ['input[name="last_name"]', 'input[placeholder*="Last"]'],
  email: ['input[name="email"]', 'input[name="_systemfield_email"]', 'input[type="email"]'],
  phone: ['input[name="phone"]', 'input[name="_systemfield_phone"]', 'input[type="tel"]'],
  location: ['input[name="location"]', 'input[name="_systemfield_location"]', 'input[placeholder*="Location"]'],
  linkedin: ['input[name="linkedin"]', 'input[name="_systemfield_linkedin"]', 'input[placeholder*="LinkedIn"]'],
  portfolio: ['input[name="website"]', 'input[name="portfolio"]', 'input[placeholder*="Website"]', 'input[placeholder*="Portfolio"]'],
  current_company: ['input[name="company"]', 'input[name="currentCompany"]', 'input[placeholder*="Company"]'],
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

  const nameParts = (profile.name || "").split(" ");
  const mapping = {
    first_name: profile.first_name || nameParts[0] || "",
    last_name: profile.last_name || nameParts.slice(1).join(" ") || "",
    email: profile.email,
    location: profile.location,
    portfolio: profile.portfolio_url,
    current_company: profile.current_company,
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
