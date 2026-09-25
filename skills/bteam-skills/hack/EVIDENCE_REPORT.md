# Evidence and Report Standard

Shared by red and blue. Read this before writing a conclusion.

## Minimum evidence block

Any "confirmed" vulnerability, intrusion, or risk must be reproducible by someone who was not in the room.

```
Title
Location (URL / host / repo path / rule name / event ID)
Time (with timezone)
Preconditions
Step-by-step repro or step-by-step query
Observed result (redacted response, command output, or raw event)
Impact (what control was obtained / what harm was done)
Non-destructive proof (what was done, what was not)
Residual risk
Fix or detection recommendation
Evidence attachment names
```

Missing repro or query → "hypothesis" or "insufficient evidence" only.

Working directory: `assets/` for inventories and script excerpts, `evidence/` for requests and diffs, `reports/` for confirmed items only. Process notes are not official findings.

## Readability

- Screenshots include address bar, key parameters, time, result; red box plus one sentence when needed
- Requests and responses strip cookies, tokens, ID numbers, full secrets
- Command output keeps the few lines that prove privilege — not a full junk screen
- Queries are complete and copyable; filters, index, and time window are explicit
- Timezones are consistent; cross-zone systems note the conversion on the timeline

## How to write secrets

| May write | Must not write |
|---|---|
| Secret type, last four, fingerprint | Full secret, full cookie |
| Permission scope, whether liveness was verified | A connection string that can log in directly |
| File path and commit | Unredacted ID numbers, phones, mail bodies |

Full secrets go only in the authorizing party's agreed vault, with expiry.

## Red-team report structure

1. Decision summary: deepest impact layer reached, what to fix now
2. Attack-chain narrative (by time, not by CVE number)
3. Confirmed findings (finding template below)
4. Uncovered and time-box limits
5. Detection gaps (for blue)
6. Appendix: raw scanner output, compliance items

Do not put a Nessus/Nuclei export in the body.

## Blue-team case structure

1. One-sentence conclusion
2. Impact scope (users, hosts, data, business)
3. Timeline
4. Queries and raw event excerpts
5. Containment done and how to roll it back
6. Eradication / recovery
7. Detection and logging improvements
8. Open questions

## Severity (impact first)

Use the impact ladder; CVSS is a cross-check only:

- Critical: production high privilege or bulk sensitive data already held or immediately reachable, or an intrusion in progress
- High: auth bypass, object-level IDOR to core data, live cloud key, stable path to a host
- Medium: extra conditions needed but the path is real
- Low: isolated config issue
- Info: a clue that helps later testing; not harm by itself

Unexploitable theory is not High. High requires the exploit conditions in writing.

## Immediate notify

Do not wait for close-out when:

- Production data can be read or changed without authorization
- Live cloud key / domain-admin equivalent
- Signs of an intrusion in progress
- Testing accidentally affected the business (lockout, outage)

Notify: time, asset, confirmed impact, suggested immediate action, what we stopped.

## Two write-to-disk gates

### Session-attribution gate

Before writing "anonymous" or "unauthorized with no identity", ask: did the breaking request carry a session?

- Session present → IDOR or auth issue: "used the current session to reach someone else's object"
- Still works with credentials stripped → then write unauthenticated
- Tested with a session, then stripped the cookie in the report to label anonymous = forbidden

### Secret liveness gate

Copying a string is not a finding. Private keys, access keys, connection strings, JWTs, sessions usable as someone else, must satisfy both:

1. Fake rejected, real accepted by production
2. One non-impacting read-only call returns identity or an object list

Fail the gate → clue only. Placeholders, expired values, fake and real getting the same error, frontend salts used to encrypt a phone number — not results.

## Do not file as results

A half-chain; weak password that never issued a session; connection string with host and no creds; secret that failed the liveness gate; self-only CSRF; missing security headers; expired cert with no exploit path; HTTP 200 JSON; same-role-readable or public ops data; unauthenticated SMS send with no account takeover or password change. If unsure, do not file.

Medium, high, and critical: write to disk as soon as confirmed. Do not batch until the end. Same type on the same URL in the same task: do not file twice.

## Voice

- Say what was achieved, not brochure tone, not an "attacker" performance
- Impact is the real privilege surface this door opens, not how many shots this test fired
- Do not invent destructive actions that were not performed; a can-change / can-delete surface may be described, marked as not executed
- Repro steps keep only the requests needed to break; comparisons and copied parameters sit in the step that uses them — no empty extra steps

---

## Finding template

Copy and fill. Delete inapplicable rows; do not leave filler.

~~~~md
## [ID] Title (impact in one sentence)

- Severity: critical / high / medium / low / info
- Status: confirmed / hypothesis / insufficient evidence
- Impact-ladder position: cloud/domain-admin equivalent | host or service privilege | service-account abuse | auth bypass or IDOR | chainable misconfig | isolated medium | compliance
- Asset:
- Environment: prod / staging / test / unknown
- Found at (timezone):
- Found how: red-team test / code audit / source leak / blue triage / hunt
- Did the break carry a session: yes / no (session present → do not write "anonymous unauthorized")
- Title register: anonymous unauthenticated (no session, reached someone else) / IDOR (session, someone else's object) / auth takeover / other
- Secret liveness gate: n/a / not passed (clue) / passed (fake-vs-real + identity or list)
- Matrix ticks: unauth / IDOR / injection / SSRF / exec / logic / upload chain / other; no entry → N/A + reason

### Problem
(Three to six sentences. What the attacker can do now, whom it harms.)

### Location
- URL / host / account / resource ID:
- Code: `path:line` symbol
- Config: effective file path
- Related commit / image / pipeline:

### Preconditions
- Account required:
- Role:
- Network position:
- Other:

### Repro or query
1.
2.
3.

### Diff
- Baseline:
- After probe:
- Subject or fields that changed:

### Observation
```
(redacted response, command output, or raw event)
```

### Taint or control path (code audit)
- Source:
- Propagation:
- Sink:
- Sanitizer: none / present but failed (why) / effective (if effective, do not file as confirmed)
- Authz-matrix gap:

### Source-leak clues (if applicable)
- Leak shape:
- History mined:
- Secret type and fingerprint:
- Read-only verified:
- Next-hop assets:

### Impact
- Control proven:
- Possible but unverified (hypothesis):
- Data or systems involved:

### Non-destructive statement
- Did:
- Did not:

### Remediation
1. Immediate:
2. Root:
3. How to verify the fix:

### Detection (for blue)
- Telemetry that should have been visible:
- Suggested rule hypothesis:
- Why existing rules missed it:

### Attachments
- Screenshot / request / query-export filenames:
~~~~

---

## Detection-rule template

Fill completely before production. Fail the quality gate → do not deploy.

```md
## Rule name

- Status: draft / test / prod / retired
- Owner:
- Created:
- Last tuned:
- ATT&CK: Txxxx (sub-technique too)
- Severity: by business impact, not the product default
- Mode: strict / broad (broad needs a reason)

### Hypothesis
If the attacker does ________, we should see ________ in ________.

### Data source
- Product and index:
- Key fields:
- Field-dictionary link:
- Source health check:
- Retention:

### Logic
(Pseudocode or Sigma-style. Intent, not an unportable private GUI screenshot as the only truth.)

### Known TP fixture
- Source: red team / hunt / historical case / controlled exercise
- How to fire:
- Last hit:

### FP profile
- Expected benign fires:
- Suppression:
- Retro window and result (7–30 days):
- FP rate:

### Investigation hints
1. Look first at:
2. Then expand to:
3. When to label benign TP:
4. When to contain immediately:

### Containment suggestions
- Reversible actions:
- Actions that need approval:

### Retirement
- When to merge, shrink, or take offline:
- On six-month silence, check what first:

### Coverage gap
- What this rule explicitly cannot catch:
- Logs needed but not yet ingested:
```

---

## Pattern-card template

Only for techniques recognizable on another system of the same shape. Site-specific paths, campaign IDs, and dead endpoints are not cards. Medium findings go in the report, not on a card.

```md
## Recognize
(Framework / parameter shape / business surface. Not a vendor, product, or path.)

## Where to hit
(A method, not the only entry. Say whether a session is required.)

## What counts as success
(Must answer: whose what appeared beyond baseline. HTTP 200 alone is forbidden.)

## False points
(When this shape is not a bug. This run not breaking through does not retire the technique.)

## Do not stop at
(Common half-chain endpoints, and where the chain must go)
```
