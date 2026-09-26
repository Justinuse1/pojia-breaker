-- theater-facts.db schema
-- Ported from dsh-redteam-mode (MIT, Copyright (c) 2026 Jueze-2019)
-- https://github.com/Jueze-2019/dsh-redteam-mode — perupped for POJIA.AI theater persistence
-- One DB per theater: theaters/<id>/facts.db. engagement is directory-level isolation
-- (asset has no engagement_id column by design), cross-theater experience lives in ammo-knowledge.db.
-- 22 business tables + 2 FTS5 virtual tables + indexes. Python sqlite3 compatible (verified).

CREATE VIRTUAL TABLE IF NOT EXISTS asset_fts USING fts5(
  asset_id UNINDEXED, ip, names, banners, titles, fingerprints
);;

CREATE VIRTUAL TABLE IF NOT EXISTS poc_fts USING fts5(
  poc_id UNINDEXED, title, cve, component, versions, tags, description, content
);;

CREATE TABLE IF NOT EXISTS scan_run (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  agent_session_id TEXT, tool TEXT, argv TEXT,
  started_at TEXT, finished_at TEXT, status TEXT DEFAULT 'running'
);;

CREATE TABLE IF NOT EXISTS segment (
  cidr TEXT PRIMARY KEY, ip_start TEXT, ip_end TEXT,
  org TEXT, asn TEXT, country TEXT, city TEXT,
  source TEXT, first_seen TEXT, last_seen TEXT
);;

CREATE TABLE IF NOT EXISTS asset (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  segment_cidr TEXT NOT NULL, ip TEXT NOT NULL, ip_int INTEGER,
  state TEXT DEFAULT 'unknown', primary_name TEXT, confidence REAL,
  first_seen TEXT, last_seen TEXT, discovered_at TEXT,
  test_status TEXT DEFAULT 'untested', test_notes TEXT, test_surface TEXT,
  test_updated_at TEXT, test_updated_by TEXT, blocked_count INTEGER DEFAULT 0,
  priority TEXT, potential TEXT, assess_reason TEXT, assessed_at TEXT, assessed_by TEXT,
  UNIQUE(segment_cidr, ip)
);;

CREATE TABLE IF NOT EXISTS asset_name (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_id INTEGER NOT NULL, name TEXT NOT NULL, kind TEXT,
  provenance TEXT, tool TEXT, first_seen TEXT, last_seen TEXT,
  UNIQUE(asset_id, name, kind)
);;

CREATE TABLE IF NOT EXISTS port (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_id INTEGER NOT NULL, proto TEXT DEFAULT 'tcp', port INTEGER NOT NULL,
  state TEXT DEFAULT 'open', provenance TEXT, tool TEXT, banner TEXT,
  url TEXT, title TEXT,
  first_seen TEXT, last_seen TEXT,
  UNIQUE(asset_id, proto, port)
);;

CREATE TABLE IF NOT EXISTS service (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  port_id INTEGER NOT NULL, name TEXT, product TEXT, version TEXT, cpe TEXT,
  provenance TEXT, tool TEXT, first_seen TEXT, last_seen TEXT
);;

CREATE TABLE IF NOT EXISTS fingerprint (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_id INTEGER NOT NULL, port_id INTEGER,
  category TEXT, vendor TEXT, product TEXT, version TEXT,
  evidence TEXT, confidence REAL, provenance TEXT, tool TEXT,
  first_seen TEXT, last_seen TEXT
);;

CREATE TABLE IF NOT EXISTS observation (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  entity_kind TEXT NOT NULL, entity_id INTEGER NOT NULL,
  attr TEXT, value TEXT, provenance TEXT, tool TEXT,
  scan_run_id INTEGER, collected_at TEXT, raw_ref TEXT
);;

CREATE TABLE IF NOT EXISTS edge (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  src_kind TEXT NOT NULL, src_id TEXT NOT NULL,
  dst_kind TEXT NOT NULL, dst_id TEXT NOT NULL,
  relation TEXT NOT NULL, confidence REAL, scan_run_id INTEGER,
  first_seen TEXT, last_seen TEXT,
  UNIQUE(src_kind, src_id, dst_kind, dst_id, relation)
);;

CREATE TABLE IF NOT EXISTS tag (
  entity_kind TEXT NOT NULL, entity_id INTEGER NOT NULL, tag TEXT NOT NULL,
  note TEXT, created_by TEXT, created_at TEXT,
  PRIMARY KEY (entity_kind, entity_id, tag)
);;

CREATE TABLE IF NOT EXISTS vuln (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_id INTEGER, port_id INTEGER, cve TEXT, title TEXT, severity TEXT,
  source TEXT, confidence REAL, status TEXT, evidence TEXT, target TEXT,
  found_by_agent TEXT, found_at TEXT, gained TEXT, agent TEXT
);;

CREATE TABLE IF NOT EXISTS score_point (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT UNIQUE,
  name TEXT NOT NULL,
  category TEXT,
  points INTEGER DEFAULT 0,
  max_hits INTEGER DEFAULT 1,
  description TEXT,
  enabled INTEGER DEFAULT 1,
  sort_order INTEGER DEFAULT 0,
  created_at TEXT, updated_at TEXT,
  /* ── 按《突破入侵类得分规则》新增的判定字段（v0.11.0）────────────────────
     rule：规则号（RULE 1…25）；**同一 rule 的得分点共用该规则的得分上限**
     tier：同规则内的档位（普通权限/管理员权限/加成分…），面板与报告按它分组展示
     cap：该 rule 的累计得分上限（0 = 不设上限）
     dedup_scope：计分口径 service(同资产同端口只算最高一条) / system(同系统只算最高权限一次)
                  / target(整个目标只算一次) / none(按台卡节点数累加)
     legacy：1 = 旧版得分点（迁移后保留但停用，只作历史参照，不参与新口径计分） */
  /* src：《突破入侵类得分规则（合并版）》里的原序号（合并行写首个原序号），仅用于与原表对账 */
  src INTEGER,
  rule INTEGER,
  tier TEXT,
  cap INTEGER DEFAULT 0,
  dedup_scope TEXT DEFAULT 'service',
  legacy INTEGER DEFAULT 0,
  /* builtin：1 = 随《突破入侵类得分规则》分发的内置得分点（分值/上限/口径由规则锁定，
     用户只能改「启用/停用」）；0 = 用户自建点（可任意编辑，且不会被播种逻辑清掉）。
     历史教训：清理旧体系时用 code 名单判定是否内置，于是用户自建的得分点在
     下一次读取得分面板时被当成旧体系残留连同命中一起删掉 —— 「新增得分点」永远无效，
     而 saveScorePoint 还返回 ok，界面照样弹「已保存」。 */
  builtin INTEGER DEFAULT 0
);;

CREATE TABLE IF NOT EXISTS stage (
  code TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  subtitle TEXT,
  color TEXT,
  goal TEXT,
  sections TEXT,
  tools TEXT,
  transition TEXT,
  sort_order INTEGER DEFAULT 0,
  updated_at TEXT
);;

CREATE TABLE IF NOT EXISTS score_hit (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  point_id INTEGER NOT NULL,
  asset_id INTEGER, vuln_id INTEGER, step_id INTEGER, target TEXT,
  evidence TEXT, note TEXT,
  self_created INTEGER DEFAULT 0,
  port INTEGER,
  recorded_by TEXT, recorded_at TEXT,
  /* 本次命中的实际分值（NULL = 用得分点的默认 points）。
     《合并版》把同一项的多个档位合并成一条（如服务器主机权限"普通 10 / 管理员 50"、
     域名控制"一级 50 / 二级 20"），**档位差异只能落在每一条命中上**，
     否则"权限取高只计一次"无从表达。 */
  points INTEGER,
  /* 倍率：G5 数据规模翻倍（×2）/ G6 IPv6 成果 ×3。**作用在权限分上**，
     与 points 相乘后再参与上限累计。存下来是为了让面板与报告能解释"这条为什么是 200 分"，
     而不是让读者以为分值算错了。 */
  multiplier REAL DEFAULT 1
);;

CREATE TABLE IF NOT EXISTS credential (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_id INTEGER, host TEXT, username TEXT, secret_type TEXT,
  secret_value TEXT, secret_ref TEXT,
  privilege TEXT, source TEXT, tool TEXT, note TEXT,
  found_by_agent TEXT, found_at TEXT, agent TEXT,
  UNIQUE(host, username, secret_type)
);;

CREATE TABLE IF NOT EXISTS access_session (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_id INTEGER, host TEXT, username TEXT, method TEXT, privilege TEXT,
  session_ref TEXT, note TEXT, found_by_agent TEXT, obtained_at TEXT
);;

CREATE TABLE IF NOT EXISTS webshell (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_id INTEGER, url TEXT NOT NULL, shell_type TEXT, pass_key TEXT,
  secret_ref TEXT, privilege TEXT,
  status TEXT DEFAULT 'unknown', last_check TEXT, check_note TEXT, latency_ms INTEGER,
  note TEXT, found_by_agent TEXT, created_at TEXT, updated_at TEXT, agent TEXT,
  UNIQUE(url, pass_key)
);;

CREATE TABLE IF NOT EXISTS tunnel (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_id INTEGER, webshell_id INTEGER, kind TEXT, listen TEXT,
  entry TEXT, reach TEXT,
  entry_kind TEXT,
  status TEXT DEFAULT 'unknown', last_check TEXT, check_note TEXT, latency_ms INTEGER,
  pid TEXT, command TEXT, note TEXT, found_by_agent TEXT, created_at TEXT, updated_at TEXT, agent TEXT
);;

CREATE TABLE IF NOT EXISTS http_evidence (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  vuln_id INTEGER, asset_id INTEGER, label TEXT,
  method TEXT, url TEXT, status INTEGER,
  request TEXT, response TEXT, note TEXT,
  captured_by TEXT, captured_at TEXT
);;

CREATE TABLE IF NOT EXISTS attack_file (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  target TEXT NOT NULL, target_kind TEXT, name TEXT NOT NULL, kind TEXT,
  path TEXT NOT NULL, description TEXT, evidence TEXT,
  asset_id INTEGER, vuln_id INTEGER, created_by TEXT, created_at TEXT,
  UNIQUE(target, name)
);;

CREATE TABLE IF NOT EXISTS attack_step (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  seq INTEGER, stage TEXT, title TEXT, detail TEXT,
  asset_id INTEGER, vuln_id INTEGER, access_id INTEGER, point_id INTEGER,
  evidence_ref TEXT, tool TEXT, agent TEXT, result TEXT,
  recorded_by TEXT, recorded_at TEXT
);;

CREATE INDEX IF NOT EXISTS ix_asset_segment ON asset(segment_cidr);;

CREATE INDEX IF NOT EXISTS ix_asset_ip_int ON asset(ip_int);;

CREATE INDEX IF NOT EXISTS ix_port_asset ON port(asset_id);;

CREATE INDEX IF NOT EXISTS ix_port_port ON port(port);;

CREATE INDEX IF NOT EXISTS ix_service_port ON service(port_id);;

CREATE INDEX IF NOT EXISTS ix_service_name ON service(name, product, version);;

CREATE INDEX IF NOT EXISTS ix_fp_asset ON fingerprint(asset_id);;

CREATE INDEX IF NOT EXISTS ix_fp_product ON fingerprint(product, version);;

CREATE INDEX IF NOT EXISTS ix_edge_src ON edge(src_kind, src_id);;

CREATE INDEX IF NOT EXISTS ix_edge_dst ON edge(dst_kind, dst_id);;

CREATE INDEX IF NOT EXISTS ix_obs_entity ON observation(entity_kind, entity_id);;

CREATE INDEX IF NOT EXISTS ix_vuln_asset ON vuln(asset_id);;

CREATE INDEX IF NOT EXISTS ix_vuln_sev ON vuln(severity, status);;

CREATE INDEX IF NOT EXISTS ix_vuln_cve ON vuln(cve);;

CREATE INDEX IF NOT EXISTS ix_cred_host ON credential(host);;

CREATE INDEX IF NOT EXISTS ix_access_host ON access_session(host);;

CREATE INDEX IF NOT EXISTS ix_webshell_status ON webshell(status);;

CREATE INDEX IF NOT EXISTS ix_tunnel_status ON tunnel(status);;

CREATE INDEX IF NOT EXISTS ix_http_vuln ON http_evidence(vuln_id);;

CREATE INDEX IF NOT EXISTS ix_http_asset ON http_evidence(asset_id);;

CREATE INDEX IF NOT EXISTS ix_step_seq ON attack_step(seq, id);;

CREATE INDEX IF NOT EXISTS ix_attack_target ON attack_file(target);;

CREATE INDEX IF NOT EXISTS ix_score_hit_point ON score_hit(point_id);;

CREATE INDEX IF NOT EXISTS ix_score_hit_time ON score_hit(recorded_at, id);;

CREATE INDEX IF NOT EXISTS ix_score_hit_vuln ON score_hit(vuln_id);;

CREATE INDEX IF NOT EXISTS ix_score_hit_step ON score_hit(step_id);;

CREATE INDEX IF NOT EXISTS ix_step_asset ON attack_step(asset_id);;

CREATE INDEX IF NOT EXISTS ix_step_vuln ON attack_step(vuln_id);;

CREATE INDEX IF NOT EXISTS ix_step_recorded ON attack_step(recorded_at);;

CREATE INDEX IF NOT EXISTS ix_asset_segment_state ON asset(segment_cidr, state);;

CREATE INDEX IF NOT EXISTS ix_http_url ON http_evidence(url);;

CREATE INDEX IF NOT EXISTS ix_tunnel_asset ON tunnel(asset_id);;

CREATE INDEX IF NOT EXISTS ix_webshell_asset ON webshell(asset_id);;

CREATE INDEX IF NOT EXISTS ix_credential_asset ON credential(asset_id);;

CREATE INDEX IF NOT EXISTS ix_access_asset ON access_session(asset_id);;

CREATE INDEX IF NOT EXISTS ix_score_hit_asset ON score_hit(asset_id);;

CREATE VIEW IF NOT EXISTS v_asset_summary AS
SELECT a.id, a.ip, a.segment_cidr, a.state, a.primary_name, a.first_seen, a.last_seen,
  (SELECT COUNT(*) FROM port p WHERE p.asset_id = a.id AND p.state = 'open') AS open_ports,
  (SELECT COUNT(*) FROM observation o WHERE o.entity_kind = 'asset' AND o.entity_id = a.id AND o.provenance = 'passive') AS passive_signals,
  (SELECT COUNT(*) FROM observation o WHERE o.entity_kind = 'asset' AND o.entity_id = a.id AND o.provenance = 'active') AS active_signals
FROM asset a;;

CREATE VIEW IF NOT EXISTS v_asset_service AS
SELECT p.asset_id, p.port, p.proto, p.provenance AS port_provenance,
       s.name AS service, s.product, s.version, s.provenance AS service_provenance
FROM port p LEFT JOIN service s ON s.port_id = p.id;;

CREATE TABLE IF NOT EXISTS poc (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT NOT NULL,                -- 稳定标识（slug），智能体可直接引用
  title TEXT NOT NULL,
  kind TEXT,                         -- poc | exp | script | template | payload
  category TEXT,                     -- 归类：rce / deserialization / file-upload / sqli / unauthorized / auth-bypass / weak-password / ssrf / xxe / path-traversal / file-read / info-leak / privesc / tunnel / other
  cve TEXT,                          -- CVE / CNVD / 厂商编号
  component TEXT,                    -- 组件/产品（Weblogic、Shiro、泛微 OA…）
  versions TEXT,                     -- 影响版本
  severity TEXT,
  language TEXT,                     -- python | go | java | bash | http | nuclei | js | php
  source TEXT,                       -- web | self | manual | nuclei-template | kb
  source_url TEXT,
  description TEXT,
  usage TEXT,                        -- 用法/命令行示例
  content TEXT,                      -- 正文（脚本 / POC / 原始请求）
  path TEXT,                         -- 落盘位置（pocs/<code>/<file>），便于智能体直接 cat
  verified INTEGER DEFAULT 0,        -- 是否实测验证过
  verified_note TEXT,                -- 验证证据（哪台目标、什么回显）
  hit_count INTEGER DEFAULT 0,       -- 被复用次数
  used_on TEXT,                      -- 最近一次使用在哪个靶标/目标
  -- 来源溯源：这条知识是在哪个靶标、哪台资产上发现/验证出来的（建立时间看 created_at）
  engagement_id TEXT,
  engagement_name TEXT,
  asset_target TEXT,
  found_by_agent TEXT,
  tags TEXT,
  created_by TEXT, created_at TEXT, updated_at TEXT,
  UNIQUE(code)
);;

CREATE INDEX IF NOT EXISTS ix_poc_cve ON poc(cve);;

CREATE INDEX IF NOT EXISTS ix_poc_component ON poc(component);;

CREATE INDEX IF NOT EXISTS ix_poc_kind ON poc(kind, verified);;
