/**
 * pojia-pilot / lib/persist.js
 * v0.3.2 磁盘状态机 (借鉴 Seep Lab Mode: ~/.pi/agent/lab-mode.flag)
 *
 * 痛点: 激活状态 (activeUntil) 是进程内存——宿主重启/新会话/上下文压缩后即丢,
 * 模型切换后注入块消失, 每次都要重打口令。
 *
 * 方案: 激活时把状态落到 $DSH_HOME/memory/pilot-mode.flag,
 * isActivated() 先查内存, 未命中再查磁盘标志文件。
 * 上下文压缩/会话重建后, 磁盘标志仍在 → 注入块自动恢复。
 *
 * 设计约束:
 *  - 标志文件带 ttl 与靶名, 过期自动失效(不无限常开, 安全默认);
 *  - injectAlways=true 时跳过此机制(本来就常开);
 *  - 标志文件损坏/不可读 → 视为未激活, 不阻断插件加载。
 */
import fs from "node:fs";
import path from "node:path";
import { findDshHome } from "./token.js";

const FLAG_RELPATH = path.join("memory", "pilot-mode.flag");

function flagPath(cfg) {
  const home = cfg?.dshHome || findDshHome();
  return path.join(home, FLAG_RELPATH);
}

/**
 * 把激活状态持久化到磁盘。
 * @param {{target:string, until:number, owned:boolean}} snap
 */
export function saveFlag(cfg, snap) {
  try {
    const file = flagPath(cfg);
    fs.mkdirSync(path.dirname(file), { recursive: true });
    const payload = {
      v: 1,
      target: String(snap.target || ""),
      until: Number(snap.until || 0),
      owned: Boolean(snap.owned),
      at: Date.now(),
    };
    fs.writeFileSync(file, JSON.stringify(payload), "utf8");
    return payload;
  } catch {
    return null; // 磁盘失败不阻断激活
  }
}

/**
 * 读磁盘标志。过期/损坏 → 清除并返回 null。
 * @returns {{target:string, until:number, owned:boolean, remainingMs:number}|null}
 */
export function loadFlag(cfg) {
  let raw = "";
  try {
    raw = fs.readFileSync(flagPath(cfg), "utf8");
  } catch {
    return null;
  }
  let obj = null;
  try {
    obj = JSON.parse(raw);
  } catch {
    clearFlag(cfg);
    return null;
  }
  const until = Number(obj?.until || 0);
  if (!until || until <= Date.now()) {
    clearFlag(cfg);
    return null;
  }
  return {
    target: String(obj.target || ""),
    until,
    owned: Boolean(obj.owned),
    remainingMs: until - Date.now(),
  };
}

/** 清除磁盘标志(过期/手动退出)。 */
export function clearFlag(cfg) {
  try {
    fs.unlinkSync(flagPath(cfg));
  } catch { /* 不存在即成功 */ }
}

export default { saveFlag, loadFlag, clearFlag };
