# pojia-pilot 测试组安装说明

**版本基准(2026-09-25)**
- pojia-pilot **v0.3.4**(仓库 commit `b86a3df`)
- dsh-purge(环境层)**v1.1.19**,速配 DSH 宿主 **0.1.7-rc.1**
- 测试平台:Windows 11 / Linux(社区版 DSH desktop-next)

---

## 一、前置条件

1. **DSH 社区版桌面端已装好并能正常启动**(0.1.7-rc.1 系;官方 EXE 版未验证,勿混用)
2. 本机有 `git`(安装脚本要用;没有的话先装:https://git-scm.com)
3. 只测试**自有资产或已获书面授权**的目标 —— 这是红线,脚本和文档里都写死了

## 二、一键安装

**Windows(PowerShell):**
```powershell
irm https://raw.githubusercontent.com/Justinuse1/pojia-breaker/master/plugins/pojia-pilot/install.ps1 | iex
```

**Linux / macOS:**
```bash
curl -sL https://raw.githubusercontent.com/Justinuse1/pojia-breaker/master/plugins/pojia-pilot/install.sh | bash
```

脚本会自动完成:
1. 安装 pojia-pilot v0.3.4(作战层)→ `~/.dsh/plugins/pojia-pilot`
2. 检测并自动拉装 dsh-purge v1.1.19(环境层)→ `~/.dsh/plugins/dsh-purge`
3. 生成靶令牌模板 `~/.dsh/memory/targets/example.com.md`

装完**重启 DSH**。启动日志里出现 `dsh web: http://127.0.0.1:<端口>/` 即宿主正常。

> 若 dsh-purge 拉取失败(网络原因),pojia 基础功能照常可用,只是少了环境层补丁。可手动补:
> `git clone --depth 1 https://github.com/YuJunZhiXue/dsh-purge ~/.dsh/plugins/dsh-purge`

## 三、验证安装(5 分钟自检)

1. **插件就位**:DSH 设置 → 已安装插件 → 应看到 `pojia-pilot` 和 `dsh-purge` 各一条
2. **补丁应用**:purge 装好后首次重启会自动打宿主补丁(40/43 左右,少数 skipped 属正常)
3. **口令激活**:会话里输入
   ```
   pojiaai example.com
   ```
   返回激活确认即通。首次使用先编辑 `~/.dsh/memory/targets/<你的目标>.md`,填 `授权依据` 并把 STATUS 改为 `authorized`

## 四、常用命令

| 命令 | 作用 |
|---|---|
| `pojiaai <域名>` | 口令开局,装载破甲+SOP+看门狗 |
| `/autopilot <域名>` | 挂机:全阶段自动循环 |
| `/autopilot <域名> 验证利用` | 挂机限定:只跑该阶段(侦查/排序/验证利用/数据验证/痕迹清理) |
| `/autopilot stop` | 停止挂机 |
| `/ammo <目标描述>` | 弹药推荐 Top3 |

内置保护(测试组重点观察项):
- **SOP 条令**:五阶段轮数预算,爆破类尝试有硬上限,每 3 次失败必须出小结
- **效率看门狗**:爆破/扫描类连跑 4 次预警、6 次强停换面
- **拒绝守护**:命中拒绝自动走恢复链(存进度→新会话→令牌恢复)

## 五、测试反馈要点

遇到问题请附上:
1. `~/.dsh/logs/` 下最新宿主日志
2. 执行的命令和模型回复截图
3. `pojia-pilot` 版本(设置页可见)

已知边界(不算 bug):
- 官方 EXE 版宿主未适配(勿报)
- 偶发 skipped 补丁 = 该组件本机不存在,正常
- 挂机状态存磁盘,宿主重启后自动恢复继续

---

**pojia.ai** · © 2026 POJIA.AI · 仅供授权安全研究与教学使用
