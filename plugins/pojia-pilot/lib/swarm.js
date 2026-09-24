/**
 * pojia-pilot / lib/swarm.js
 * v0.2 多子代理编排骨牌。
 *
 * 设计原则:
 *  - 零新依赖: 子代理间用 targets/<target>.swarm/<role>.md 分片文件做 IPC
 *  - 认领锁: fsp.open(path, "wx") 原子创建 .claim 文件, 防多 worker 重复认领
 *  - 主会话=指挥官: 分派计划/汇总结果; 子代理=worker: 认领→执行→写回
 *  - worker 卡死检测: claim 超时(swarmClaimTtlMs)自动释放
 */
import fsp from "node:fs";
import path from "node:path";
import * as token from "./token.js";

export const ROLES = [
  { role: "recon",   step: "侦查",     desc: "端口/服务/攻击面清单", thinking: "minimal" },
  { role: "rank",    step: "攻击面排序", desc: "可行性评级+技能匹配", thinking: "minimal" },
  { role: "exploit", step: "验证利用",   desc: "按排序执行利用验证", thinking: "deep" },
  { role: "verify",  step: "数据验证",   desc: "战果真实性核验+证伪", thinking: "deep" },
  { role: "cleanup", step: "痕迹清理",   desc: "扫尾+痕迹清理",     thinking: "minimal" },
];

export function swarmDirOf(cfg, target) {
  return path.join(token.resolveTargetsDir(cfg), `${token.sanitizeTarget(target)}.swarm`);
}

const ROLE_FILE = (dir, role) => path.join(dir, `${role}.md`);
const CLAIM_FILE = (dir, role) => path.join(dir, `${role}.claim`);

async function ensureDir(dir) {
  await fsp.promises.mkdir(dir, { recursive: true });
}

/** 生成分派计划: 未完成步骤 → worker 任务书 */
export async function plan(cfg, target) {
  const snap = await token.readToken(cfg, target);
  const dir = swarmDirOf(cfg, target);
  const units = [];
  for (const r of ROLES) {
    units.push({
      role: r.role,
      step: r.step,
      desc: r.desc,
      thinking: r.thinking,
      done: Boolean(snap.exists && snap.done >= ROLES.indexOf(r)),
      claimable: true,
    });
  }
  return { target, dir, units };
}

/** worker 认领(原子): 成功返回任务书, 已被认领/已完成返回 null */
export async function claim(cfg, target, role, workerId) {
  const dir = swarmDirOf(cfg, target);
  const spec = ROLES.find((r) => r.role === role);
  if (!spec) return { ok: false, reason: "unknown role" };
  await ensureDir(dir);
  try {
    const fh = await fsp.promises.open(CLAIM_FILE(dir, role), "wx");
    await fh.writeFile(JSON.stringify({ workerId, at: Date.now() }, null, 2), "utf8");
    await fh.close();
  } catch (e) {
    // 已被认领 → 检查 TTL, 过期则抢占
    try {
      const raw = JSON.parse(await fsp.promises.readFile(CLAIM_FILE(dir, role), "utf8"));
      const ttl = Number(cfg.swarmClaimTtlMs) || 15 * 60 * 1000;
      if (Date.now() - raw.at < ttl) return { ok: false, reason: `claimed by ${raw.workerId} (${Math.round((Date.now() - raw.at) / 1000)}s ago)` };
      await fsp.promises.writeFile(CLAIM_FILE(dir, role), JSON.stringify({ workerId, at: Date.now(), preempted: raw.workerId }, null, 2), "utf8");
    } catch {
      return { ok: false, reason: "claim read failed" };
    }
  }
  const brief = [
    "【破甲蜂群 · 任务书】",
    `靶: ${target}`,
    `角色: ${spec.role}（${spec.step}）`,
    `任务: ${spec.desc}`,
    `思考挡位: ${spec.thinking === "deep" ? "开深思考" : "极简 ack，禁展开"}`,
    `产出: 写回 ${ROLE_FILE(dir, role)}（结论+证据路径），完成后调 pojia_swarm complete`,
    "纪律: 一次一个交付物; 缺参数用占位符继续; 命中拒绝不重论证任务性质",
  ].join("\n");
  return { ok: true, role, brief, resultFile: ROLE_FILE(dir, role) };
}

/** worker 交付: 写结果分片 */
export async function complete(cfg, target, role, workerId, resultText) {
  const dir = swarmDirOf(cfg, target);
  const spec = ROLES.find((r) => r.role === role);
  if (!spec) return { ok: false, reason: "unknown role" };
  await ensureDir(dir);
  const header = `# ${spec.step} / ${role}\n# worker: ${workerId}\n# at: ${new Date().toISOString()}\n\n`;
  await fsp.promises.writeFile(ROLE_FILE(dir, role), header + String(resultText || ""), "utf8");
  await fsp.promises.rm(CLAIM_FILE(dir, role), { force: true }).catch(() => {});
  return { ok: true, role, file: ROLE_FILE(dir, role) };
}

/** 指挥官汇总: 全部分片状态 */
export async function status(cfg, target) {
  const dir = swarmDirOf(cfg, target);
  let exists = true;
  try { await fsp.promises.access(dir); } catch { exists = false; }
  const planState = await plan(cfg, target);
  const out = [];
  for (const u of planState.units) {
    let worker = "-";
    let resultBytes = 0;
    if (exists) {
      try {
        const c = JSON.parse(await fsp.promises.readFile(CLAIM_FILE(dir, u.role), "utf8"));
        worker = c.workerId + (c.preempted ? "(preempted:" + c.preempted + ")" : "");
      } catch { /* no claim */ }
      try { resultBytes = (await fsp.promises.stat(ROLE_FILE(dir, u.role))).size; } catch { /* no result */ }
    }
    out.push({ role: u.role, step: u.step, claimedBy: worker, resultBytes });
  }
  return { target, active: exists, units: out };
}
