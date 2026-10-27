# Notes Firestore Production package — 2026-10-27

## Result

No Production backend/configuration changed. Koofr remains the source of truth;
no real Koofr read/write, no billing change, and no Production deploy occurred.

## Verified state

- Vercel CLI 65.4.0 authenticated as team `hunghvt`; explicit project inspect
  matched `hunghvt-notes` / `prj_c4sEp6nB4msWTsPiGoALSuVutVTK`, Node 24.x.
- Preview candidate `dpl_H1L38KavsPzE4CbYnpSetZUGnW38` is READY and has Preview
  target, no aliases; direct deploy did not require Git link. Synthetic Notes
  flow and Vercel OIDC → STS → Firestore passed. This is Preview-only evidence.
- Isolated NAS ADC token successfully listed `notes-lab-56f0f/(default)`. The
  real synthetic Firestore smoke passed. GCP Resource Manager lists only one
  Notes-named project available to the signed-in account: `notes-lab-56f0f`
  (Notes Lab), explicitly the test project. Its only database is `(default)`.
- Preview service account `notes-preview-firestore@notes-lab-56f0f.iam.gserviceaccount.com`
  currently has unconditional project-level `roles/datastore.user`; no
  Production data may be placed in this test project or shared with this
  identity.
- No separate Production GCP project is discoverable. Production WIF/SA are not
  created. Preview role was not mutated; no IAM grant was widened.

## Koofr snapshot access blocker

Vercel Production has six Secret values which the CLI identifies as not
retrievable. `vercel env run` is documented to inject environment into a child,
but this CLI cannot pull those Secret values locally. A failed command was
misparsed as a project-creation flow; the empty `notes-migration-runner` project
was verified to have zero env variables/deployments and deleted immediately.
Its local `.vercel` link and `.gitignore` were removed. Do not retry `env run`.
No secret or value appeared in output.

The real source snapshot byte size, counts, and hash remain unknown. The Notes
candidate adds `scripts/koofr-readonly-snapshot.mjs`, which can run where the
existing dedicated Notes WebDAV env is available. It performs GET-only catalog
and immutable-record reads, validates every record hash/ID, rechecks the catalog
after reads, and writes a 0600 snapshot beneath a 0700 directory. It bypasses the
2 MB app-backup endpoint and supports the migration CLI's 50 MB input ceiling.
If the actual snapshot is >50 MB, importer expansion is a gate. This exporter
has not touched Koofr.

## Migration identity and namespace

Production subject must be exactly
`owner:hunghvt:project:hunghvt-notes:environment:production`, issuer
`https://oidc.vercel.com/hunghvt`, audience `https://vercel.com/hunghvt`.
Use a separate WIF pool/provider and a dedicated SA in the selected dedicated
Production project. Grant Production SA Firestore access only there; Preview SA
remains in the test project. This relies on the official Vercel GCP OIDC subject
format and Google Workload Identity Federation.

Keep Production `NOTES_DATA_NAMESPACE`, `NOTES_SESSION_PASSWORD`, `NOTES_BASE_URL`,
Homepage auth settings, browser/API contract and UI untouched. Import preserves
catalog epoch, IDs/revisions/history, order/folders, shares/tokenHash/tokenBox,
receipts, trash and purge tombstones. A new same-namespace rollback helper
checks the exact pre-cutover Koofr catalog hash/epoch, uploads missing immutable
records under the root lock, then publishes the current Firestore catalog. It
keeps namespace-bound token-box/share URLs and post-switch edits, and fails
closed if Koofr was independently changed. It does not delete Koofr data.
Fixtures verify read-only export and post-cutover rollback (Node 24 targeted suite: 38/38); the project-selecting migration CLI also requires the explicit project to match both `GOOGLE_CLOUD_PROJECT` and `NOTES_MIGRATION_PROJECT_ID`. No real Koofr rollback occurred.

## Cutover package

1. Select a dedicated existing Production GCP project. Check IAM mutation rights
   there; create an exact-subject Production WIF provider and dedicated SA. No
   billing changes.
2. Obtain an approved read-only snapshot execution path within Vercel Production
   runtime; do not send Secrets in chat. Export and record bytes/hash/counts.
3. Validate snapshot; dry-run/import to the Production Firestore destination;
   compare full counts/hash; verify independent Firestore backup/restore.
4. Final approved cutover: brief write freeze; fresh final snapshot/import/hash
   compare; Production deploy with only Firestore config changed; verify owner,
   share, trash/restore, Code Inbox and CAS; then re-enable writes.
5. Rollback: freeze, export current Firestore state, restore into the original
   Koofr namespace using recorded baseline hash, compare full snapshot, switch
   backend to Koofr without changing namespace/session/auth, verify, then reopen
   writes. Retain both stores; no automatic deletion.

Write downtime is not responsibly estimable until real source count/size is
known. Measure snapshot/import/verify after the private export. The prior small
synthetic smoke is not a production duration estimate.

## Minimal support still needed

1. Identify an already authorized dedicated Production GCP project; `notes-lab-56f0f`
   is test-only and cannot be repurposed.
2. Approve a read-only Production-runtime export path, since Vercel Secrets are
   write-only to CLI. No credentials or snapshot body should be pasted into chat.

Official sources: [Vercel GCP OIDC](https://vercel.com/docs/oidc/gcp),
[Google WIF](https://docs.cloud.google.com/iam/docs/workload-identity-federation),
[Firestore IAM conditions](https://docs.cloud.google.com/firestore/native/docs/manage-databases),
[Vercel env CLI](https://vercel.com/docs/cli/env).

## Verified follow-up — 2026-10-27

This follow-up supersedes the outdated “dedicated project still needed”,
“Preview identity still authorized”, and “no real snapshot” statements above.
The owner's decision is to reuse `notes-lab-56f0f`, database `(default)`, for
Notes after revoking Preview access. No extra project or billing was created.

### IAM and runtime identity

- Removed Preview SA's project `roles/datastore.user` grant and its exact
  Preview `roles/iam.workloadIdentityUser` binding; disabled pool
  `vercel-notes-preview`. A real request from the old Preview runtime identity
  was denied twice after propagation. Direct/project and service-account
  bindings were checked; no inherited matching grant was found.
- Created separate SA `notes-production-firestore` and pool/provider
  `vercel-notes-production`. Issuer is `https://oidc.vercel.com/hunghvt`,
  audience `https://vercel.com/hunghvt`, with exact subject
  `owner:hunghvt:project:hunghvt-notes:environment:production`. The only
  production impersonation binding is that subject. Firestore data access is
  conditioned on database `(default)` in `notes-lab-56f0f`. No user-managed
  service-account keys or billing changes.
- A staged Production Vercel runtime completed a real Firestore read of a
  synthetic absent probe document through OIDC → STS → Firestore. It wrote no
  Notes data.

### Read-only Koofr snapshot

A temporary exporter was run on a staged Production deployment behind the
project's Vercel SSO protection. Unauthenticated access returned 302; the
authenticated health check reported `koofr-v1`; POST returned 405. The
temporary handler had only protected health/identity/GET manifest, record and
final-stability actions, with no write route or background job. It used the
existing Production runtime Secrets without reading them back. The exporter
verified IDs and immutable record hashes and compared the same catalog hash
before and after all GET requests.

The private snapshot is outside both repositories at
`/home/admin/.local/state/notes-migration/koofr-production-20261027.json.gz`;
directory mode is 0700 and file mode 0600. Raw JSON size 1,829,423 bytes;
gzip size 404,736 bytes; one successful pass, 32 HTTP requests; raw snapshot
SHA-256 `79d97641b8562f65d0c9c55d4aaf60b861da96483de2d5f0c9756f63775b7c38`,
gzip file SHA-256
`3dd8ec69231dfc3afb8ca0e515958d2c7107fe61fe56a126bb62ff17692bdf7a`.
The migration verifier returned VALID with 28 Notes (6 active, 22 trash), 2
folders, 11 share records, 24 receipts, 0 erased-ID tombstones, fingerprint
`5d652b5743f3d79735a1df1f917ff378649a89a767e80073934a9e78192235b5`. No note
content is recorded here. Snapshot is below the migration CLI's 50 MB limit.

The exporter route/helper, one-time client and all three staged Production
deployments were removed after validation. The two pre-existing Production
aliases still resolve to their original deployment IDs; no production domain
or alias was changed.

### Migration/rollback package and remaining boundary

Notes candidate now supports `.json.gz` input to verify/import/rollback with a
50 MB expanded-size cap. Native Firestore export supports an explicit 50 MB
limit for rollback, while the normal app backup keeps its existing 2 MB limit.
The fresh final Koofr snapshot and import/parity check remain required after an
approved write freeze. Rollback must export the *current* Firestore snapshot,
then restore it into the original Koofr namespace against the recorded
pre-cutover catalog hash and epoch; this carries every post-cutover edit,
revisions, links/token-box, receipts, trash and tombstones. The helper fails
closed if the Koofr catalog changed outside the freeze.

No Firestore Notes import, production backend change, write freeze, billing
action, or Koofr mutation has occurred. Koofr remains live Production. The
cutover duration is still unmeasured; assess from the final snapshot size and a
pre-import dry run rather than claiming a number now. Next action is a concrete
cutover plan for review, not further project setup.

### Final cutover update — 27/10/2026

The pending cutover was completed after this package was written. The prior
snapshot-size, Koofr-production and no-import statements are historical. Read
the final snapshot, parity, IAM, runtime and rollback evidence in
[notes-firestore-production-cutover-20261027.md](notes-firestore-production-cutover-20261027.md).
