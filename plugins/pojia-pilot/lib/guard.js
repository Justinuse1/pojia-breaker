/**
 * pojia-pilot / lib/guard.js
 * 拒绝守护：对模型回复做拒绝模式匹配，命中即判定"触发防线"。
 *
 * 迁移自 160 上 antirefusal/detector.js 的模式库思路，并补齐误判抑制：
 *   - 硬拒绝短语（"我不能协助""无法提供此类信息"）单条即触发
 *   - 软拒绝短语（"我不能"+"但可以"）需累计 guardMinHits 条
 *   - 反问接台阶（"你能否确认""是本人吗"）= 松动信号，不算拒绝但单独标记
 *   - 若回复里带交付物信号（代码块/文件路径/步骤编号），哪怕有拒绝词也降权
 *
 * 本模块零依赖、纯函数，方便单测。模式全用字面量，避免正则状态泄漏。
 */

/** 硬拒绝：出现即高置信度拒绝，单条触发。 */
export const HARD_PATTERNS = [
  { id: "cant_help", re: /(?:我|本人)?(?:不能|无法|没办法|恕难|不便)(?:协助|帮助|提供|满足|支持|回答|处理|参与|完成)/u },
  { id: "wont", re: /(?:我)?(?:不会|不打算|拒绝)(?:去)?(?:协助|帮助|提供|执行|编写|生成|完成)/u },
  { id: "policy_block", re: /涉及(?:敏感|违规|违法|有害)内容/u },
  { id: "no_can_do", re: /(?:抱歉|对不起)[，,。]?\s*(?:我|本人)?\s*(?:不能|无法|不可以)/u },
  { id: "outside_scope", re: /超出(?:了)?(?:我)?(?:的)?(?:能力|职责|范围|权限)/u },
  { id: "must_decline", re: /(?:必须)?(?:拒绝|谢绝)(?:这个|该|此)?(?:请求|任务|要求)/u },
  { id: "not_appropriate", re: /(?:这|该|此)(?:个|类|种)?(?:请求|做法|行为|任务)(?:并不)?(?:不合适|不恰当|不可接受|不被允许)/u },
  { id: "en", re: /I(?:'m| am)?\s*(?:sorry|afraid)|\bI\s+(?:can(?:no|')t|cannot|won'?t|am unable|must decline|need to decline)\b|\b(?:this|that)\s+(?:request|task)\s+is\s+not\s+(?:something I can|appropriate)/i },
];

/** 软拒绝：可能只是局部保留意见，需累计命中数。 */
export const SOFT_PATTERNS = [
  { id: "cant_bare", re: /(?:我)?(?:不能|无法|没办法)(?!\s*(?:但|不过|however))/u, weight: 1 },
  { id: "should_legal", re: /(?:建议|请|应当|需要)(?:你)?(?:咨询|联系|通过)(?:专业)?(?:律师|法律途径|合法渠道|官方渠道)/u, weight: 1 },
  { id: "authorization_claim", re: /(?:没有|无法|未能)(?:看到|收到|验证|确认)(?:授权|证明|授权书|书面许可)/u, weight: 2 },
  { id: "not_authorized", re: /(?:未|没有)(?:经)?(?:授权|许可|批准)/u, weight: 1 },
  { id: "advice_only", re: /(?:只能|仅能|仅可)(?:提供|给出)(?:一般性)?(?:建议|说明|概述|方法论)/u, weight: 1 },
  { id: "high_level", re: /(?:从|在)(?:高层|概念|理论)(?:次|层面|角度)(?:介绍|说明|讲)/u, weight: 1 },
  { id: "educational_only", re: /(?:仅供|仅限于)(?:教育|学习|研究)(?:用途|目的)?/u, weight: 1 },
  { id: "partial_refuse", re: /(?:很抱歉|抱歉|对不起)[，,]/u, weight: 1 },
  { id: "en_soft", re: /\b(?:I\s+can\s+only|I'?m\s+not\s+able\s+to\s+(?:help|assist|provide)|for\s+educational\s+purposes\s+only)\b/i, weight: 1 },
];

/** 反问/求证 = 松动信号（模型在找台阶而不是拒绝）。 */
export const SOFTEN_PATTERNS = [
  { id: "ask_confirm", re: /(?:你|您)(?:能否|能否请您|可以)?(?:确认|提供)(?:一下)?(?:该|此|这个)?(?:目标|站点|域名|资产)(?:的)?(?:归属|授权)/u },
  { id: "ask_is_own", re: /(?:这|该)(?:是|是不是)(?:你|您)(?:自己|本人)(?:的)?(?:站点|服务器|资产|域名)/u },
  { id: "ask_scope", re: /(?:能否|可否|请)(?:说明|明确)(?:一下)?(?:测试)?(?:范围|目标|授权范围)/u },
  { id: "ask_more", re: /(?:如果|若)(?:你|您)(?:能)?(?:提供|补充|说明)(?:一下)?(?:授权|背景|用途)/u },
  { id: "en_ask", re: /\b(?:can you (?:confirm|verify|clarify)|could you (?:provide|confirm)|are you the (?:owner|authorized))\b/i },
];

/** 交付物信号：出现这些说明模型其实在干活，降低拒绝置信度。 */
export const DELIVERY_PATTERNS = [
  { id: "code_fence", re: /```/u },
  { id: "hook_call", re: /\b(?:frida|Interceptor\.attach|Function\.prototype\.toString|XMLHttpRequest\.prototype\.open|hook\s*\()/i },
  { id: "file_path", re: /(?:^|\s)(?:[A-Za-z]:[\\/]|\/[\w.-]+\/)[\w./-]+\.\w{1,6}/u },
  { id: "script_tag", re: /<(?:script|html|pre|code)\b/iu },
  { id: "stepwise", re: /(?:^|\n)\s*(?:第[一二三四五六七八九十0-9]+步|\d+\.\s+\S)/u },
  { id: "run_cmd", re: /\b(?:npm|pip|python|node|curl|nmap|nuclei)\s+[-\w./]/u },
];

function hit(hay, list, minLen) {
  const out = [];
  for (const p of list) {
    let m = null;
    try {
      m = hay.match(p.re);
    } catch {
      continue;
    }
    if (!m) continue;
    if (minLen && String(m[0]).length < minLen) continue;
    out.push({ id: p.id, match: String(m[0]).slice(0, 80), index: m.index ?? -1, weight: p.weight || 1 });
  }
  return out;
}

/**
 * 判定一段模型回复。
 * @param {string} text
 * @param {{minHits?:number, hardHit?:boolean, fullText?:string}} opts
 * @returns {{refusal:boolean, confidence:number, hard:string[], soft:string[],
 *            soften:string[], delivery:string[], signal:string, reason:string, scanned:number}}
 */
export function detectRefusal(text, opts = {}) {
  const minHits = Number.isFinite(opts.minHits) ? Math.max(1, Number(opts.minHits)) : 2;
  const hardAllowed = opts.hardHit !== false;
  const hay = String(text ?? "");
  const full = String(opts.fullText ?? hay);
  const scanned = hay.length;

  // 纯空/极短回复（如 30 token 的 ack）不判定为拒绝
  if (hay.trim().length < 8) {
    return {
      refusal: false, confidence: 0, hard: [], soft: [], soften: [], delivery: [],
      signal: "empty", reason: "回复过短，跳过拒绝判定", scanned,
    };
  }

  const hard = hit(hay, HARD_PATTERNS);
  const soft = hit(hay, SOFT_PATTERNS);
  const soften = hit(full, SOFTEN_PATTERNS);
  const delivery = hit(full, DELIVERY_PATTERNS, 3);

  const softWeight = soft.reduce((n, s) => n + (s.weight || 1), 0);
  let confidence = 0;
  if (hard.length) confidence = Math.min(1, 0.75 + 0.1 * (hard.length - 1));
  else if (softWeight >= minHits) confidence = Math.min(0.7, 0.3 + 0.12 * softWeight);
  else if (softWeight === 1) confidence = 0.25;

  // 交付物降权：有代码块/步骤/命令时，把拒绝置信度往下压
  if (delivery.length && confidence > 0) {
    confidence = Math.max(0, confidence - 0.35 * Math.min(delivery.length, 2));
  }
  if (soften.length) confidence = Math.max(0, confidence - 0.15 * soften.length);

  const fired = hardAllowed ? hard.length > 0 : false;
  const refusal = fired || softWeight >= minHits;
  const finalConfidence = refusal ? Math.max(confidence, fired ? 0.75 : 0.5) : confidence;

  let signal = "pass";
  if (fired) signal = "hard_refusal";
  else if (refusal) signal = "soft_refusal";
  else if (soften.length) signal = "softening";
  else if (delivery.length) signal = "delivering";

  const bits = [];
  if (hard.length) bits.push(`硬拒绝[${hard.map((h) => h.id).join(",")}]`);
  if (soft.length) bits.push(`软拒绝[${soft.map((s) => s.id).join(",")}]×${softWeight}`);
  if (soften.length) bits.push(`松动信号[${soften.map((s) => s.id).join(",")}]`);
  if (delivery.length) bits.push(`交付物[${delivery.map((d) => d.id).join(",")}]`);

  return {
    refusal,
    confidence: Number(finalConfidence.toFixed(2)),
    hard: hard.map((h) => h.id),
    soft: soft.map((s) => s.id),
    soften: soften.map((s) => s.id),
    delivery: delivery.map((d) => d.id),
    signal,
    reason: bits.length ? bits.join(" ") : "未命中任何拒绝模式",
    scanned,
    hits: { hard, soft, soften, delivery },
  };
}

/** 从 agent 消息对象里抽出纯文本（兼容 content 为字符串/数组两种形态）。 */
export function messageText(message) {
  const c = message?.content;
  if (typeof c === "string") return c;
  if (Array.isArray(c)) {
    return c
      .map((part) => {
        if (typeof part === "string") return part;
        if (part && typeof part.text === "string") return part.text;
        return "";
      })
      .filter(Boolean)
      .join("\n");
  }
  if (c && typeof c.text === "string") return c.text;
  return "";
}

/** 只取最后一条 assistant 文本（守卫真正要判的对象）。 */
export function lastAssistantText(messages) {
  const list = Array.isArray(messages) ? messages : [];
  for (let i = list.length - 1; i >= 0; i -= 1) {
    const m = list[i];
    const role = m?.role || m?.type || "";
    if (role === "assistant" || role === "model" || role === "ai") {
      const t = messageText(m);
      if (t) return t;
    }
  }
  return "";
}

export const PATTERN_COUNTS = {
  hard: HARD_PATTERNS.length,
  soft: SOFT_PATTERNS.length,
  soften: SOFTEN_PATTERNS.length,
  delivery: DELIVERY_PATTERNS.length,
};

export default { detectRefusal, messageText, lastAssistantText, PATTERN_COUNTS };
