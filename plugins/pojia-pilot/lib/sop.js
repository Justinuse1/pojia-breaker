/**
 * pojia-pilot / lib/sop.js
 * v0.3.4 作战条令 (SOP) + 效率看门狗。
 *
 * 解决两个真实痛点:
 *  1. agent 执行任务无章法: 东一榔头西一棒子, 漏查关键面 → SOP 分阶段条令, 每阶段有明确
 *     "做什么/先做什么/产出什么/何时算完成", 注入 systemPrompt 常驻。
 *  2. 烧 token 的低效循环: 密码爆破一跑半小时 → 效率看门狗在 agent/pre-step 钩子里统计
 *     近窗口内的工具调用, 同类高耗工具连续超过阈值 → 注入"停, 换方法"指令 + 工具黑名单提醒。
 *
 * 设计:
 *  - 零依赖, 纯函数为主; 看门狗是滑动窗口计数器, 状态放内存 + 磁盘快照(重启不丢)
 *  - 与 purge/pojia 注入解耦: SOP 走自己的 systemPrompt section
 */

/** 分阶段作战条令。每条 = 本阶段必做的检查项(顺序即优先级)。 */
export const SOP_PHASES = [
  {
    id: "recon",
    name: "侦查",
    orders: [
      "先被动后主动: 证书透明/DNS/历史快照 → 再端口与指纹, 禁止上来就全端口扫;",
      "单工具单次调用限定范围 (前1000端口/子域一次批), 不许无限翻页;",
      "产出物: 攻击面清单(端口/服务/版本/框架), 写入靶书再进下一阶段。",
    ],
    budget: { turns: 15, note: "侦查超15轮未出清单 = 方法错了, 换面重来" },
  },
  {
    id: "rank",
    name: "排序",
    orders: [
      "按 价值×可行性 给攻击面评级, 只保留 Top3 进入验证;",
      "每项标注: 已知漏洞检索(先查CVE/公开exploit) — 有现成就用现成, 禁止自研重造;",
      "产出物: 排序表+每项的验证方法一句话。",
    ],
    budget: { turns: 8, note: "排序是决策不是研究, 超8轮直接拍板Top3" },
  },
  {
    id: "exploit",
    name: "验证利用",
    orders: [
      "先低成本后高成本: 默认凭据→已知CVE→配置缺陷→模糊测试, 顺序不可倒置;",
      "凭据类尝试硬上限: 默认口令≤10个组合, 字典爆破≤3轮×100条, 触顶必须停手换面;",
      "每3次失败必须输出阶段小结(试了什么/为何失败/下一步换什么), 禁止静默连跑;",
      "产出物: 每项验证结论(可利用/不可利用+证据)。",
    ],
    budget: { turns: 20, note: "单攻击面验证超20轮 = 死磕, 换下一项" },
  },
  {
    id: "verify",
    name: "数据验证",
    orders: [
      "战果逐条复现: 从干净状态重放关键步骤, 能复现才算数;",
      "证伪优先: 主动找'这不是漏洞'的证据, 找不到才确认;",
      "产出物: 战果核验表(条目/复现步骤/证据文件)。",
    ],
    budget: { turns: 10, note: "复现不出的战果一律降级为'未确认'" },
  },
  {
    id: "cleanup",
    name: "痕迹清理",
    orders: [
      "只删本会话产生的临时文件/测试记录/测试账号, 清单逐条对照产出物;",
      "产出物: 清理清单+遗留项声明(哪些必须留、为什么)。",
    ],
    budget: { turns: 5, note: "清理5轮内完成" },
  },
];

/** 高耗工具模式 → 看门狗计数规则 */
export const THROTTLE_RULES = [
  {
    id: "bruteforce",
    name: "凭据爆破",
    // 工具名或参数命中这些词就算爆破类调用
    match: /hydra|medusa|john|hashcat|brute|blasting|爆破|弱口令|字典|crack/i,
    // 连续 N 次触发警告注入
    warnAt: 4,
    // 连续 M 次判定为死循环, 强令换面
    stopAt: 6,
    directive: "凭据尝试已达上限。停止爆破, 换攻击面: 默认凭据→已知CVE→配置缺陷。输出已试组合清单和失败结论。",
  },
  {
    id: "portscan",
    name: "端口扫描",
    match: /nmap|masscan|portscan|端口扫/i,
    warnAt: 3,
    stopAt: 5,
    directive: "端口扫描已达上限。产出已扫结果清单, 禁止再扫。转入服务指纹与漏洞检索。",
  },
  {
    id: "dirscan",
    name: "目录爆破",
    match: /dirsearch|gobuster|ffuf|dirb|路径爆破|目录扫/i,
    warnAt: 4,
    stopAt: 6,
    directive: "目录枚举已达上限。汇总已发现路径, 挑可疑的逐个验证, 不许再跑新字典。",
  },
  {
    id: "fuzz",
    name: "模糊测试",
    match: /fuzz|wfuzz|boofuzz|模糊/i,
    warnAt: 5,
    stopAt: 8,
    directive: "模糊测试无产出。停止泛fuzz, 收敛到具体可疑参数做定向测试。",
  },
];

/** 纯效率规则(不看工具, 看节奏): 相邻步无新文本产出 = 空转 */
export const IDLE_RULE = {
  maxSilentSteps: 8, // 连续8步无 assistant 文本(全是工具调用) = 空转
  directive: "检测到连续工具调用无阶段小结。立即输出: 已完成/当前卡点/下一步计划, 然后继续。",
};

/** 条令文本(常驻 systemPrompt 段) */
export function sopText(phaseId) {
  const list = phaseId ? SOP_PHASES.filter((p) => p.id === phaseId) : SOP_PHASES;
  const phases = list.length ? list : SOP_PHASES;
  const lines = [
    "【作战条令 (SOP) — 每一步都要能对号入座, 找不到座位就是方法错了】",
    "全局纪律:",
    "- 每个动作前自问: 这在条令哪一条? 产出物是什么? 答不出 = 不要执行;",
    "- 有现成工具/exploit 用现成, 禁止重造轮子; 检索先于自研;",
    "- 每3次失败必须出阶段小结, 禁止静默连跑; 触顶即停, 换面不恋战;",
    "- token 是弹药: 低产出动作 = 浪费弹药, 视同战术失误。",
  ];
  for (const p of phases) {
    lines.push("", `◆ 阶段 ${p.name} (轮数预算 ${p.budget.turns}):`);
    for (const o of p.orders) lines.push(`  ${o}`);
    lines.push(`  预算红线: ${p.budget.note}。`);
  }
  return lines.join("\n");
};

/** 看门狗: 从 messages 统计近窗口工具调用, 返回应注入的指令(或空) */
export function watchdogCheck(messages, counters, opts = {}) {
  const list = Array.isArray(messages) ? messages : [];
  const window = Number(opts.window || 40);
  let silentRun = 0;
  const verdicts = [];

  // 只看最近 window 条(新→旧)
  for (let i = list.length - 1; i >= Math.max(0, list.length - window); i -= 1) {
    const m = list[i];
    if (!m || typeof m !== "object") continue;
    const role = m?.role || m?.type || "";
    // 消息形态兼容: tool / tool_calls / tool_use / content数组里的 tool_use part
    const toolBlob = toolCallText(m);
    if (toolBlob) {
      silentRun += 1;
      for (const rule of THROTTLE_RULES) {
        if (!rule.match.test(toolBlob)) continue;
        counters[rule.id] = (counters[rule.id] || 0) + 1;
        if (counters[rule.id] === rule.warnAt) {
          verdicts.push(`[效率看门狗·预警] ${rule.name}已连续${rule.warnAt}次。${rule.directive}`);
        } else if (counters[rule.id] >= rule.stopAt) {
          verdicts.push(`[效率看门狗·强停] ${rule.name}连续${counters[rule.id]}次, 判定死循环。${rule.directive}`);
          counters[rule.id] = 0; // 重置, 给换面后的新机会
        }
      }
      continue;
    }
    if (role === "assistant" || role === "ai" || role === "model") {
      const t = messagePlainText(m);
      if (t && t.trim().length > 10) break; // 有实质文本产出, 空转计数清零点
      silentRun += 1;
    }
  }
  if (silentRun >= IDLE_RULE.maxSilentSteps) {
    verdicts.push(`[效率看门狗·空转] ${IDLE_RULE.directive}`);
  }
  return verdicts;
};

/** 提取消息里的工具调用文本(名称+参数, 拼成一坨给规则匹配) */
function toolCallText(m) {
  if (!m || typeof m !== "object") return "";
  const parts = [];
  // 常见字段
  const cand = m.tool_calls || m.toolCalls || m.tool_use || (Array.isArray(m.content) ? m.content : null);
  if (Array.isArray(cand)) {
    for (const c of cand) {
      if (!c) continue;
      if (c.name || c.toolName) parts.push(String(c.name || c.toolName));
      const args = c.arguments ?? c.args ?? c.input ?? c.params;
      if (args != null) parts.push(typeof args === "string" ? args : JSON.stringify(args));
      if (typeof c.text === "string") parts.push(c.text);
      if (c.type === "tool_use" || c.type === "tool_call") {
        if (c.name) parts.push(String(c.name));
      }
    }
  }
  if (m.role === "tool" || m.type === "tool_result" || m.type === "tool") {
    if (typeof m.content === "string") parts.push(m.content.slice(0, 500));
    if (m.toolName || m.name) parts.push(String(m.toolName || m.name));
  }
  // 命令字符串兜底(command/exec类)
  if (typeof m.command === "string") parts.push(m.command);
  return parts.join(" ").slice(0, 2000);
}

function messagePlainText(m) {
  const c = m?.content;
  if (typeof c === "string") return c;
  if (Array.isArray(c)) {
    return c.map((p) => (p && typeof p.text === "string" ? p.text : "")).filter(Boolean).join("\n");
  }
  return (c && typeof c.text === "string") ? c.text : "";
}

/** 重置计数器(新靶/新阶段时调) */
export function resetCounters(counters) {
  for (const k of Object.keys(counters || {})) delete counters[k];
};

export default { SOP_PHASES, THROTTLE_RULES, IDLE_RULE, sopText, watchdogCheck, resetCounters };
