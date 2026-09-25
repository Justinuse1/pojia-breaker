# Red-Team Execution

Use with `SKILL.md` §§2–3. How to pick targets, expand scope, and close out. Exploit recipes live in deep topic skills.

## Before kickoff

- Written authorization, RoE, in/out-of-scope lists, banned techniques, data handling, emergency contact, stop conditions
- Confirm IPs / domains actually belong to the authorizing party — do not trust a spoken CIDR alone
- Create the evidence directory and a change log (scope expansion, high-severity finds, pauses)
- Agree the immediate-notify threshold for high-severity finds

No authorization letter or equivalent approval → stop.

## Impact ladder

Report and daily triage use this ladder, not scanner scores:

1. Cloud / domain-admin equivalent
2. Host shell or high-privilege service
3. Abuseable service account / role
4. Auth bypass, object-level IDOR, secret read
5. Chainable misconfiguration
6. Isolated medium
7. Pure compliance (security headers, banner, CVE with no path)

Layer 7 may go in an appendix. It is not a primary result.

## Engagement loop

See field features first, then open the matching check class (`SKILL.md` §3 and `TEST_MATRIX.md`). Opening one class is not firing only that shot. Unlisted field surfaces still get tested.

```
Authorization and scope → passive recon → attack-surface inventory → priority path
    → minimal proof → follow clues / request expansion
    → freeze evidence → notify high-severity immediately → attack-chain narrative
    → clean test artifacts (non-destructive) → hand detection gaps to blue
```

Recon answers what the system already exposes. Do not open with exploitation.

## Per-site loop

Do not empty-scan a site.

1. **Portrait** (3–5 sentences): who uses it, core objects, where money/power/state live, what an unauthenticated caller can touch.
2. **Inventory**: capture real requests. Scripts record more than paths: signing salts, ciphertext identifiers, hidden routes, hardcoded demo accounts. Write "none" if absent. If scripts fail to download, use captured traffic and inline page content — do not idle.
3. **Find the business surface**: if the open page is login, follow redirect params, `baseURL`, 302, and same-brand `api` / `admin` / `gateway` to the business host or local gateway. Dig unauthenticated against business APIs, not login HTML. Do not audit someone else's SSO page; follow it back to this product's business surface.
4. **Classify the response**: a full sentence "please log in" with no business fields → N/A the injection class. `list` / `total` / business fields (even `total=0`) → differential surface. Errors, timeouts, and length diffs are also differential surfaces. An empty list is not "please log in".
5. **Same-family login codes**: unauthenticated exceptions already probed, remaining business endpoints all return the same login code → stop injection. If the inventory still has issue-session / reset / rebind / ticket-swap, finish those auth endpoints before marking this round done.
6. **With a session, walk the object graph immediately**: list → detail → attachment / export / approval; swap identifiers at each layer. Do not keep throwing quotes at business endpoints after you are in.
7. **Minimum to change sites**: portrait exists, inventory exists, matrix ticked or N/A+reason per entry, confirmed medium on an object either chained up or falsified. A thin shell can be falsified at a glance — do not pad time with the full matrix.

Username/password boxes are not injection surfaces. Extra tenant/module fields on the login API are.

## Scope-expansion protocol

Clues you may follow (still same authorized org, not banned by RoE):

- Adjacent subdomains, historical DNS, staging/preview, docs sites, monitoring and debug entry points
- Forgotten admin ports, object storage, CI artifacts, container registries
- Source leaks, secret leaks, employee public repos
- Auth, SSO, VPN, bastion shared with the target

Actions:

1. Record asset, how found, time
2. Confirm ownership (whose cert, whose page, whose org account)
3. Write the expansion reason
4. Shallow probe first (alive, fingerprint, is there an entry); request depth only if valuable
5. No exploit, no password spray, no intrusive scan before approval

Missing boundary assets is negligence. Expanding without a record is a violation.

Do not fill progress with a new search while live surfaces on the current cluster are unfinished. Identifiers, download URLs, and internal hosts in responses go onto this site's queue. A login page is a shell — find the post-login business host first.

## Non-destructive proof whitelist

Prefer these to prove impact:

- Identity: current user, roles, permission list
- Read-only enumerate: object list, bucket list, repo list, mail metadata
- Config read: can you see the secret-management page, pipeline variable names
- Request-level: an unauthorized endpoint returned an object it should not
- File-level: path plus a redacted fragment of a sensitive file

When a write is required:

- Identifiable test object (clear prefix)
- Single row, deletable, notified in advance
- Record the rollback method immediately
- IDOR write proof: create your own test object, delete it after; do not alter other people's business rows
- Do not log out a user-provided session

## Password and auth testing

- Read lockout, MFA, CAPTCHA, rate limit first
- Unknown threshold → do not spray
- Default passwords, test accounts, and example passwords in docs beat blind spraying
- Login-form weak passwords are not mandatory; middleware default creds and hardcoded demo accounts are keys
- On lockout: stop and notify; do not "try a few more"

## Middleware audit (document-driven)

Build a live checklist before touching anything. Every row needs a result and evidence.

| Field | Write |
|---|---|
| Component and exact version | Not just "Nginx" |
| Official docs / baseline link | The version you compared against |
| Effective config path | Main + includes + env vars |
| Exposure | Port, protocol, admin plane, extra protocols (e.g. AJP) |
| Auth mode | Anonymous / password / mTLS / ACL / cloud IAM |
| Default creds and debug entry | Still on? Who can reach it? |
| Plugins / modules / extensions | Extra surface |
| TLS and listener split | Internal and external listeners mixed? |
| Known version defects | Only those for this version and verifiable |
| Logs and audit | Logs shipped off-box? Can local root unilaterally delete evidence? |
| Deviation from official recommendation | One deviation per row |

Minimum:

- Admin plane not naked on the internet
- Auth before network-trust
- Transport encryption; backup keys separated from data
- Audit logs leave the host

The process record is itself a deliverable. Do not invent checklist items or sinks from memory.

Then load [unauthorized-access-common-services](../unauthorized-access-common-services/SKILL.md) for service/port technique detail.

## Close-out

- Recover test accounts, test objects, temporary privileges
- High-severity finds already synced immediately
- The report is an attack chain; the appendix is the inventory
- Paths the red team used that blue did not see → detection gaps for blue
- State clearly: this is a time-box snapshot, and what was not covered
