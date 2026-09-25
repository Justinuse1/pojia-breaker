# B-Team Skills — 24 项 Web 渗透技能库（源自 yaklang/hack-skills 精选）

pojia-pilot 战果引擎配套技能库。引擎会话开工前先读对应 SKILL.md 再动手。
宿主部署位置: ~/.dsh/skills/bteam-skills/（install.sh 自动部署）。

- **401-403-bypass-techniques** — 401/403 bypass playbook. Use when encountering access-denied responses on admin panels, API endpoints, or restricted paths. Covers path manipulation, HTTP metho
- **api-recon-and-docs** — API reconnaissance and documentation review playbook. Use when discovering endpoints, schemas, versions, OpenAPI specs, hidden docs, and surface area for API te
- **arbitrary-write-to-rce** — Arbitrary write to RCE playbook. Use when you have an arbitrary write primitive (from heap exploitation, format string, or OOB write) and need to convert it int
- **attack-surface-mapping** — Draw a testable attack surface from one authorized target URL or one
  application. Use when the user says 攻击面, 供给面, 画攻击面, map the surface,
  application recon,
- **authbypass-authentication-flaws** — Authentication bypass testing playbook. Use when assessing login flows, password reset logic, account recovery, MFA bypass, token predictability, brute-force re
- **cmdi-command-injection** — Command injection playbook. Use when user input may reach shell commands, process execution, converters, import pipelines, or blind out-of-band command sinks.
- **deserialization-insecure** — Insecure deserialization playbook. Use when Java, PHP, or Python applications deserialize untrusted data via ObjectInputStream, unserialize, pickle, or similar 
- **hack** — Entry P0 primary router and operating doctrine for HackSkills. Use when the
  task involves web application testing, API security assessment, recon,
  vulnerabi
- **http-host-header-attacks** — HTTP Host header injection and routing abuse playbook. Use when the application
  trusts the Host header for generating URLs, routing requests, or access contro
- **idor-broken-object-authorization** — IDOR and broken object authorization testing playbook. Use when requests expose object identifiers, tenant boundaries, writable fields, or missing object-level 
- **linux-privilege-escalation** — Linux privilege escalation playbook. Use when you have low-privilege shell access and need to escalate to root via SUID/SGID binaries, capabilities, cron abuse,
- **path-traversal-lfi** — Path traversal and LFI playbook. Use when file paths, download endpoints, include operations, archive extraction, or wrapper behavior may expose filesystem cont
- **recon-and-methodology** — Reconnaissance and methodology playbook. Use when mapping assets, discovering endpoints, fingerprinting technology, and building a structured testing plan for a
- **request-smuggling** — HTTP request smuggling and desynchronization testing. Use when front proxies,
  CDNs, or load balancers disagree with the origin on message framing
  (Content-L
- **reverse-shell-techniques** — (见 payload.json)
- **sqli-sql-injection** — SQL injection playbook. Use when input reaches SQL queries, authentication logic, sorting, filtering, reporting, or DB-specific blind and out-of-band execution 
- **ssrf-server-side-request-forgery** — SSRF playbook. Use when the server fetches URLs, resolves hostnames, imports remote content, or can be driven toward internal networks, cloud metadata, or secon
- **ssti-server-side-template-injection** — SSTI playbook. Use when template expressions, server-side rendering, preview features, or templating engines may evaluate attacker-controlled content.
- **subdomain-takeover** — Subdomain takeover detection and exploitation playbook. Use when targets have
  dangling CNAME/NS/MX records pointing to deprovisioned cloud resources, expired

- **tunneling-and-pivoting** — Tunneling and pivoting playbook. Use when establishing network tunnels through compromised hosts including SSH tunneling, Chisel, Ligolo-ng, socat, DNS/ICMP/HTT
- **type-juggling** — PHP type juggling and weak comparison (`==`) bypass. Use when authentication, HMAC/signature checks, or token validation uses loose equality, numeric coercion, 
- **upload-insecure-files** — (见 payload.json)
- **waf-bypass-techniques** — WAF bypass methodology and generic evasion techniques. Use when a web application
  firewall blocks injection payloads (SQLi, XSS, RCE) and you need to craft
  
- **xxe-xml-external-entity** — XXE playbook. Use when XML, SVG, OOXML, SOAP, or parser-driven imports may resolve external entities, files, or internal network resources.
