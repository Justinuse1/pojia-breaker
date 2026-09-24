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

```bash
dsh plugin add github:Justinuse1/pojia-pilot
```

或手动：克隆本仓库到 `~/.dsh/plugins/pojia-pilot`，重载 DSH。

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
