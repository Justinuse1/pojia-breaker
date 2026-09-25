# pojia-pilot

> **别人给你解锁，我们给你打准。**
> DeepSeek Harness (DSH) 红队战术自动化插件 —— 口令一键开局 · 拒绝守护 · 令牌恢复 · 弹药推荐

purge 类插件解决「能不能」，pojia-pilot 解决「怎么赢」。
弹药有数据、战术有实证、失误有恢复，全链路自动化。

## 功能

### 🗝️ 口令一键开局
会话里输入 `pojiaai`（或 `pojiaai <target>` 指定目标）：
- 自动装载破甲规则 + 极简 ack 注入（30 token 硬约束）
- 自动读取 `memory/targets/<target>.md` 授权令牌
- 思考挡位提醒（off 短铺 → low/medium 执行，禁 max）

### 🛡️ 拒绝守护
模型回复匹配拒绝模式 → 页面顶部红条告警 →
一键执行：**存进度 → 新会话 → 令牌自动恢复**（拒绝不跨会话携带）

### 🎯 弹药推荐
输入目标描述 → 按 31 发弹药 × 双靶实测弱点谱（四级评分数据）推荐 Top3 + 战术建议

### 📋 作战条令 (SOP)
五阶段条令常驻注入（侦查→排序→验证利用→数据验证→痕迹清理），每阶段带轮数预算与产出物要求：
- 低成本优先：默认凭据→已知CVE→配置缺陷→fuzz，顺序不可倒置
- 检索先于自研：有现成 exploit 用现成，禁止重造轮子
- 每 3 次失败必须出阶段小结，触顶即停换面

### 🐕 效率看门狗
pre-step 钩子统计工具调用节奏，低效循环自动干预：
- 爆破/目录枚举/端口扫描类连跑 4 次预警、6 次强停换面
- 连续 8 步无文本产出判空转，强令输出卡点小结

### 🤝 purge 共存 (rules 桥)
检测到 [dsh-purge](https://github.com/YuJunZhiXue/dsh-purge) 时自动把靶型作战上下文写成 purge rule，走 AGENTS.md 常驻注入——新会话免口令直接带上下文。

### 🌙 无人值守 (autopilot) 与阶段限定
`/autopilot <target>` 挂机自动循环（蜂群分片 plan→claim→执行→complete）；支持阶段限定：

```
/autopilot example.com 验证利用        # 只跑该阶段，其余跳过
/autopilot example.com 验证利用 数据验证  # 多阶段
/autopilot stop                        # 停止
```

限定范围全部交付 → 收官报告 → 自动停。状态存磁盘，宿主重启不丢。

### 📊 实证底座
- 31 发弹药 × deepseek-flash / gpt-5.5 双靶交叉矩阵
- 思考开关时序（off→low）实测 ASR 0.13 → 0.22
- 一次一个交付物的贪心纪律内置

## 安装

**Linux / macOS / 160 服务器：**
```bash
curl -sL https://raw.githubusercontent.com/Justinuse1/pojia-breaker/master/plugins/pojia-pilot/install.sh | bash
```

**Windows (PowerShell)：**
```powershell
irm https://raw.githubusercontent.com/Justinuse1/pojia-breaker/master/plugins/pojia-pilot/install.ps1 | iex
```

或手动：克隆 [pojia-breaker](https://github.com/Justinuse1/pojia-breaker)（`plugins/pojia-pilot/`）到 `~/.dsh/plugins/`，重载 DSH。

> **环境层说明**：安装脚本会自动检测并拉取 [dsh-purge](https://github.com/YuJunZhiXue/dsh-purge) **最新版**（环境层，宿主补丁+常驻注入）。purge 的 `dshTarget` 字段仅为声明，运行时按 pattern 匹配打补丁——匹配不到的（如官方 EXE 专属补丁）自动软跳过，**不会打坏文件**。实测 v1.1.20 在 DSH 0.1.7-rc.1 上：40 applied / 0 pending / 4 skipped，全部兼容。拉取失败不影响 pojia-pilot 基础功能（守护/弹药/SOP/看门狗纯提示层即可运行）。两层齐全 = 完整战力。

## 快速上手（3 步开打）

1. 会话输入 `pojiaai example.com` —— 首次激活会自动生成靶令牌模板 `~/.dsh/memory/targets/example.com.md`
2. 打开模板填两行：`目标` 和 `授权依据`（自有资产/书面授权），STATUS 改 `authorized`
3. 回会话说「开打」—— 装载、弹药推荐、拒绝守护、令牌恢复全部自动

> 口令不绑定任何特定目标：`pojiaai <任意域名>` 均可，任意 target 皆支持。
> 空令牌/未授权目标的作战边界由你填写的内容决定——**只打你有权打的目标**。

## 配置（cordis.patch.yml）

```yaml
passphrase: "pojiaai"     # 触发口令
defaultTarget: "example"   # 默认目标令牌
targetsDir: ""            # 令牌目录（空=自动探测）
```

## 仅供学习交流与授权安全研究
使用者须遵守所在地法律法规。仅用于自有资产或已获书面授权的目标。

## Author

**pojia.ai** · © 2026 POJIA.AI — 弹药有数据、战术有实证、失误有恢复。

## License

MIT © 2026 POJIA.AI。第三方组件声明见 [THIRD-PARTY-NOTICES.md](../../THIRD-PARTY-NOTICES.md)。


## v0.4 战果引擎 + 战区持久化（2026-09-25）

### /engine — 战果引擎
把"已完全打穿的会话"fork 成新会话（宿主原生 session/fork，完整继承全部上下文），注入战区移交指令后对新靶续打：

```
/engine list                          模板库清单
/engine reg <名> <源会话id> <源靶> [链]  登记模板（须亲手打穿的会话）
/engine use <名|会话id> <新靶> [任务]    fork + 注入，启动作战
/engine status [前缀]                  引擎会话状态
/engine tail <会话id> [n]              拉最新产出
```

面板: POST /pojiaai/engine {"cmd":"use tpl1 new.target.com L1测绘"}

铁律：模板只能登记"亲手打穿"的会话（有完整工具调用+证据落盘链）；纯指挥/授权对话会话做模板，注入会被模型识别为话术而拒绝（实测）。

### /theater — 战区持久化
对齐 findings/evidence 结构，跨会话战果落盘：

```
<~/.dsh>/theater/<靶>/TARGET.md + TIMELINE.txt + findings/L1..L5/ + handover.md
```

激活时自动建区；`/theater handover <靶>` 产出的移交摘要就是引擎 fork 的任务书底稿。

### 战术驾驶语（autopilot 增强）
watchdog 判定（预警/强停/空转）自动附对齐实战驾驶术的话术（纠偏/换线/续接四类语料）。

### 实测依据
三轮真实跳板资产实战 3/3 成功（见 docs/ENGINE-R5-R7.md）：引擎会话自主开工、只读纪律、归属判定、穷尽性自查全部复现。
