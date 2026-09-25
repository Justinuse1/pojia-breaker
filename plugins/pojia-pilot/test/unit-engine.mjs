import test from "node:test";
import assert from "node:assert/strict";
import * as engine from "../lib/engine.js";
import * as theater from "../lib/theater.js";
import * as sop from "../lib/sop.js";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const tmpCfg = () => ({ dshHome: fs.mkdtempSync(path.join(os.tmpdir(), "pj-eng-")) });

test("engine: handoverText 含靶替换与既成事实措辞", () => {
  const t = engine.handoverText({ sourceTarget: "old.com", chain: "SQLi→RCE" }, "new.com", "做L1测绘");
  assert.match(t, /既成事实/);
  assert.match(t, /old\.com/);
  assert.match(t, /new\.com/);
  assert.match(t, /L1测绘/);
});

test("engine: handleCommand reg/list/del 往返", async () => {
  const cfg = tmpCfg();
  let out = await engine.handleCommand(cfg, "reg tpl1 session-abc old.com 全链");
  assert.match(out, /已登记/);
  out = await engine.handleCommand(cfg, "list");
  assert.match(out, /tpl1/);
  out = await engine.handleCommand(cfg, "del tpl1");
  assert.match(out, /已删除/);
  out = await engine.handleCommand(cfg, "list");
  assert.match(out, /为空/);
});

test("engine: use 无网关时给出可读错误", async () => {
  const cfg = { ...tmpCfg(), engineGateway: "http://127.0.0.1:1" };
  const out = await engine.handleCommand(cfg, "use session-x new.com");
  assert.match(out, /fork 失败|注入失败/);
});

test("theater: 建区→记事件→落战果→移交 持久化往返", () => {
  const cfg = tmpCfg();
  theater.ensureTheater(cfg, "test.com", { owned: true });
  theater.logEvent(cfg, "test.com", "fork 引擎会话 session-x");
  theater.logEvent(cfg, "test.com", "L1 完成");
  const f = theater.saveFinding(cfg, "test.com", "L4_exploit", "poc.md", "# PoC\nworks");
  assert.ok(fs.existsSync(f));
  const st = theater.theaterStatus(cfg, "test.com");
  assert.ok(st.findings.L4_exploit.includes("poc.md"));
  assert.match(st.timeline, /L1 完成/);
  const h = theater.writeHandover(cfg, "test.com", { chain: "SQLi→RCE", lessons: " Tab 绕 WAF" });
  assert.ok(fs.existsSync(h));
  assert.match(fs.readFileSync(h, "utf8"), /SQLi→RCE/);
});

test("theater: 靶名非法字符被净化", () => {
  const cfg = tmpCfg();
  const dir = theater.ensureTheater(cfg, "../evil.com");
  assert.ok(!dir.includes(".."));
});

test("sop: watchdog verdict 附战术驾驶语", () => {
  const messages = [];
  for (let i = 0; i < 4; i += 1) {
    messages.push({ role: "assistant", content: [{ type: "tool_use", name: "bash", input: { command: `hydra -L u.txt -p p.txt target` } }] });
  }
  const v = sop.watchdogCheck(messages, {});
  assert.ok(v.length >= 1);
  assert.match(v.join("\n"), /战术驾驶/);
});

test("sop: driveLine 四类语料非空", () => {
  for (const k of ["continue", "correct", "reroute", "organize"]) {
    assert.ok(sop.driveLine(k).length > 4);
  }
});
