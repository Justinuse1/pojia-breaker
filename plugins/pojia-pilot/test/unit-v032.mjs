/**
 * pojia-pilot / test/unit-v032.mjs
 * v0.3.2 三层新机制单元测试(零依赖, node 直跑):
 *   A. transmute 合规转译
 *   B. persist 磁盘状态机
 *   C. compat 版本速配
 * 用法: node test/unit-v032.mjs
 */
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const results = [];
const t = (name, fn) => {
  try { fn(); results.push(`✓ ${name}`); }
  catch (e) { results.push(`✗ ${name}: ${e.message}`); process.exitCode = 1; }
};

// ── A. transmute ──
const { transmute, transmuteLegend } = await import("../lib/transmute.js");

t("transmute: 破解→旁路验证", () => {
  const r = transmute("破解这个靶机的登录");
  assert.ok(r.text.includes("旁路验证"), r.text);
  assert.ok(!r.text.includes("破解"), r.text);
  assert.ok(r.hits.length > 0);
});
t("transmute: 长词优先(密码爆破→弱凭据审计, 不被'爆破'单独截胡)", () => {
  const r = transmute("爆破密码");
  assert.ok(r.text.includes("弱凭据审计"), r.text);
});
t("transmute: 渗透测试→授权安全评估", () => {
  const r = transmute("对内网目标做渗透测试");
  assert.ok(r.text.includes("授权安全评估"), r.text);
  assert.ok(r.text.includes("内网横向移动边界验证"), r.text);
});
t("transmute: 英文描述同样收敛", () => {
  const r = transmute("bruteforce the login and exploit the service");
  assert.ok(r.text.includes("weak-credential audit"), r.text);
  // exploit 会被中/英规则其一收敛(中文规则漏洞利用|exp(loit)? 优先)——两种产物都算合规转译成功
  const okKnown = r.text.includes("known-vulnerability verification") || r.text.includes("已知缺陷复核");
  assert.ok(okKnown, r.text);
  assert.ok(!/\b(bruteforce|exploit)\b/i.test(r.text), "原攻击词应被转译: " + r.text);
});
t("transmute: 空文本/无命中安全通过", () => {
  assert.deepEqual(transmute("").hits, []);
  const r = transmute("正常句子无命中");
  assert.equal(r.text, "正常句子无命中");
  assert.deepEqual(r.hits, []);
});
t("transmute: 非攻击文本不改写(侦查/端口扫描不在映射表)", () => {
  const r = transmute("对目标做端口扫描和服务识别");
  assert.equal(r.text, "对目标做端口扫描和服务识别");
});
t("transmuteLegend: 非空", () => {
  assert.ok(transmuteLegend().length > 50);
});

// ── B. persist ──
const persist = await import("../lib/persist.js");
const tmpHome = fs.mkdtempSync(path.join(os.tmpdir(), "pojia-persist-"));
const cfg = { dshHome: tmpHome };

t("persist: save→load 往返", () => {
  persist.saveFlag(cfg, { target: "example-target", until: Date.now() + 60_000, owned: true });
  const f = persist.loadFlag(cfg);
  assert.equal(f.target, "example-target");
  assert.equal(f.owned, true);
  assert.ok(f.remainingMs > 50_000);
});
t("persist: 过期自动清除并返回 null", () => {
  persist.saveFlag(cfg, { target: "x", until: Date.now() - 1, owned: false });
  assert.equal(persist.loadFlag(cfg), null);
  // 文件应已被清理
  const file = path.join(tmpHome, "memory", "pilot-mode.flag");
  assert.equal(fs.existsSync(file), false);
});
t("persist: 损坏文件视为未激活", () => {
  const file = path.join(tmpHome, "memory", "pilot-mode.flag");
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, "{broken json", "utf8");
  assert.equal(persist.loadFlag(cfg), null);
});
t("persist: clearFlag 幂等", () => {
  persist.clearFlag(cfg);
  persist.clearFlag(cfg);
  assert.equal(persist.loadFlag(cfg), null);
});
fs.rmSync(tmpHome, { recursive: true, force: true });

// ── C. compat ──
const compat = await import("../lib/compat.js");
const tmpHome2 = fs.mkdtempSync(path.join(os.tmpdir(), "pojia-compat-"));
const cfg2 = { dshHome: tmpHome2 };

t("compat: 全API在 → criticalOk", () => {
  const fakeCtx = {
    systemPrompt: { section() {} },
    tools: { register() {} },
    webServer: { register() {} },
    on() {},
    commands: { register() {} },
  };
  const r = compat.probe(fakeCtx, cfg2);
  assert.equal(r.criticalOk, true);
  assert.deepEqual(r.missing, []);
  assert.deepEqual(r.degraded, []);
});
t("compat: 缺 webServer → degraded 不致命", () => {
  const fakeCtx = { systemPrompt: { section() {} }, tools: { register() {} } };
  const r = compat.probe(fakeCtx, cfg2, { force: true });
  assert.equal(r.criticalOk, true);
  assert.deepEqual(r.degraded, ["webServer.register", "ctx.on(hooks)", "commands.register"]);
});
t("compat: 缺 systemPrompt → critical missing", () => {
  const fakeCtx = { tools: { register() {} } };
  const r = compat.probe(fakeCtx, cfg2, { force: true });
  assert.equal(r.criticalOk, false);
  assert.ok(r.missing.includes("systemPrompt.section"));
});
t("compat: 版本未变走缓存, 版本变了自动重探测", () => {
  const fakeCtx = { systemPrompt: { section() {} }, tools: { register() {} } };
  const r1 = compat.probe(fakeCtx, cfg2, { force: true });
  assert.equal(r1.cached, false);
  const r2 = compat.probe(fakeCtx, cfg2);
  assert.equal(r2.cached, true, "版本没变应读缓存");
  // 模拟 runtime 升级: 改 compat 文件里的 hostVersion 戳
  const file = path.join(tmpHome2, "memory", "pilot-compat.json");
  const prev = JSON.parse(fs.readFileSync(file, "utf8"));
  prev.hostVersion = "0.0.1-old";
  fs.writeFileSync(file, JSON.stringify(prev));
  const r3 = compat.probe(fakeCtx, cfg2);
  assert.equal(r3.cached, false, "版本变了应自动重探测");
});
t("compat: brief 可读", () => {
  const b = compat.brief(compat.probe({ tools: { register() {} } }, cfg2, { force: true }));
  assert.ok(b.includes("版本速配"));
  assert.ok(b.includes("MISSING"));
});
fs.rmSync(tmpHome2, { recursive: true, force: true });

// 报告
console.log(results.join("\n"));
console.log(`\n${results.filter((r) => r.startsWith("✓")).length}/${results.length} passed`);
