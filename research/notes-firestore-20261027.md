# Notes Firestore direction — progress 2026-10-27

## Requested boundary

Explore moving Notes storage from Koofr to Firestore while preserving the current UI and all user-visible behavior. No billing enablement, cloud database creation, real-data migration, deployment, secret reuse, or production access was authorized. Work was done on the existing local branch `codex/notes-owner-open-experiment-20261027` from the Notes `release/minimal-notes` source ancestry.

## Environment and access check

The current shell is the NAS ARM64 environment (`uname` reports aarch64; available memory at inspection about 2 GiB, root volume free about 1.4 GiB). `firebase`, `gcloud`, and `gsutil` were not found. `~/.config/gcloud` was absent. These environment variables were unset: `GOOGLE_APPLICATION_CREDENTIALS`, `GOOGLE_CLOUD_PROJECT`, `GCLOUD_PROJECT`, `FIREBASE_CONFIG`, `CLOUDSDK_CONFIG`. No credential files were searched or read, and no Gemini/Koofr/Homepage credential was accessed. This means no suitable Firebase CLI or Google Cloud session/access could be verified in the shell.

The default Firestore emulator port 8080 is already bound, but the prepared emulator config uses loopback port 8089. Java is not installed. A temporary Java 21 download was attempted; network transfer remained below 50 KiB/s with a projected completion over 20 minutes. It was canceled before extraction/installation, and all created temporary JRE/npm/emulator cache paths were cleaned. No emulator process was started and no system package was installed.

## Code prepared

- Added `lib/firestore-storage.mjs`, a dependency-injected Firestore-compatible transport for the existing `NoteStore` protocol. `api/app.js` and `appConfig` are unchanged; Koofr remains the active backend and the new adapter cannot be selected by production configuration.
- Existing business logic is reused for CAS/revisions, fencing, idempotency, share ACL/revocation, trash/purge/restore and snapshot verification. The transport implements root lease claim/expiry/unlock and requires a valid current fencing token on writes/deletes. It denies an unguarded catalog reseed outside a freshly created root.
- Firestore documents are limited to 700 KiB binary chunks plus a manifest, with transaction-consistent reads and SHA-256/byte-count verification. This lets the prototype carry existing note records above Firestore's 1 MiB document limit while preserving the current application-level 3.1 MB ceiling.
- Added the exact runtime dependency `@google-cloud/firestore@9.4.0`, pinned in package-lock. SDK initialization is deliberately not wired to the live API because no project identity or Google authorization exists.
- Added `firebase.json` with Firestore only, bound to `127.0.0.1:8089`, and deny-all `firestore.rules`; the emulator runner accepts only `demo-hunghvt-notes` and a loopback 8089 endpoint. It cannot target a real project.
- Added mock transaction tests for save/CAS/idempotency, hash tamper rejection, multi-chunk records, simultaneous lock claims, expiry/fencing/stale unlock, share revocation, trash/verified purge, and backup/restore to a separate namespace. Test fixture is in-memory and is not represented as the Firebase emulator.

Node 24 full suite: **154/154 pass** (`v24.22.1`). Emulator smoke guard check exits with `FIRESTORE_EMULATOR_GUARD` when the endpoint/project are absent. Real emulator and real cloud access were not tested.

## Gemini advisory and Codex assessment

One advisory call to `gemini-task` succeeded via `key1` / `gemini-3.5-flash-lite`; only filtered architecture context was sent, no secret or Notes content. Gemini recommended a direct Firestore repository/API rewrite over a WebDAV-compatibility transport. It highlighted split-brain/stale lease risks, transaction abort/backoff, immediate share revocation, idempotency atomics, document size limits, and read/write cost. It suggested a mock/SQLite surrogate because the NAS lacked Firebase CLI/Java/ADC.

Codex agrees a native Firestore repository is the cleaner long-term shape, and agrees the root lease, request charges, document sizing and IAM need explicit qualification. The current adapter is a narrower parity prototype because it reuses existing thoroughly tested business logic and cannot change the active backend; it is not being recommended as a permanent architecture. SQLite was not used because its locking/transaction behavior would not validate Firestore semantics. The in-memory fake establishes protocol parity only; an actual Firestore emulator test remains a gate.

## Official docs checked

- Firebase server Admin/Firestore clients authenticate with ADC/IAM, and production server libraries use IAM rather than client Security Rules. The application still must enforce owner/share authorization.
- Firestore has a 1 MiB document ceiling; current Cloud Firestore free quota is 1 GiB storage, 50,000 document reads/day, 20,000 writes/day and 20,000 deletes/day for exactly one free database per project. Exceeding the free allowance requires billing; no billing was enabled.
- Firebase Local Emulator Suite requires Firebase CLI and Java. Demo project IDs (`demo-*`) have no live resources, and emulator traffic uses `FIRESTORE_EMULATOR_HOST`.
- Vercel documents Google Cloud Workload Identity Federation. It can use short-lived Vercel OIDC identities instead of a persistent service-account JSON key. Runtime API integration still needs implementation and a scoped IAM trust/config.

Primary references: [Firebase Admin setup](https://firebase.google.com/docs/admin/setup), [Firestore IAM](https://cloud.google.com/firestore/docs/security/iam), [Firestore limits](https://cloud.google.com/firestore/quotas), [Firestore pricing](https://firebase.google.com/docs/firestore/pricing), [Local Emulator Suite](https://firebase.google.com/docs/emulator-suite/install_and_configure), [emulator project isolation](https://firebase.google.com/docs/emulator-suite/connect_firestore), and [Vercel GCP OIDC](https://vercel.com/docs/oidc/gcp).

## Cloud permission path (not yet requested from the user)

When needed, use an existing Google Cloud project with an authorized administrator; do not create a project or enable billing. A project administrator needs to create the Firestore database, Workload Identity Pool/Provider for the intended Vercel project/environment, and a dedicated service account; grant the runtime account only `roles/datastore.user` and bind Vercel OIDC to impersonate it. The Vercel project needs the non-secret project/pool/provider/service-account identifiers. No Google service-account JSON key, API key, or token is required in chat. Phone/iPad entry point: [Firebase Console](https://console.firebase.google.com/) or [Google Cloud Console](https://console.cloud.google.com/).

The console setup could require project IAM/workload-identity/service-account administrator permissions; the user has not indicated that such access exists. If the console requires enabling billing or a new project, stop and reassess rather than proceeding.

## Decision / next gate

Keep Koofr active. First run the prepared demo-project emulator test only after Java/CLI can be supplied within NAS resource limits; next, compare the native repository design with the compatibility adapter and build a request/cost model. Before any Vercel Preview/cloud test, obtain explicit project/WIF authorization and verify that the intended Firestore database fits the free-tier constraints. Do not switch backend, deploy, seed real data, or migrate until emulator parity, cost, backup/restore, production authentication and rollback have been reviewed.

Notes code is local-only, unpushed, and not deployed: commit
`8e6d0dbfe63396fa2fc5b1e8c7e707a7db3cb66a` on branch
`codex/notes-owner-open-experiment-20261027`, checkout
`/home/admin/Hunghvt-notes`.

## Native repository continuation — 27/10/2026

Kept the compatibility adapter intact and made a separate local branch
`codex/notes-firestore-native-20261027`. Added a native repository prototype
and design at `Hunghvt-notes/lib/firestore-native-repository.mjs` and
`Hunghvt-notes/docs/firestore-native-design.md`. It uses per-note CAS
transactions, immutable content revisions, compact operation receipts,
share-token reads in the same transaction as note reads/writes, and share-count
guards for Code Inbox. History is separate version documents; chunks start only
above 750 KiB. API integration remains disabled.

Focused Node 24 tests pass **8/8**: create/update revision CAS, same-op replay
including concurrent duplicate requests, same-base competing writers,
independent-note writes, share/revoke, five history revisions, large chunked
content/hash readback, and Inbox blocking when a share exists. These tests use
an in-memory Firestore-shaped fake. They do not establish transaction locking,
retry/billing behavior, or cloud latency.

Scope still missing before native feature parity: folder APIs and atomic
multi-note operations, order CAS, trash/restore/purge, consistent backup/restore,
and the real emulator/cloud test. Existing browser draft code, GitHub OIDC and
envelope crypto, UI routes, and application response contract are intended to
stay. Native path replaces the root catalog/lease, global receipts/folder/share
maps, DAV lock/fencing, and DAV inventory/purge/backup internals. User-visible
atomic folder/trash guarantees need an explicit native protocol before wiring.

One Gemini critique was requested with filtered architecture only. It correctly
flagged same-note contention, multi-note lock sets, operation retention, chunk
amplification, purge fanout, and checking ACL on every operation. Codex rejected
its fixed “one write per second” assertion (official docs say per-document rate
is workload-dependent) and its claim of a 500 combined read+write cap. Google
release notes say the service removed the old 500-write Commit/transaction cap;
current quota docs list a 500 field-transform limit. Some SDK references retain
their own 500-write constraints, so behavior for the pinned Node Admin
transaction must be checked on a real target before deciding the 500-note edge.
Read/write count estimates
and exact gaps are in the Notes design document.

Cloud path: current NAS shell still has no Firebase/gcloud CLI or verified ADC.
For the least user setup, use Google Cloud Shell from a phone/iPad in an already
authorized dedicated non-production project with an existing Firestore database
and a user grant of `roles/datastore.user`, then run only the synthetic
namespaced smoke test. That role grants project-level data access, so a
production Notes project is not a safe test target. This does not use NAS
credentials and does not require Vercel OIDC. A
NAS-origin test separately needs an installed Cloud CLI plus ADC or scoped
workload identity. Vercel production separately needs GCP Workload Identity
Federation scoped to the Vercel project/environment and a dedicated service
account. No project/database was created, no billing enabled and no cloud call
made. Official references and steps are in `Hunghvt-notes/docs/firestore-native-design.md`.

During a requested full local-suite check, 119 tests passed and 6 test files
failed to load because `iron-session` is not installed in this checkout. The
suite also ran its existing synthetic fixture cleanup allowlist: it reported
39 synthetic probe folders removed, production root present and unrelated folder
names unchanged. Focused native tests were then run separately and passed.

The Notes branch is local-only, based on the previous adapter branch and
uncommitted at this handoff; no push/deploy/cloud access occurred. See
`Hunghvt-notes` branch `codex/notes-firestore-native-20261027`.

## Follow-up: offline suite and Cloud Shell package — 27/10/2026

The earlier missing `iron-session` report was a checkout dependency-install
state, not a missing manifest/lock entry. `npm ci --ignore-scripts --no-audit
--no-fund` completed successfully with Node 24. Notes branch
`codex/notes-firestore-cloudshell-20261027` is now on GitHub at
`ebd704d3a149f5756dbc8b9a41eda5f326efe09b`. Its offline test runner removes
Koofr/OIDC variables and refuses non-loopback network requests; mocked cleanup
logs are suppressed so they cannot be mistaken for real Koofr deletion. Local
Node 24 suite: 163/163 passed. Cloud Shell guide and script are packaged; no
real Firestore call, billing change, or Vercel deployment occurred. Vercel
deployment query for that exact branch returned zero results after the branch
config disabled auto-deploy. GitHub CI was still in progress when checked.

Use the branch's `docs/FIRESTORE-CLOUD-SMOKE.md` on mobile Cloud Shell for the
prepared one-command run. It requires an existing dedicated non-production
Firestore project/database and `roles/datastore.user`; it does not provision a
project/database. The guide installs official Node 24 in `/tmp`, checks the
active `gcloud` project, and gives an exact-run-ID cleanup command for an
interrupted smoke. NAS ADC and production Vercel OIDC remain separate.
