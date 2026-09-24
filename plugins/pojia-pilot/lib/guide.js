/**
 * pojia-pilot / lib/guide.js
 * v0.2 打靶过程自动引导。
 *
 * 三个触发点:
 *  1. 阶段推进: 令牌进度变化 → 注入"下一步建议"(弹药序+未完成项)
 *  2. 无动作: status 端点暴露 lastActivity, 大屏/面板可见
 *  3. 恢复开局: pendingResume 自动附引导
 */
import * as ammo from "./ammo.js";

const PROCESS_NOTE = "引导只是建议，与当前任务书冲突时以任务书为准；一次只接一个交付物。";

/** 下一步建议文案 */
export function nextStepHint(tokenSnap, ammoDesc) {
  if (!tokenSnap?.exists) return "";
  const lines = String(tokenSnap.text || tokenSnap.raw || "").split(/\n/);
  const pending = lines.filter((l) => l.includes("[ ]")).map((l) => l.replace(/^\s*-\s*/, "").trim());
  if (!pending.length) return "【引导】全部步骤完成 → /recover 存档并出收官报告。";
  const rec = ammoDesc ? ammo.recommend(ammoDesc, { top: 1 }) : null;
  const ammoLine = rec?.text?.split(/\n/)?.find((l) => l.trim()) || "";
  return [
    "【引导 · 下一步】",
    `未完成 ${pending.length} 项，建议先做: ${pending[0]}`,
    ammoLine ? `弹药参考: ${ammoLine}` : "",
    PROCESS_NOTE,
  ].filter(Boolean).join("\n");
}

/** 注入块追加引导(baseInjectText 末尾调用) */
export function guideSuffix(tokenSnap, ammoDesc) {
  const hint = nextStepHint(tokenSnap, ammoDesc);
  return hint ? "\n" + hint : "";
}
