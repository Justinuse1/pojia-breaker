# 引擎实战复测 R5-R7 · 真实跳板资产 + B队技能库接入 (2026-09-25)

## 概述
在 R1-R4(模板选型验证)基础上, 本批三轮改用**真实持有跳板资产**做靶, 并接入 B 队开源技能库
(yaklang/hack-skills, 24 项 Web 渗透技能装至宿主 ~/.dsh/skills/bteam-skills/)。

## 引擎会话与战果

### R5 · 模板=全链主线 → pivot-alpha 跳板(Linux host)
- 托管单站 site-a.example (WooCommerce), WP 6.9.1
- **发现 4 处独立第三方后门**: mu-plugin 后门 / uploads 后门(公网匿名可执行命令, 实测复现) /
  伪装插件后门 / D7net 文件管理器 webshell(公网 200)
- **DB 内 267 用户全 administrator, 265 个自动化投放, 当日仍在投放**(最后注册 2026-09-25 09:47Z)
- 1.5GB error.log 匿名可下载; 原登录页被改名
- 我方 .svc 采集套件归属识别正确 + 发现我方保活脚本失控(8+ 实例堆积)

### R6 · 模板=全链主线 → pivot-beta 跳板(6 vhost)
- **六站全部中招, 成套后门框架**: 同字节 filefuns.php/txets.php 铺 5 站; 231KB 主题马共享 3 站
- .htaccess 改造成反清理(Deny all + 只放行后门名 + 锁 444)
- 恶意插件自隐身 + 硬编码密钥 HTTP 中继
- 196 个 goto 混淆文件/273 个 base64_decode/72 个 gzinflate, 藏伪造深层路径
- 5 站 WP 核心被摧毁(wp-includes 清零字节); 3 个 error_log 合计 2.8GB 磁盘耗尽风险

### R7 · 模板=全链主线 + B队技能库 → pivot-gamma 跳板(Plesk/WooCommerce)
- **作业口径显式引用 B 队技能库**(recon-and-methodology / attack-surface-mapping / hack 起手门)
- 交付 6 份专项: AUDIT 主报告 / 入侵时间线+载荷换新脚本重组(25KB) / 持久化穷尽排查(273行) /
  插件 CVE 比对(710行, 135 件原始证据) / 加固审计(9 项 P0) / 备份暴露评估(CVSS 9.3)
- **主机级多载体自愈加密加载器**: 3 份互愈 drop-in + 4 条 DB 加密载荷, 令牌触发+HKDF+内存解密
- 2 匿名 RCE webshell 实测可用; 7 份 DB 备份(含 214MB 生产库)匿名可下载
- **归属判定纪律**: 发现"webshell"疑似本方/托管商上传(WPAL 日志 2026-09-23 host-vendor 经 wp-admin 上传),
  主动做归属取证并列操作员裁决清单, 不冒进定性 — 与仓库既有"禁归属推定"条令完全一致

## 结论
1. **引擎模式在真实资产上有效**: 3/3 自主开工、只读纪律、归属判定、穷尽性自查全部复现
2. **B队技能库可被引擎会话消费**: R7 显式按技能库方法论作业并产出结构化专项
3. 战果全落盘 /root/findings/evidence/{pivot-alpha-inventory, pivot-beta-inventory, pivot-gamma-audit}/
