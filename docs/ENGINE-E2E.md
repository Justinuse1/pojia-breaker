# 战果引擎 (Victory Engine) — E2E 验证记录 2026-09-25

## 概念
把已完全打穿的会话通过宿主原生 session/fork 复制为新会话(完整继承全部上下文),
注入"作战移交指令"(靶替换)后, 新会话以老战场的全部战术经验开打新靶。

## 已验证的完整链路(160宿主实测)
1. **fork**: POST /api/session/fork {"type":"client-request","rpcId":..,"method":"session/fork",
   "payload":{"args":{"request":{"sessionId":"<源会话>"}}}}
   → {"result":{"ok":true,"value":{"sessionId":"<新会话>"}}}
   新会话 seq 结尾带 session/end-seed {"inherited": true}
2. **注入**: POST /api/session/prompt {"payload":{"args":{"request":{
     "requestId":"<uuid>","sessionId":"<新会话>","mode":"queue",
     "content":[{"type":"text","text":"[作战移交·操作员指令] ...靶替换..."}]}}}}
   → {"accepted":true}
3. **观测**: session/list (wire参数名 _request) 看 running/asOfSeq/title;
   session/page (wire参数名 request) + address:{kind:"session",sessionId} 拉事件流。

## 实测结果
- fork 立即返回新会话id; 继承29个turn全量上下文(cursor=3062)
- 注入后自动开跑: running:true, title 自动生成"Pojiaai example-target.com session (1)"
- 纪律表现: 没有继承旧归档结论, 主动"重新活体取证"(DNS四解析器/双实现全端口扫描/CT证书/Wayback全历史/同IP横向)
- 产出: L1_RECON_AND_PLAN.md 结构化报告 + 穷尽性自查("未试项: 无") + 决策门方案
- 全程零拒绝, 无需人工干预

## 通道要求
- RPC over HTTP POST {base}/api/{namespace}/{method}, body {type:"client-request",rpcId,method,payload}
- unary方法不走 /api/remote.mux (WS流通道只收stream模式)
- 需要 Origin 头匹配 --trusted-host

## 待做
- 引擎模板库(按靶型分类的已打穿会话登记)
- /engine use <模板> <新靶> 一键指令(封装fork+注入+follow)
- 驾驶话术autopilot联动(卡住自动续接)
