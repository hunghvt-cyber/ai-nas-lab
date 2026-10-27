# Direct Vercel Preview → Firestore result — 2026-10-27

## Previous method vs. new method

**Previous attempt:** branch-scoped project Preview env creation through Vercel env API returned HTTP 400 because `hunghvt-notes` has no Git repository connection. It created no variables. A readback confirmed no Preview envs.

**New method:** authenticated Vercel CLI 65.4.0 deployed the exact clean checkout `082824c51f305a9c94ecdea6aafb9a479a4ccf5e` directly to project `prj_c4sEp6nB4msWTsPiGoALSuVutVTK` / team `hunghvt`. No Git linking was done. The deployment command explicitly used `--environment preview` and `--project` by ID; no production flag, promote or alias was used.

CLI `--help` supports `--env KEY=VALUE`, but that would put secrets in argv. Instead, a 0600 configuration file outside the checkout was passed through supported `--local-config`; its `env` object supplied runtime values to this deployment only. A dummy dry-run confirmed its marker was absent from deployment source/file output. Actual CLI stdout/stderr was captured in memory and scanned against generated secret values before emitting the result. Temporary config, auth payload and cookie jar used mode 0600 and were removed. No secret was committed or printed.

## Actual deployment and runtime

- URL: https://hunghvt-notes-7akbwqjy0-hunghvt.vercel.app
- Deployment: `dpl_H1L38KavsPzE4CbYnpSetZUGnW38`, READY; Vercel metadata has `target: null` (Preview) and empty aliases.
- Exact project/team IDs match. Project has Git connection disabled/absent; direct deployment did not change it.
- Vercel deployment claims independently read back as:
  - issuer `https://oidc.vercel.com/hunghvt`
  - audience `https://vercel.com/hunghvt`
  - subject `owner:hunghvt:project:hunghvt-notes:environment:preview`
  - environment `preview`, project `hunghvt-notes`
- This matches the existing exact WIF condition. No IAM/WIF change was made.
- Vercel CLI requests to the live app passed health config, Notes password authentication, Firestore note create/read, soft delete to trash, and purge. All HTTP operations returned 200. This exercises the actual Vercel OIDC → STS/service-account impersonation → Firestore path.
- Firestore readback in the isolated `preview-notes-firestore` vault found 0 active, 0 trash, and 1 purged synthetic note metadata record; note content is removed. No user Notes data was involved.
- The initial OIDC/health deployment and an intermediate authentication-harness deployment were deleted. Only the successful Preview deployment remains.

No Preview project env was created; branch-filtered environment list is still empty. Existing project values remain Production-only. No billing, production deployment, alias, data migration or production configuration changed.

## What this verifies and limits

Verified: direct no-Git Preview deployment from the exact tested commit, one-deployment runtime config, exact OIDC claims, Notes login, actual Firestore operations, synthetic cleanup, no secret output, and no project env mutation.

Not verified: production WIF identity, production project IAM/billing/quotas, large Koofr snapshot export, migration/cutover, or rollback execution on real data. Koofr remains the active production backend.

## Evidence references

- CLI runtime env and deployment target: https://vercel.com/docs/cli/deploy
- CLI local config option: https://vercel.com/docs/cli/global-options
- Runtime env in Vercel configuration: https://vercel.com/docs/project-configuration/vercel-json
- Vercel GCP OIDC: https://vercel.com/docs/oidc/gcp
