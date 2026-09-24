/**
 * pojia-pilot / lib/thinking.js
 * v0.2 思考挡位控制: 按令牌阶段动态生成注入指令。
 *
 * 实态约束: DSH 平台挡位由宿主 UI 控制(off/low/medium, 禁 max)。
 * 插件做提示级控制——阶段1(侦查/排序)要求极简 ack 压输出,
 * 阶段2+(利用/验证)放行深思考。护栏句避免模型铺长铺垫。
 */

const STAGE_THINKING = [
  { match: /侦查|recon|信息收集|测绘/i,            mode: "minimal", note: "侦查期：每轮只交一行结论+证据路径，不展开推理过程。" },
  { match: /排序|rank|评级|攻击面/i,               mode: "minimal", note: "排序期：表格化评级，每项一行理由，禁止长论证。" },
  { match: /利用|exploit|打点|突破|渗透/i,          mode: "deep",    note: "利用期：开深思考，先一句话说打点再动手。" },
  { match: /验证|verify|核验|证伪/i,               mode: "deep",    note: "验证期：开深思考，正反双向判定，REFUTED 也入账。" },
  { match: /清理|cleanup|扫尾/i,                  mode: "minimal", note: "扫尾期：极简执行清单，逐项打勾。" },
];

/** 从令牌文本推断当前阶段 → 挡位指令 */
export function stageThinking(tokenText) {
  const t = String(tokenText || "");
  // 找第一个未完成项(未打勾的 [ ] 行)
  const pending = t.split(/\n/).find((l) => l.includes("[ ]"));
  if (!pending) return { mode: "deep", note: "全部步骤完成：收官模式，只做汇总与报告。", stage: "done" };
  for (const s of STAGE_THINKING) {
    if (s.match.test(pending)) {
      return { mode: s.mode, note: s.note, stage: pending.trim().replace(/^-\s*\[\s*\]\s*/, "") };
    }
  }
  return { mode: "deep", note: "默认放行深思考。", stage: pending.trim() };
}

/** 生成注入段文本(空字符串=不注入, 不占上下文) */
export function injectText(tokenText) {
  const s = stageThinking(tokenText);
  if (s.mode === "minimal") {
    return [
      "【思考挡位 · 极简】",
      s.note,
      "本阶段输出纪律: 单行 ack → 直接工具调用 → 单行结论。禁止铺陈、禁止复述任务、禁止提前总结。",
    ].join("\n");
  }
  return [
    "【思考挡位 · 深思】",
    s.note,
    "深思考放行，但开头仍须一句话点明当前动作再展开。",
  ].join("\n");
}
