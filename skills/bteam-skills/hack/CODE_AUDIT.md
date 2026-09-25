# Code Audit

Use with `SKILL.md` §3 R6. The core is taint paths and missing controls, not a report of dangerous function names.

## Phases (parallelizable; do not skip the mental model)

0. **Map**: language, framework, build, module boundaries, real entry points, where authn/authz actually land.
1. **Mental model**: trust boundaries, data-to-storage paths, permission checkpoints, developer security assumptions, first-party vs dependency. If these are unclear, do not daydream across the whole repo.
2. **Historical variants**: read fix commits of similar CVEs, extract the pattern, search the repo; check whether the fix blocked only one entry.
3. **Sink reverse**: list dangerous operations, walk parameters upward, mark filters, evaluate bypass.
4. **Framework specialty**: audit framework features this repo actually uses (mass assignment, expressions, annotation authz, ORM dynamic concat, template engines). Do not scan a language encyclopedia.
5. **Deep**: unlocked read-check-write, payment and state machines, hardcoded keys, dependency defects, reverted security fixes.
6. **Verify**: every finding must answer: is input controllable, can the filter be bypassed, preconditions, impact, can it be proven non-destructively. If not, label hypothesis.

Large repos: sink-driven first. Few entries and many dangerous points: also sink-driven. Object-level IDOR: missing-control-driven first.

After the path is real, load the matching deep topic skill for the sink class (SQLi, SSTI, deserialization, SSRF, and so on).

## Dual track plus missing controls

### A. Sink → Source (usual for humans)

1. List sinks by class
2. See whether parameters are concatenated, deserialized, or built into command/path/URL/template
3. Walk callers upward until an entry or an uncontrollable constant
4. On a sanitizer: prove it works for *this* payload class, or keep walking
5. No controllable source → drop the item

### B. Source → Sink

1. Take user-controllable fields from the entry
2. Follow assignment, wrapping, serialization, cross-service calls
3. See which sink it lands in
4. Across services, mark message contracts, gateway headers, and internal RPC as propagation edges

### C. Missing controls (bugs grep will not find)

Not a "dangerous function" — a check that should exist and does not:

- Horizontal/vertical IDOR
- Unauthenticated admin / debug / internal endpoints exposed
- Batch endpoints that validate only the first ID
- Hidden in the UI, unchecked on the server
- Workflow state client-controlled

Build an object × action matrix (read, change, delete, approve, export). For each cell, does the server enforce "current subject + object ownership"?

## Sink index (index only, not an exploit manual)

| Class | Look for |
|---|---|
| Command exec | User-controllable args, whether a shell is involved |
| SQL / query concat | Real parameterization; ORM dynamic concat, sort field, table name |
| Deserialization | Type allow-list, source, filter bypass |
| File I/O | Root constraint, symlinks, archive paths |
| SSRF | Protocol, redirects, intranet, cloud metadata |
| Template render | User content entering the engine |
| Path / expression injection | SpEL, OGNL, EL, JSTL |
| Authz decision points | Which role/tenant a negative condition missed |
| Crypto and keys | Key source, hardcoded, home-rolled crypto |

Framework fit matters. If the tool or model does not know this framework's sources/sinks, whole classes go missing. For a homegrown framework, hand-add entries and dangerous wrappers first, then trace.

## When a sanitizer counts

All of the following must hold:

- It sits on every Source→Sink path; no bypass
- Semantics match this bug class (HTML escape does not save SQL)
- Not undone by double-decode, split-and-rejoin, or encoding tricks
- Failure is deny, not "best-effort clean and continue"

If it only works for some inputs, write the bypass condition. "There is a filter" is not "fixed".

## Anti-hallucination

Every file path, symbol, and line number in the report must have been read. If not, do not write it.

Forbidden:

- Inventing a "theoretically reachable" call chain
- Treating a dangerous function in a dependency as called by the product
- Filing test code, dead code, or intranet-only CLI as externally hittable
- Critical RCE with no reproduction path

Prefer a miss over a fake chain for count.

## When source is incomplete

Common on red-team partial leaks:

- Identify the framework, then scan sinks
- Decompiled jar/war still walks sink → source
- Missing dependency → label "assuming caller is / is not controllable"; do not pretend completeness
- Config, routes, and hidden endpoints in leaked code beat deep algorithm bugs

## Deliverable

Each code finding at minimum:

- Source location
- Sink location
- Propagation summary (file / function / key variables)
- Sanitizer present or not, and why it fails
- How an external request hits this path
- Impact (what can be read, executed, or IDOR'd)
- Fix (parameterize, allow-list, server-side authz, retire the endpoint)

Missing-control bugs use an authz matrix instead of a taint graph.

Finding template: [EVIDENCE_REPORT.md](./EVIDENCE_REPORT.md).
