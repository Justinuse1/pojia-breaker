/**
 * pojia-pilot / lib/compat.js
 * v0.3.2 版本速配层 (借鉴 dsh-purge skipIfMarked + 自动还原重应用机制)
 *
 * 痛点: 官方 DSH 升级(0.1.6→0.1.7-rc.x→正式版)后, 依赖 API 形态的插件逻辑
 * 可能静默失配——路由注册改名、systemPrompt 段位变化、hook 事件消失。
 * purge 的死穴正是「官方升级即废」; 我们要在升级后第一小时内自愈。
 *
 * 机制:
 *  1. 启动时探测宿主 runtime 版本 + 关键 API 面(systemPrompt.section /
 *     tools.register / webServer.register / ctx.on),
 *     每个探测点标记 ok/degraded/missing;
 *  2. 把探测结果写入 $DSH_HOME/memory/pilot-compat.json (带 runtime 版本戳);
 *  3. 版本变化 → 全部探测点重跑(自动重应用); 版本没变 → 读缓存, 零开销;
 *  4. degraded/missing 的能力自动降级: 缺 systemPrompt→只走工具描述通道,
 *     缺 webServer→路由进 routeErrors, 状态里可见;
 *  5. /pojiaai/status 暴露 compat 结果, 一眼看穿哪条链路因升级失配。
 *
 * 设计约束: 探测全部只读、无副作用、失败不阻断加载。
 */
import fs from "node:fs";
import path from "node:path";
import { findDshHome } from "./token.js";

const COMPAT_RELPATH = path.join("memory", "pilot-compat.json");

/** 关键 API 面。缺失任何一个都能被 status 点名。 */
const PROBES = [
  { id: "systemPrompt.section", critical: true,  test: (ctx) => typeof ctx?.systemPrompt?.section === "function" },
  { id: "tools.register",       critical: true,  test: (ctx) => typeof ctx?.tools?.register === "function" },
  { id: "webServer.register",   critical: false, test: (ctx) => typeof ctx?.webServer?.register === "function" },
  { id: "ctx.on(hooks)",        critical: false, test: (ctx) => typeof ctx?.on === "function" },
  { id: "commands.register",    critical: false, test: (ctx) => Boolean(ctx?.commands) && typeof ctx?.commands?.register === "function" },
];

function compatPath(cfg) {
  return path.join(cfg?.dshHome || findDshHome(), COMPAT_RELPATH);
}

/** 读宿主 runtime 版本(读不到返回空串, 不阻断)。 */
export function hostVersion(dshHome) {
  const candidates = [
    path.join(dshHome || findDshHome(), "package.json"),
  ];
  try {
    // 宿主 node_modules 里的 dsh runtime 版本最准
    const here = path.resolve(path.dirname(fileUrl()));
    const nm = path.join(here, "..", "..", "..", "node_modules", "@deepseek-ai", "dsh", "package.json");
    candidates.unshift(nm);
  } catch { /* fileUrl 失败就只看 DSH_HOME */ }
  for (const f of candidates) {
    try {
      const pkg = JSON.parse(fs.readFileSync(f, "utf8"));
      if (pkg?.version) return String(pkg.version);
    } catch { /* 下一个 */ }
  }
  return "";
}

function fileUrl() {
  // compat.js 自己的位置 → 推宿主 node_modules 根 (lib/compat.js 上三级)
  return import.meta.url;
}

/**
 * 跑全套探测。版本未变且缓存健康 → 直接用缓存(自动重应用语义: 版本变了才重跑)。
 * @returns {{hostVersion, probes:{id,ok,critical}[], degraded:string[], missing:string[], cached:boolean}}
 */
export function probe(ctx, cfg, { force = false } = {}) {
  const hv = hostVersion(cfg?.dshHome);
  const file = compatPath(cfg);
  if (!force) {
    try {
      const prev = JSON.parse(fs.readFileSync(file, "utf8"));
      if (prev?.hostVersion === hv && Array.isArray(prev?.probes)) {
        return { ...prev, cached: true };
      }
    } catch { /* 无缓存/损坏 → 重跑 */ }
  }

  const probes = PROBES.map((p) => {
    let ok = false;
    try { ok = Boolean(p.test(ctx)); } catch { ok = false; }
    return { id: p.id, ok, critical: p.critical };
  });
  const missing = probes.filter((p) => !p.ok && p.critical).map((p) => p.id);
  const degraded = probes.filter((p) => !p.ok && !p.critical).map((p) => p.id);
  const result = {
    hostVersion: hv,
    probes,
    missing,
    degraded,
    criticalOk: missing.length === 0,
    probedAt: Date.now(),
    cached: false,
  };
  try {
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, JSON.stringify(result), "utf8");
  } catch { /* 写不了就只在内存里用 */ }
  return result;
}

/** 生成人类可读的速配简报(status/工具描述用)。 */
export function brief(compat) {
  if (!compat) return "版本速配: 未探测";
  const lines = [`版本速配: runtime ${compat.hostVersion || "?"} ${compat.cached ? "(缓存)" : "(新探测)"}`];
  for (const p of compat.probes) {
    lines.push(`- ${p.ok ? "✓" : p.critical ? "✗ MISSING" : "△ degraded"} ${p.id}`);
  }
  if (compat.missing.length) lines.push(`注意: 关键能力缺失 ${compat.missing.join(",")} → 注入降级到工具描述通道`);
  return lines.join("\n");
}

export default { probe, hostVersion, brief };
