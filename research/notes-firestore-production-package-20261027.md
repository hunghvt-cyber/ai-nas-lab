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
