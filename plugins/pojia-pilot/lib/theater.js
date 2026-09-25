/**
 * pojia-pilot / lib/theater.js
 * v0.4 战区持久化（Theater Persistence）—— 对齐 160 findings/evidence 结构。
 *
 * 160 实战教训: 战果散在会话里=没有战果。每个靶一个 evidence 目录,
 * 结构固定(对应五层), 换会话/换人接手都能直接续打:
 *
 *   <dshHome>/theater/<靶名>/
 *     TARGET.md          ← 靶书指针+授权状态+当前阶段
 *     TIMELINE.txt       ← append-only 事件线(每步一行, 跨会话累计)
 *     findings/          ← 阶段战果(按 sop 五阶段命名)
 *       L1_recon/ L4_exploit/ L5_loot/ ...
 *     handover.md        ← 移交摘要(会话结束/被否定时自动写, 引擎fork的种子)
 *
 * 与引擎(engine.js)的关系: handover.md 就是下次 fork 的任务书底稿。
 */
import fs from "node:fs";
import path from "node:path";
import { findDshHome } from "./token.js";

const PHASE_DIRS = ["L1_recon", "L2_surface", "L3_access", "L4_exploit", "L5_loot"];

function theaterRoot(cfg) {
  const home = cfg?.dshHome || findDshHome();
  return path.join(home, "theater");
}

export function theaterDir(cfg, target) {
  const safe = String(target || "unknown").split(/[/\\]/).join("_").replace(/[^a-zA-Z0-9._-]/g, "_").replace(/\.{2,}/g, "_").slice(0, 64) || "unknown";
  return path.join(theaterRoot(cfg), safe);
}

/** 确保战区目录结构存在(幂等) */
export function ensureTheater(cfg, target, meta = {}) {
  const dir = theaterDir(cfg, target);
  for (const d of [dir, ...PHASE_DIRS.map((p) => path.join(dir, "findings", p))]) {
    fs.mkdirSync(d, { recursive: true });
  }
  const targetMd = path.join(dir, "TARGET.md");
  if (!fs.existsSync(targetMd)) {
    fs.writeFileSync(
      targetMd,
      [
        `# 战区 · ${target}`,
        "",
        `- 建区: ${new Date().toISOString()}`,
        `- 授权: ${meta.owned ? "操作员确认自有/书面授权" : "按靶书(memory/targets/)为准"}`,
        "- 阶段: L1_recon → L2_surface → L3_access → L4_exploit → L5_loot",
        "",
        "> 本目录为跨会话战区。所有战果落 findings/ 对应阶段目录; 事件线记 TIMELINE.txt; 移交摘要写 handover.md。",
      ].join("\n"),
      "utf8"
    );
  }
  return dir;
}

/** TIMELINE 追加一行(append-only, 带UTC时间戳) */
export function logEvent(cfg, target, event) {
  try {
    const dir = ensureTheater(cfg, target);
    const line = `${new Date().toISOString()} ${String(event).replace(/\s+/g, " ").slice(0, 300)}\n`;
    fs.appendFileSync(path.join(dir, "TIMELINE.txt"), line, "utf8");
    return true;
  } catch {
    return false;
  }
}

/** 战果落盘: 写入对应阶段目录, 返回落盘路径 */
export function saveFinding(cfg, target, phase, filename, content) {
  const dir = ensureTheater(cfg, target);
  const ph = PHASE_DIRS.includes(phase) ? phase : "L1_recon";
  const file = path.join(dir, "findings", ph, String(filename || `note-${Date.now()}.md`).replace(/[^a-zA-Z0-9._-]/g, "_"));
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, String(content ?? ""), "utf8");
  logEvent(cfg, target, `finding → ${path.relative(dir, file)} (${Buffer.byteLength(String(content || ""))}B)`);
  return file;
}

/** 移交摘要(引擎fork的任务书底稿) */
export function writeHandover(cfg, target, sections) {
  const dir = ensureTheater(cfg, target);
  const body = [
    `# 移交摘要 · ${target}`,
    `- 生成: ${new Date().toISOString()}`,
    "",
    "## 已验证战术链",
    sections.chain || "(待补)",
    "",
    "## 关键战果/凭据位置",
    sections.loot || "(见 findings/L5_loot/)",
    "",
    "## 转向点与教训",
    sections.lessons || "(见 TIMELINE.txt)",
    "",
    "## 下一步建议",
    sections.next || "(待补)",
    "",
    "> 本文件是战果引擎(engine) fork 新会话时的任务书底稿: 新会话继承父上下文后, 以本文件对齐战区现状继续推进。",
  ].join("\n");
  const file = path.join(dir, "handover.md");
  fs.writeFileSync(file, body, "utf8");
  logEvent(cfg, target, "handover.md updated");
  return file;
}

/** 读战区概览(状态/事件尾部) */
export function theaterStatus(cfg, target, tailLines = 10) {
  const dir = theaterDir(cfg, target);
  if (!fs.existsSync(dir)) return null;
  let timeline = "";
  try {
    const raw = fs.readFileSync(path.join(dir, "TIMELINE.txt"), "utf8").trimEnd();
    timeline = raw.split("\n").slice(-tailLines).join("\n");
  } catch { /* 无事件线 */ }
  const findings = {};
  for (const p of PHASE_DIRS) {
    try {
      findings[p] = fs.readdirSync(path.join(dir, "findings", p)).filter((f) => !f.startsWith("."));
    } catch {
      findings[p] = [];
    }
  }
  return { dir, timeline, findings };
}

/** 列出全部战区 */
export function listTheaters(cfg) {
  try {
    return fs.readdirSync(theaterRoot(cfg)).filter((f) => !f.startsWith("."));
  } catch {
    return [];
  }
}

export default { ensureTheater, logEvent, saveFinding, writeHandover, theaterStatus, listTheaters };
