# Notes Production cutover to Firestore — 2026-10-27

This report supersedes the earlier package status that said Koofr was still
serving Production. Cutover was authorized in the user session and completed
without changing the project-wide Production environment, enabling billing,
creating a service-account key, linking Git to Vercel, or deleting Koofr data.

## Final routing

- Application URL: <https://hunghvt-notes.vercel.app>
- Vercel team/project: `hunghvt` / `hunghvt-notes`
- Active Production deployment: `dpl_SrEHLu6jv6tjTUEPR7F25sxdsFZ1`
- Notes source branch: `codex/notes-production-cutover-20261027`
- GitHub branch head: `97c84e74d2e21ceb3a72b36dd16e6d9505a8e742`
- Deployed source tree: `ab169c6bd440f228a3f521fc4357b7bddf2eadec`
- Original candidate `7fccf15e11896f1f397f1d893fa2a8dab0876b0a` is in the
  branch ancestry. Vercel remains a direct deployment; no Git auto-deploy was
  linked. Deployment-specific runtime overrides select the Firestore backend.
- GCP target: project `notes-lab-56f0f`, database `(default)`, vault
  `notes-production`. Existing Notes namespace, Homepage auth configuration,
  session cookie name/password, public interface, and domain were retained.

The exact primary alias was assigned to the Firestore deployment after the
frozen Firestore deployment had passed health/config checks. The other alias,
`hunghvt-notes-hunghvt.vercel.app`, was left on its previous deployment.
Temporary exporter and smoke deployments were removed. The export API is absent
from the active build; rollback support remains in source and is disabled by
default in the live deployment.

## IAM and WIF preflight

Read-only IAM inspection immediately before switching showed:

- Preview WIF pool `vercel-notes-preview` is disabled. Its provider still has
  only the exact Preview subject condition, but a disabled pool cannot issue
  tokens. Preview service account is enabled but has no IAM bindings; the
  project policy has no Preview principal binding. Earlier real requests from
  the old Preview identity returned denied after propagation.
- Production WIF pool/provider are active and their condition is exactly
  `owner:hunghvt:project:hunghvt-notes:environment:production`.
- Production service account is enabled. Its Workload Identity User binding is
  the exact Production subject principal. Its project-level Firestore grant is
  limited by IAM condition to
  `resource.name == "projects/notes-lab-56f0f/databases/(default)"`.
- No static service-account JSON key was created. No billing change was made.

The live Firestore smoke authenticated through the Vercel Production OIDC → STS
path with this Production identity. It used only a generated synthetic vault.

## Source export and parity

All app writes (owner, share, and Code Inbox) were frozen before the final
GET-only Koofr export. No purge was run. The source snapshot is private outside
Git under `/home/admin/.local/state/notes-migration`, mode `0600` in a `0700`
directory; it and the older snapshot remain intact.

Final Koofr snapshot `koofr-production-final-20261027-1811.json.gz`:

- Raw snapshot: 1,852,349 bytes; gzip: 413,459 bytes.
- Gzip SHA-256: `ee5fa400d6e4e91d3dc900ebf07f2111271eab2bd82d97b77a41bfaafc04936e`.
- Stable source catalog SHA-256: `e9c5db628b65300ca858ed200b472f47dd3a939472120186e75dada5af81936c`.
- Validated counts: 28 notes (6 active, 22 trash), 2 folders, 11 shares (0
  active), 24 receipts, 0 erased tombstones.
- Full snapshot fingerprint:
  `63ae5286e861ee8684d86f6b3db55f354b2e43e60f096508d10797e6f8218c6f`.

The destination vault was checked empty immediately before import. Import
reported `match=true`. A second private snapshot exported from the real
Production Firestore vault after cutover also validated and compared equal to
the source (`match=true`, same counts and fingerprint). Its size is 1,853,427
bytes. This verifies note bodies, histories, revisions, folder/order, trash,
share/token-box records, receipts and tombstones as represented by the migration
comparator. No snapshot contents are included here.

The private post-cutover snapshot is
`firestore-production-postcutover-20261027.json`; the pre-cutover Firestore
copy remains `firestore-production-precutover-20261027.json`. Both are mode
`0600`. Koofr remains unchanged and available for rollback.

## Runtime checks and evidence limits

An SSO-protected Production-target deployment without an alias used the exact
Production WIF configuration and a unique `notes-cutover-smoke-<UUID>` vault.
The in-runtime smoke passed all 13 checks: synthetic login, list/open, save,
idempotent replay, stale-revision CAS conflict, folder creation, order update,
share/read/revoke, trash/restore, and Code Inbox envelope/storage handling.
The synthetic vault was recursively deleted and independently checked absent.
That smoke deployment used a synthetic local-password provider and a
test-only Code Inbox authorizer. It exercised real Production WIF/STS/Firestore
and application/storage code; it did **not** impersonate the owner's Homepage
password or mint a GitHub Actions OIDC assertion.

After alias switch, the live URL returned health `configured=true`,
`production=true`; an unauthenticated owner save and share returned
`LOGIN_REQUIRED`, and an unauthenticated Inbox request returned
`INBOX_UNAUTHORIZED` (rather than a freeze response). These probes made no note
or Inbox writes. A successful owner login in the user's browser was not
observable from this session because its existing cookie/password is not
available to Codex. The Homepage auth configuration, key, session password,
namespace and cookie contract were left in place. The full offline suite on the
exact final Notes tree passed 176/176.

The temporary GET-only Koofr exporter and synthetic smoke routes were removed
from the final source before deployment. The staged exporter deployment was
deleted after the final export. No production app request wrote to Koofr after
the alias switch; app and Inbox storage dispatch to the Firestore backend.
Remaining Koofr workflows are limited to exact synthetic test namespaces or
read-only inventory and do not target the live Notes namespace.

## Freeze duration and rollback

The live write freeze began at approximately `2026-10-27 18:09:24.943 +0700`.
The first recorded canonical-domain responses on the final deployment were at
`18:33:40.907 +0700`; an unauthenticated save reached the normal login gate by
`18:33:48.221 +0700`. The measured write outage was therefore about 24 minutes
(less than 24m24s; exact alias-update timestamp is not exposed by Vercel alias
listing). Local drafts were not cleared, and no user Notes were purged.

If rollback is needed after new Firestore edits exist: freeze the Firestore
deployment first and allow in-flight requests to drain; export the **current**
Firestore state; invoke the gated `restore-current-firestore-to-original-koofr`
rollback with the preserved original namespace and the source baseline catalog
hash above; verify full snapshot parity in Koofr; then point the exact primary
alias to a Koofr-backend deployment and reopen writes. Do not switch to the old
pre-cutover Koofr snapshot. The fixture rollback test verified that a
post-cutover edit and share token-box are carried back, while a stale baseline
is rejected. The rollback endpoint is not enabled on the live deployment.

## Repository state

Candidate cutover source was built from a clean isolated worktree on `/vol1`.
The dirty `/home/admin/Hunghvt-notes` checkout was left untouched. `ai-nas-lab`
local `main` also had pre-existing changes; this report was prepared on a new
branch based on `675680844da62d3c9428595713c1d1859b917551`, without copying or
resetting those changes.
