const API_BASE = "https://jobs.usamif.com/api/v1";

async function checkConnection() {
  const { eck_token: token } = await chrome.storage.local.get("eck_token");
  const statusEl = document.getElementById("status");
  const loginForm = document.getElementById("login-form");
  const connectedView = document.getElementById("connected-view");

  if (!token) {
    statusEl.className = "status disconnected";
    statusEl.textContent = "Not connected";
    loginForm.style.display = "block";
    connectedView.style.display = "none";
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/auth/extension/profile/`, {
      headers: { Authorization: `ExtToken ${token}` },
    });
    if (!res.ok) throw new Error("Invalid token");
    const data = await res.json();
    const profile = data.data || data;

    statusEl.className = "status connected";
    statusEl.textContent = "Connected";
    loginForm.style.display = "none";
    connectedView.style.display = "block";
    document.getElementById("profile-name").textContent =
      profile.full_name || profile.email || "Connected";
  } catch {
    statusEl.className = "status disconnected";
    statusEl.textContent = "Token expired or invalid";
    loginForm.style.display = "block";
    connectedView.style.display = "none";
    await chrome.storage.local.remove("eck_token");
  }
}

document.getElementById("connect").addEventListener("click", async () => {
  const token = document.getElementById("token").value.trim();
  if (!token || !token.startsWith("eck_")) {
    alert("Please enter a valid extension token (starts with eck_).");
    return;
  }
  await chrome.storage.local.set({ eck_token: token });
  checkConnection();
});

document.getElementById("disconnect").addEventListener("click", async () => {
  await chrome.storage.local.remove("eck_token");
  checkConnection();
});

checkConnection();
