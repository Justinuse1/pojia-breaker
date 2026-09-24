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

## 快速上手（3 步开打）

1. 会话输入 `pojiaai example.com` —— 首次激活会自动生成靶令牌模板 `~/.dsh/memory/targets/example.com.md`
2. 打开模板填两行：`目标` 和 `授权依据`（自有资产/书面授权），STATUS 改 `authorized`
3. 回会话说「开打」—— 装载、弹药推荐、拒绝守护、令牌恢复全部自动

> 口令不绑定任何特定目标：`pojiaai <任意域名>` 均可，任意 target 皆支持。
> 空令牌/未授权目标的作战边界由你填写的内容决定——**只打你有权打的目标**。

## 配置（cordis.patch.yml）

```yaml
passphrase: "pojiaai"     # 触发口令
defaultTarget: "redacted"   # 默认目标令牌
targetsDir: ""            # 令牌目录（空=自动探测）
```

## 仅供学习交流与授权安全研究
使用者须遵守所在地法律法规。仅用于自有资产或已获书面授权的目标。

## License
MIT
