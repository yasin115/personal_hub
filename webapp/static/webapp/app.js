"use strict";

/* ------------------------------------------------------------------
 * Telegram Mini App detection + theme sync
 * ------------------------------------------------------------------ */
const tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;
const IS_TELEGRAM = !!(tg && tg.initData);

if (tg) {
  tg.ready();
  tg.expand();
  applyTelegramTheme(tg.themeParams || {});
  tg.onEvent && tg.onEvent("themeChanged", () => applyTelegramTheme(tg.themeParams || {}));
}

function applyTelegramTheme(t) {
  const root = document.documentElement.style;
  const map = {
    "--tg-bg-color": t.bg_color,
    "--tg-secondary-bg-color": t.secondary_bg_color,
    "--tg-text-color": t.text_color,
    "--tg-hint-color": t.hint_color,
    "--tg-link-color": t.link_color,
    "--tg-button-color": t.button_color,
    "--tg-button-text-color": t.button_text_color,
  };
  Object.entries(map).forEach(([key, value]) => {
    if (value) root.setProperty(key, "#" + value.replace("#", ""));
  });
}

if (IS_TELEGRAM) {
  document.getElementById("brandSubtitle").textContent = "متصل به مینی‌اپ تلگرام";
}

/* ------------------------------------------------------------------
 * Tiny JWT-based API client (works identically inside Telegram's
 * webview or a normal browser -- same JSON API either way)
 * ------------------------------------------------------------------ */
const ACCESS_KEY = "ph_access_token";
const REFRESH_KEY = "ph_refresh_token";

const getAccess = () => localStorage.getItem(ACCESS_KEY);
const getRefresh = () => localStorage.getItem(REFRESH_KEY);
const setTokens = (access, refresh) => {
  if (access) localStorage.setItem(ACCESS_KEY, access);
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
};
const clearTokens = () => {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
};

async function refreshAccessToken() {
  const refresh = getRefresh();
  if (!refresh) return false;
  const res = await fetch("/api/token/refresh/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });
  if (!res.ok) return false;
  const data = await res.json();
  setTokens(data.access, data.refresh); // ROTATE_REFRESH_TOKENS is on: server issues a new refresh token too
  return true;
}

async function api(path, options = {}) {
  const doFetch = () => {
    const headers = Object.assign({ "Content-Type": "application/json" }, options.headers || {});
    const token = getAccess();
    if (token) headers["Authorization"] = "Bearer " + token;
    return fetch(path, Object.assign({}, options, { headers }));
  };

  let res = await doFetch();
  if (res.status === 401 && getRefresh()) {
    const refreshed = await refreshAccessToken();
    if (refreshed) res = await doFetch();
  }
  return res;
}

/* ------------------------------------------------------------------
 * View elements
 * ------------------------------------------------------------------ */
const authView = document.getElementById("authView");
const dashboardView = document.getElementById("dashboardView");

const loginForm = document.getElementById("loginForm");
const registerForm = document.getElementById("registerForm");
const loginError = document.getElementById("loginError");
const registerError = document.getElementById("registerError");

const userNameEl = document.getElementById("userName");
const logoutBtn = document.getElementById("logoutBtn");

const linkStatusUnknown = document.getElementById("linkStatusUnknown");
const linkStatusLinked = document.getElementById("linkStatusLinked");
const linkStatusTelegramAuto = document.getElementById("linkStatusTelegramAuto");
const linkStatusBrowser = document.getElementById("linkStatusBrowser");
const unlinkBtn = document.getElementById("unlinkBtn");
const connectBtn = document.getElementById("connectBtn");
const connectPanel = document.getElementById("connectPanel");
const deepLinkBtn = document.getElementById("deepLinkBtn");
const qrCanvas = document.getElementById("qrCanvas");
const manualForm = document.getElementById("manualForm");
const manualError = document.getElementById("manualError");

function showOnly(el) {
  [linkStatusUnknown, linkStatusLinked, linkStatusTelegramAuto, linkStatusBrowser].forEach((e) =>
    e.classList.add("hidden")
  );
  el.classList.remove("hidden");
}

/* ------------------------------------------------------------------
 * Auth tabs (login / register)
 * ------------------------------------------------------------------ */
document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    const isLogin = btn.dataset.tab === "login";
    loginForm.classList.toggle("hidden", !isLogin);
    registerForm.classList.toggle("hidden", isLogin);
  });
});

loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  loginError.textContent = "";
  const fd = new FormData(loginForm);
  const res = await fetch("/api/token/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: fd.get("username"), password: fd.get("password") }),
  });
  if (!res.ok) {
    loginError.textContent = "نام کاربری یا رمز عبور اشتباه است.";
    return;
  }
  const data = await res.json();
  setTokens(data.access, data.refresh);
  await enterDashboard();
});

registerForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  registerError.textContent = "";
  const fd = new FormData(registerForm);
  const payload = {
    username: fd.get("username"),
    email: fd.get("email"),
    password: fd.get("password"),
    password2: fd.get("password2"),
  };
  const res = await fetch("/api/register/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) {
    registerError.textContent = firstErrorMessage(data);
    return;
  }
  setTokens(data.access, data.refresh);
  await enterDashboard();
});

function firstErrorMessage(errData) {
  if (!errData || typeof errData !== "object") return "خطایی رخ داد.";
  for (const key of Object.keys(errData)) {
    const val = errData[key];
    if (Array.isArray(val) && val.length) return val[0];
    if (typeof val === "string") return val;
  }
  return "خطایی رخ داد.";
}

logoutBtn.addEventListener("click", () => {
  clearTokens();
  location.reload();
});

/* ------------------------------------------------------------------
 * Dashboard + linking
 * ------------------------------------------------------------------ */
async function enterDashboard() {
  authView.classList.add("hidden");
  dashboardView.classList.remove("hidden");
  showOnly(linkStatusUnknown);

  const meRes = await api("/api/me/");
  if (!meRes.ok) {
    // token invalid/expired beyond refresh -> back to login
    clearTokens();
    dashboardView.classList.add("hidden");
    authView.classList.remove("hidden");
    return;
  }
  const me = await meRes.json();
  userNameEl.textContent = me.username;

  const linked = !!(me.profile && me.profile.telegram_chat_id);
  if (linked) {
    showOnly(linkStatusLinked);
    return;
  }

  if (IS_TELEGRAM) {
    showOnly(linkStatusTelegramAuto);
    await autoLinkViaTelegram();
  } else {
    showOnly(linkStatusBrowser);
  }
}

async function autoLinkViaTelegram() {
  const res = await api("/api/telegram/webhook/webapp-link/", {
    method: "POST",
    body: JSON.stringify({ init_data: tg.initData }),
  });
  if (res.ok) {
    showOnly(linkStatusLinked);
    tg.HapticFeedback && tg.HapticFeedback.notificationOccurred("success");
  } else {
    // fall back to the manual/QR panel even inside Telegram, just in case
    showOnly(linkStatusBrowser);
  }
}

unlinkBtn.addEventListener("click", async () => {
  unlinkBtn.disabled = true;
  await api("/api/telegram/webhook/unlink/", { method: "POST" });
  unlinkBtn.disabled = false;
  if (IS_TELEGRAM) {
    showOnly(linkStatusTelegramAuto);
    await autoLinkViaTelegram();
  } else {
    showOnly(linkStatusBrowser);
  }
});

let pollTimer = null;

connectBtn.addEventListener("click", async () => {
  connectBtn.disabled = true;
  const res = await api("/api/telegram/webhook/generate-link/", { method: "POST" });
  connectBtn.disabled = false;
  if (!res.ok) return;
  const data = await res.json();

  connectPanel.classList.remove("hidden");
  deepLinkBtn.href = data.deep_link;

  if (window.QRCode) {
    QRCode.toCanvas(qrCanvas, data.deep_link, { width: 220, margin: 1 });
  }

  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(async () => {
    const statusRes = await api("/api/telegram/webhook/link-status/");
    if (!statusRes.ok) return;
    const statusData = await statusRes.json();
    if (statusData.linked) {
      clearInterval(pollTimer);
      pollTimer = null;
      showOnly(linkStatusLinked);
    }
  }, 2500);
});

manualForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  manualError.textContent = "";
  const code = new FormData(manualForm).get("code").trim();
  if (!code) return;
  const res = await api("/api/telegram/webhook/verify-link/", {
    method: "POST",
    body: JSON.stringify({ code }),
  });
  const data = await res.json();
  if (!res.ok) {
    manualError.textContent = data.detail || "کد نامعتبر است.";
    return;
  }
  if (pollTimer) clearInterval(pollTimer);
  showOnly(linkStatusLinked);
});

/* ------------------------------------------------------------------
 * Boot
 * ------------------------------------------------------------------ */
(async function boot() {
  if (getAccess()) {
    dashboardView.classList.remove("hidden");
    await enterDashboard();
  } else {
    authView.classList.remove("hidden");
  }
})();
