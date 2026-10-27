# Vercel per-deployment Firestore Preview attempt — 2026-10-27

## Existing approach (previous turn)

The earlier approach attempted branch-specific Vercel project Preview environment variables through the Vercel environment API. Vercel returned HTTP 400 `BAD_REQUEST`: project `hunghvt-notes` has no connected Git repository. The request created no variables; a later branch filter returned an empty list. No deployment was started.

## New approach requested

Candidate source remains the verified Notes commit `082824c51f305a9c94ecdea6aafb9a479a4ccf5e`, project `hunghvt-notes` (`prj_c4sEp6nB4msWTsPiGoALSuVutVTK`), GCP project `notes-lab-56f0f`. WIF provider/subject and IAM were left unchanged.

Checked current official CLI help from a one-off npm CLI installation: Vercel CLI `65.4.0` supports runtime `--env KEY=VALUE` and explicit `--environment preview`. However, supplying the secret as `--env KEY=VALUE` places it in the CLI process argv, contrary to the request's no-secret-in-arguments rule. No secret was supplied to CLI or shell.

Checked CLI auth without printing identity data: `vercel whoami --format json --non-interactive` reported `loggedIn: false`, `linkedProject: null`. A harmless dry-run using only a dummy local config, explicit project ID/team, and `--environment preview` failed before file inspection with:
`You do not have access to the specified account`
`https://err.sh/vercel/scope-not-accessible`
No deployment was created.

Checked current Vercel REST API v13 Create Deployment schema. It supports deployment source/files, target and project settings, but documents no per-deployment runtime `env` field. The authenticated Vercel MCP deployment tool has the same limitation. Thus we did not send secret material through an undocumented field or embed it in uploaded source.

## Result and minimum unblock

This request is blocked by absent local Vercel CLI authentication/team access, not by Git linkage. Minimum required action: authenticate the local Vercel CLI for an account with access to team `hunghvt` (device/browser login); do not link Git or change project settings. After that, a deployment-only config can be tested without putting values into shell argv, but it must first be confirmed that the current CLI supports that path and that values are not emitted in logs or source upload. If not, stop rather than using `--env` with secrets in argv or creating shared project Preview variables.

The exact WIF Preview subject was not weakened. No project environment variable, Production setting, alias, deployment, billing setting, or real Notes data was changed.

Official references:
- CLI deploy options, `--env` and target: https://vercel.com/docs/cli/deploy
- CLI deployment target default/Preview: https://vercel.com/docs/deployments/environments
- REST API v13 Create Deployment schema: https://vercel.com/docs/rest-api/deployments/create-a-new-deployment
- Local configuration option: https://vercel.com/docs/cli/global-options
