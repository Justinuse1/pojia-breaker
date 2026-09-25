# Test Matrix and Effort

Use with `SKILL.md` §3. What to hit first, what "tested" means per class, and when you must not stop. Probe recipes live in deep topic skills.

## 1. Effort order

Do not delete classes. If an entry exists, finish it or write N/A plus reason. Spend effort first on surfaces more likely to reach influential control:

1. Unauthenticated access to another user, tenant, or subject
2. Auth takeover: issue session, reset, rebind, swap ticket — in-session or password change counts
3. Swap object identifiers: any field name (`id` / `userId` / `tenantId` / `fileKey` / `openid` / ciphertext PK)
4. Authenticated writes and business logic: add role, change amount or state, skip approval, coupon/inventory concurrency
5. Injection, SSRF, XSS, command or template execution on surfaces that show a **diff**
6. Salts, hardcoded keys, demo accounts in scripts and pages

No session: unauthenticated success → swap identifiers → auth endpoints → script keys → injection/SSRF/XSS/exec on differential surfaces.

With a session: swap identifiers while authenticated → add fields / skip steps / money → then put injection on business parameters that already return data.

Low-priority even if present: self-only CSRF, upload that only stores-and-downloads with no follow-on chain, login-form weak passwords.

GraphQL, upload, XML, WebSocket, deserialization: if this site exposed them, finish or write N/A. Do not insert them *before* identifier-swap and takeover, and do not pretend they are invisible.

## 2. Type matrix

Tick every class against the current endpoint inventory. Information disclosure alone is not a pass.

| Class | Done means |
|---|---|
| Unauthenticated | Critical read/write with credentials stripped. On success, swap identifiers |
| IDOR | No account: after unauthenticated success, swap. With account: record same-subject baseline, then neighbor account, identifiers copied from responses, `0`/`-1`/empty, plus attachments/exports |
| Injection | Only endpoints where count, content, or a fetched URL can change. Each filter/sort/keyword param: baseline → probe → diff. Full "please log in" with no business fields → N/A the class. Pick probes for the actual stack; do not throw only quotes |
| SSRF | Every URL / callback / webhook / file / fetch / import / preview / proxy parameter, proven to intranet, metadata, or an outbound control |
| Command or template exec | Command, expression, template, deserialization, dangerous upload followed to execution or falsified |
| Credentials | After copying a string, pass the liveness gate: production accepts the real value (rejects a fake) and one read-only call returns identity or a list |
| Default creds | Middleware/component naked defaults that actually issue a session. Login-form weak passwords are not mandatory. Hardcoded demo accounts are keys |
| Sensitive paths | Swagger / Actuator / debug / heapdump / env; secrets found here get mined |
| XSS | Reflected on reflection points; stored on write-then-read-back; combine with whether unauthenticated read is possible |
| Upload | Type, path, executable or SSRF or business IDOR. Do not stop at store+download |
| Path traversal | `file` / `path` / `filename` / `key` |
| CSRF | Write succeeds with missing or bad token; self-only CSRF is not a primary result |
| Logic and privilege | Write endpoints that add role/amount/state; multi-step skip; money/coupon/stock to small or negative; claim/approval gets one concurrency pass. No such endpoint → N/A |
| Auth takeover | Inventory has issue-session, reset, rebind, ticket-swap, or step-up → tick. Username/password boxes are not injection surfaces |
| Other field surfaces | Classes this table does not name still get tested |

After classifying the surface, load the matching deep topic skill for probes (`SKILL.md` §3 signal table).

## 3. Do not stop on a half-chain

| You saw | You must continue to |
|---|---|
| File channel open | Business API, executable, path, or SSRF chain |
| OTP or slider passed | Does the code return in-band, bind an account, reset swap the user |
| Config has host but no creds | Keep looking for the full credential |
| Copied a secret | Fake-vs-real + identity or list, read-only |
| Same-role readable, public static, HTTP 200 JSON | Pivot to cross-user, injection, or privilege |
| Response sprouted id / download URL / token / internal host | Onto this site's queue |
| List or detail passed | Same object's attachment, export, preview, approval — one more shot |
| Medium already confirmed | Follow the same object to write, cross-user, takeover, or execution before changing targets |

## 4. Parameters, diffs, and response classes

Script inventory must answer whether these exist: business paths, signing salts, ciphertext identifiers, hidden routes, demo accounts. Write "none" if absent.

Classify the response before spraying:

| Response looks like | It is | Do |
|---|---|---|
| One sentence "please log in", no list/total/roster/detail | Login gate | N/A the injection class; do not throw quotes per path |
| Has list / total / business fields, even `total=0` | Differential surface | Swap params, swap identifiers, inject per stack |
| Error, timeout, or length/timing clearly off baseline | Differential surface | Compare once or twice; stop if the diff is unstable |
| Missing a parameter dumps a roster or detail | Unauthenticated exception | Treat as unauthenticated + identifier swap |

1. Open the real page, capture the full request (query + body + headers).
2. List every filter and identifier field, including short enums.
3. On a differential surface, each filter param at least: normal, empty, illegal, stack-appropriate probe, and if needed a location change (query / json / header / path).
4. Diff is hard evidence: same-subject baseline count or fields vs post-probe count and other-subject fields.
5. After a block, retry once with encoding or location change; still no diff → stop. Do not spray forever.
6. List passed → hit attachments and exports. Parent authorized, child often not.

## 5. Scope modes

**Locked** (user gave a fixed site or list):

- Do not scan unrelated brand lines before entering the site
- Must follow: extra hosts the entry already ships, post-login gateway and API domain, extra paths on the same host, same-product business hosts in scripts
- If the user marked priority assets, hit that group first; do not stall on the first login wall

**Exploratory** (user gave an org name and allowed boundary expansion):

- Multiple seeds become a queue; deep-mine one live cluster at a time
- Dedup, drop dead pages and non-alive hosts, then enter
- Remaining live surfaces on this cluster unfinished → do not fill progress with a new search
- Write a change log before the next cluster; re-request authorization if needed

A batch of sites that share the same login shell: finish auth endpoints on a representative, then on the others only look for new reset/rebind/ticket-swap paths. No new endpoint → do not open a full matrix per site.

## 6. Pre-conclusion self-check

- [ ] On differential surfaces, each filter param got an injection or IDOR diff
- [ ] Unauthenticated tested with credentials stripped
- [ ] Cross-user / cross-tenant tested — not only "tenant admin can read in-role"
- [ ] With a session: object graph, identifier swap, extra fields, step skip
- [ ] Upload followed to executable, SSRF, or business IDOR
- [ ] Auth chain followed past OTP / slider
- [ ] "Admin" was not misread as "in-role therefore not a bug"
- [ ] After a block, location or encoding changed; injection probes matched the stack
- [ ] This round did not over-index on unauthenticated reads
- [ ] Injection / SSRF / XSS / exec were actually tested, not one quote per path
- [ ] Confirmed medium on an object was chained up; response clues entered the queue
- [ ] Copied credentials passed the liveness gate
- [ ] Session findings were not written as anonymous unauthorized
- [ ] Portrait was written; scripts extracted more than paths
- [ ] Empty list / error was not treated as "please log in"
- [ ] List passed → attachments and exports were hit
- [ ] The full matrix was not poured into the same-family login code
