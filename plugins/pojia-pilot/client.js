// pojia-pilot client.js — Web UI 面板 (v0.1)
// 挂载: slot面板 + 拒绝红条 + 弹药推荐卡片
// 模式参考: dsh-purge client.js 的 fetch+slot 结构

export const name = "pojia-pilot-client";

const API = "/pojiaai";
const $ = (sel) => document.querySelector(sel);

async function api(path, opts) {
  const r = await fetch(API + path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!r.ok) throw new Error(`${path}: ${r.status}`);
  return r.json();
}

function card(title, bodyHtml) {
  const el = document.createElement("div");
  el.className = "pojia-card";
  el.style.cssText =
    "border:1px solid #2a6;border-radius:8px;padding:12px;margin:8px 0;background:#0d1a12;color:#cfc;";
  el.innerHTML = `<b style="color:#4c8">🎯 ${title}</b><br/>` + bodyHtml;
  return el;
}

// ── 状态面板 ─────────────────────────────────────────────
async function renderStatus(container) {
  try {
    const s = await api("/status");
    const html =
      `当前靶: <b>${s.target || "未设定"}</b> · 守护: ${s.guard ? "🟢开" : "⚪关"} · ` +
      `激活: ${s.activated ? "✅" : "未激活"}<br/>` +
      `<small>口令: 输入 <code>${s.passphrase || "pojiaai"}</code> 一键开局</small>`;
    container.appendChild(card("pilot 状态", html));
  } catch (e) {
    container.appendChild(card("pilot 状态", `离线: ${e.message}`));
  }
}

// ── 弹药推荐 ─────────────────────────────────────────────
async function renderAmmo(container, desc) {
  try {
    const r = await api("/ammo", {
      method: "POST",
      body: JSON.stringify({ desc }),
    });
    const items = (r.recommendations || [])
      .map(
        (a, i) =>
          `${i + 1}. <b>${a.id}</b> (${a.level}, ASR ${a.asr}) — ${a.desc}`
      )
      .join("<br/>");
    container.appendChild(card("弹药推荐 Top3", items || "无匹配"));
  } catch (e) {
    container.appendChild(card("弹药推荐", `失败: ${e.message}`));
  }
}

// ── 拒绝红条 ─────────────────────────────────────────────
function showRejectBar(reason) {
  const bar = document.createElement("div");
  bar.style.cssText =
    "position:fixed;top:0;left:0;right:0;z-index:99999;" +
    "background:#7a1f1f;color:#fff;padding:10px 16px;font-size:14px;" +
    "display:flex;gap:12px;align-items:center;";
  bar.innerHTML =
    `🛡️ <b>检测到拒绝防线</b> <small>(${reason})</small>` +
    `<button id="pojia-recover" style="margin-left:auto;cursor:pointer;">` +
    `存档·新会话·恢复</button>` +
    `<button id="pojia-dismiss" style="cursor:pointer;">忽略</button>`;
  document.body.appendChild(bar);
  $("#pojia-recover").onclick = async () => {
    try {
      const r = await api("/recover", { method: "POST", body: "{}" });
      bar.innerHTML = `✅ 进度已存档 (${r.archived || "ok"}) — 请新开会话, 令牌将自动恢复`;
      setTimeout(() => bar.remove(), 5000);
    } catch (e) {
      bar.innerHTML = `恢复失败: ${e.message}`;
    }
  };
  $("#pojia-dismiss").onclick = () => bar.remove();
}

// ── 挂载入口 ─────────────────────────────────────────────
export function mount(ctx) {
  const host = ctx.get?.("webServer") || {};
  // 轮询守护状态(由Host端guard检测结果同步)
  let lastReject = null;
  setInterval(async () => {
    try {
      const s = await api("/guard");
      if (s.rejected && s.rejectId !== lastReject) {
        lastReject = s.rejectId;
        showRejectBar(s.reason || "模式匹配");
      }
    } catch {}
  }, 4000);

  // 面板挂到侧栏slot(有则挂, 无则浮窗)
  const anchor =
    $("#dsh-sidebar") || document.querySelector("aside") || document.body;
  const panel = document.createElement("div");
  panel.id = "pojia-panel";
  anchor.appendChild(panel);
  renderStatus(panel);

  // 弹药推荐输入
  const input = document.createElement("input");
  input.placeholder = "描述目标 → 弹药推荐 (回车)";
  input.style.cssText =
    "width:100%;padding:6px;margin:4px 0;border-radius:6px;border:1px solid #2a6;background:#0a140e;color:#cfc;";
  input.onkeydown = (e) => {
    if (e.key === "Enter" && input.value.trim()) {
      renderAmmo(panel, input.value.trim());
      input.value = "";
    }
  };
  panel.appendChild(input);
  console.log("[pojia-pilot] client mounted");
}
