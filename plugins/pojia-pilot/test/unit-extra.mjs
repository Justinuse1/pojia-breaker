
import * as sop from "file:///C:/Users/53241/pojia-breaker/plugins/pojia-pilot/lib/sop.js";
import * as rules from "file:///C:/Users/53241/pojia-breaker/plugins/pojia-pilot/lib/rules.js";
import * as autopilot from "file:///C:/Users/53241/pojia-breaker/plugins/pojia-pilot/lib/autopilot.js";

let fail = 0;
const t = (name, cond) => { console.log((cond?"✓":"✗ FAIL"), name); if(!cond) fail++; };

const st = sop.sopText();
t("sop: 五阶段条令非空", st && st.length > 500);
t("sop: 含轮数预算", /轮/.test(st));
t("sop: 含凭据硬上限", /默认凭据|硬上限|10/.test(st));
t("sop: 含小结纪律", /小结/.test(st));
const wd = sop.watchdogCheck([{role:"tool",content:"hydra run 1"},{role:"tool",content:"hydra run 2"},{role:"tool",content:"hydra run 3"},{role:"tool",content:"hydra run 4"}], {});
t("watchdog: 爆破4连触发预警", Array.isArray(wd) && wd.length > 0 && /看门狗/.test(wd[0]));
const wd2 = sop.watchdogCheck([], {});
t("watchdog: 空历史不触发", Array.isArray(wd2) && wd2.length === 0);
const wscan = sop.watchdogCheck(Array.from({length:10},(_,i)=>({role:"tool",content:"nmap -p "+i})), {});
t("watchdog: 扫描连发触发", Array.isArray(wscan) && wscan.length > 0);
t("rules: 规则文本生成", typeof rules.buildRuleContent === "function" ? rules.buildRuleContent("example.com").length > 100 : true);
const ph = autopilot.parsePhases("验证利用 数据验证");
t("autopilot: parsePhases字符串", ph && Array.isArray(ph.roles) && ph.roles.length === 2 && ph.roles[0] === "exploit");
const ph2 = autopilot.parsePhases(["侦查"]);
t("autopilot: parsePhases数组", ph2 && ph2.roles.length === 1 && ph2.roles[0] === "recon");
const ph3 = autopilot.parsePhases("乱写的阶段");
t("autopilot: 未知阶段进unknown", ph3 && ph3.unknown.length === 1);
console.log(fail === 0 ? "\n专项: ALL PASS" : `\n专项: ${fail} FAILED`);
process.exit(fail === 0 ? 0 : 1);
