# Surface Patterns

Use with `SKILL.md`. Each row is a field shape. Recognize it, write down where the rest of the surface lives, stop grinding the decoy. Exploitation is not this file.

## Shells and twins

| You see | The rest of the surface is | Stop grinding |
|---|---|---|
| Open page is login HTML, captcha, SSO button | `service=` / `redirect_uri=` / `baseURL` / 302 / same-product `api`/`admin`/`gateway`, or the **same-host** API behind the form | Captcha, slider, login-box dictionary. Seeing login ≠ change asset |
| Login page belongs to another product (SSO / CAS / OAuth / unified auth) | Follow the callback back to **this** business plane. Do not audit the identity product | The foreign login HTML itself |
| Frontend RPC sits under a logged-in prefix; the same gateway also has `n` / `unlogin` / `guest` | The unlogin twin of the same cmd / method | Treating the logged-in 401 as "no API" |
| Business frontend account CRUD returns login-gate; a separate identity subdomain speaks the same account API without a cookie | That identity host: list / generate / reset-pwd | Stopping at the business frontend 401 |
| SPA interceptor puts `User-Id` / `employeeId` in a header and treats it as the session | Unauthenticated roster of numeric ids + the "current user" info API with that header swapped | Assuming no session exists because there is no cookie |
| Management SPA only jumps to SSO; no password box on the page | Backend still exposing a password login API | OCR on the SSO page |

## Client-named planes

| You see | The rest of the surface is | Stop grinding |
|---|---|---|
| `env.js` / `baseURL` / `apiHost` / `/prod-api` / `VUE_APP_*` | That host is the API plane. Paths in chunks belong there, not on the login host | Dir-brute on the login host |
| Webpack / umi chunks, sourcemaps, router `hidden` / `admin` | APIs the UI never renders. Hit them directly | Only mapping visible menus |
| Mini-program / APP / H5 wall; packet has `appId`, gateway, client salt | Those values are **this site's** keys | Treating the H5 login wall as the whole product |
| GraphQL / WebSocket / upload / XML / deserialize already in the inventory | They stay on the list for this site | Pretending they are invisible because they are not the first test |

## Keys that are surface

| You see | The rest of the surface is | Stop grinding |
|---|---|---|
| Frontend salt; write or list APIs take `timestamp` / `sign` / `nonce` and no cookie | Replay with a self-computed sign. Contrast: other APIs still want a session | Copying the salt into a report and stopping |
| Detail id is long ciphertext; JS has `modulus` / `exponent` / JSEncrypt | Encrypt neighbor plaintext serials (or the page's hardcoded `userid`) and swap | Treating ciphertext as unguessable, skipping identifier-swap |
| Page hardcodes a demo account / test tenant / experience entry | Use it as a key | Equating this with a login-form dictionary |
| Landing page / ops JSON has `skipPath` / `jumpUrl` whose query already carries a session-like token | That token against `me` / `info` | Only reading the CMS copy |
| Docs, demo zip, official HTML, or bundled JS contain a full app secret (not a placeholder) | The token-exchange or production-sign API named next to it | Filing the string as "info leak" without a plane to use it on |
| `getUploadSign` / STS / object `key` in the client | Storage list / overwrite / sibling bucket — not "upload works" | Stopping at store-and-download |

## Responses that grow the graph

| You see | The rest of the surface is | Stop grinding |
|---|---|---|
| List or detail succeeded | Same object's attachment, export, preview, approval. Parent auth often does not cover the child | Changing hosts after the list |
| Response newly names an id, download URL, token, internal host, role field | **This site's** queue, immediately | Treating them as log noise |
| Public list is filtered to published; detail / hidden tab / preview / export uses the same business id | The unpublished / internal body on that same id | Believing the list is the whole catalog |
| Fill-form / quiz model endpoint; schema includes standard answers or internal stems | The schema and sample-image preview, not the form title | Stopping at the public form chrome |
| Short-link resolver 302s; landing query has phone / name / amount | The resolver path + a short dictionary, not the welcome HTML | Homepage 302 to official site as "no surface" |

## Collapse, do not rematrix

| You see | The rest of the surface is | Stop grinding |
|---|---|---|
| Same title, skeleton, build hash, API prefix, login chain | 2–3 representatives. Siblings: only new path / port / app / `jump`/`service=`/`moduleId` plane | Full matrix on every mirror |
| Business paths extracted; unauth exceptions probed; remaining endpoints share one login-code family | Auth endpoints if present (session / reset / rebind / ticket-swap). Siblings: glance for new path or code change | Quotes on "please log in"; a new thread per leftover host |
| 403 + no business script + default server page | One-shot falsify; no business plane | Padding with a full injection matrix on the empty shell |

## Docs, debug, storage — only if this app already pointed here

| You see | The rest of the surface is | Stop grinding |
|---|---|---|
| Client or robots names Swagger / OpenAPI / `actuator` / `mappings` | Those JSON planes, including hidden routes in `mappings` | Full-template scanning as a substitute for the app inventory |
| `.git` / backup / `.env` linked from this host | History + secrets as a **new list of planes**, not a finding by itself | Reporting "`.git` reachable" and moving on |
| Object-storage sign proxy (`/api/storage/sign` or kin) with a `key` query | `key=/` list, then business prefixes from that list | Treating 403 on one key as "storage is closed" |
