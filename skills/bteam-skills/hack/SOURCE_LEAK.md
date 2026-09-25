# Source and Secret Leak Handling

Use with `SKILL.md` §3 R5. Red team: mine the clue to the end. Blue team: treat it as an incident, not a low-severity info-leak ticket.

How to detect and dump exposed VCS / backups: [insecure-source-code-management](../insecure-source-code-management/SKILL.md). This file is what to do after the leak is in hand.

## Identify first

Common shapes:

- `/.git`, `.svn`, backup tarballs, source packs, wrong object-storage ACL
- Public or semi-public org repos, employee personal repos, Gists, mirrors
- `.env`, sample configs, sourcemaps, CI artifacts, container image layers
- Secrets in docs, tickets, screenshots, demo videos
- "Already deleted" but still in git history or a fork

A clean current tree does not mean a clean history.

## Pipeline

```
Snapshot preservation
  → full acquire (current tree + history + dangling objects)
  → secret scan (verified first)
  → reconstruct structure (routes, config, env, CI, deps)
  → clues onto the map (intranet URLs, hidden APIs, old vulns, account model)
  → in-scope minimal read-only verification
  → impact and blast radius
  → report / incident escalate
  → owner decides rotation and invalidation
```

Red default: preserve and report; do not rotate production secrets on your own.
Blue default: treat as already compromised; push the owner to rotate. Deleting the file is not a fix.

## What must be mined

1. Secrets and identity
   - Cloud keys, repo tokens, CI secrets, DB passwords, private keys, webhooks, third-party APIs
   - Separate live / dead / unverifiable
   - Live secrets: only minimal read-only proof (whoami, list, metadata) to size the blast radius
2. History
   - Deleted commits, renamed files, forks from before a force-push
   - "Temporary" values in sample configs
3. Attack surface
   - Internal URLs, admin, debug routes, unpublished APIs
   - Microservice names, queues, bucket names
4. Engineering and supply chain
   - CI workflows, self-hosted runners, dependency sources, package names (dependency-confusion clues) → [dependency-confusion](../dependency-confusion/SKILL.md)
5. People and org
   - Mail, employee repos, test accounts, environment naming

## Verification discipline

- Purpose is severity, not more damage
- Fake-vs-real on production, plus one read-only call that returns identity or an object list — otherwise it is still a clue
- One failed verification does not become a destructive retry
- Full secrets do not go in report body, ticket plaintext, or chat
- Report writes: type, location, last-four or fingerprint, permission scope, verification action, verification time
- Third-party secrets out of scope: record and tell the authorizing party; do not log into third-party production

## Extra blue actions

- Open an incident, not a low-severity "information disclosure" ticket
- Look up use of that secret after it appeared (cloud audit, IdP, repo audit)
- Rotate, invalidate, clear sessions, check whether it was already used
- Same secret in images, tickets, chat, Terraform state
- Add detection: new public repos, new secret-scan hits, abnormal use of that identity

## Common failures

- Only report "`.git` is reachable"
- Only look at HEAD, not history
- File every scanner-hit fake secret as Critical
- Use a leaked secret to delete, create, or encrypt as "proof"
- Let the customer "delete it from git" count as the fix
- Paste a full AWS key into a PDF
