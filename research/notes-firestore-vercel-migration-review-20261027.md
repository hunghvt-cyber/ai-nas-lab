# Vercel → Firestore preparation review — 2026-10-27

## Result

The candidate Notes source is still `codex/notes-firestore-cloudshell-20261027` at `082824c51f305a9c94ecdea6aafb9a479a4ccf5e`. Its clean-checkout evidence remains: Node 24 syntax check, 170/170 tests and isolated Firestore smoke passed; synthetic smoke vaults were removed.

A test-only WIF setup is prepared in GCP project `notes-lab-56f0f`:
- pool/provider: `vercel-notes-preview/notes-preview`
- issuer `https://oidc.vercel.com/hunghvt`, audience `https://vercel.com/hunghvt`
- exact subject condition `owner:hunghvt:project:hunghvt-notes:environment:preview`
- service account has `roles/datastore.user` only in the test project and `roles/iam.workloadIdentityUser` for the exact Preview subject
- no static key was created; metadata check: 0 user-managed keys, 1 Google-managed system key.
IAM/API/provider readbacks passed. This is not yet a Vercel token exchange test.

## Blocking step

Branch-scoped Preview env creation returned Vercel HTTP 400: project `hunghvt-notes` has no connected Git repository. No Preview or Production environment variables were created. The one required owner action is to reconnect the Vercel project to `hunghvt-cyber/Hunghvt-notes`; then Codex can set variables only for branch `codex/notes-firestore-cloudshell-20261027`, deploy, and verify the actual OIDC exchange. Do not add unscoped variables or broaden the WIF condition.

## Migration and rollback

The Notes review artifact is in `docs/FIRESTORE-VERCEL-MIGRATION-REVIEW.md` on the candidate branch. It records the preview configuration, gates, test steps, cutover preflight and rollback based on a write freeze plus a fresh full-current Firestore export restored into a new Koofr namespace. Thus edits after cutover are carried forward rather than lost by reverting to the old root. It also documents draft handling and the namespace-bound owner token-box limitation; no raw share token is exported.

A verified source limit is 2,000,000 bytes: Koofr export currently stops with `SNAPSHOT_TOO_LARGE`. No real Notes snapshot size was read. If the limit is hit, migration must stop before import; current code has no streaming Koofr exporter. A reviewed bounded streaming export/restore path is required above this size. Koofr remains production.

## Gemini review

Gemini agreed with branch isolation, testing an actual STS exchange, treating 2 MB as a hard preflight and exporting current Firestore state after freezing writes for rollback. It proposed broadening the exact subject, using unscoped variables plus a runtime guard, and atomically changing a Firestore namespace pointer. I rejected those: Vercel's official guide supports the chosen issuer/audience/subject pattern; unscoped credentials are not an acceptable workaround; Notes selects backend/namespace through Vercel config, not a Firestore pointer.

## Evidence and remaining gates

Measured: candidate tests/smoke; GCP IAM/WIF readbacks; Vercel's branch-env rejection; no production changes. Not verified: Vercel-issued OIDC, deployed Preview runtime, production project IAM/billing/quota, real Koofr snapshot size, production migration. No billing was enabled.

Detailed review: `Hunghvt-notes/docs/FIRESTORE-VERCEL-MIGRATION-REVIEW.md`.
