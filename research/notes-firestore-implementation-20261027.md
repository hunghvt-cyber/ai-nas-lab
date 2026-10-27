# Notes native Firestore implementation handoff — 27/10/2026

## State

The user-provided test project is `notes-lab-56f0f`. This work prepared and
pushed the native Firestore integration to the isolated Hunghvt-notes branch
[`codex/notes-firestore-cloudshell-20261027`](https://github.com/hunghvt-cyber/Hunghvt-notes/tree/codex/notes-firestore-cloudshell-20261027),
commit [`4ef6be2`](https://github.com/hunghvt-cyber/Hunghvt-notes/commit/4ef6be251dde9692f18b0b0f7364b7acebc5d5d4).
The `release/minimal-notes` branch and Vercel deployments were not changed.
Koofr remains the selected production backend.

The native repository and runtime factory are now connected to the existing
Notes API and Code Inbox store interfaces behind explicit
`NOTES_BACKEND=firestore-native-v1` selection. Production also requires the
separate `NOTES_FIRESTORE_PRODUCTION_REVIEW=approved-v1` gate. No deployment or
production setting has been changed.

Native documents cover notes/current revision, immutable version history and
content chunks, folders/order, share capability records and revocation guards,
Code Inbox authorization, trash/purge tombstones, operation receipts, and
resumable folder deletion. Save uses per-note compare-and-swap and idempotency;
independent notes do not share a global write lock. Backup/restore verifies
counts and content hashes, and restore preserves revisions/history/shares/
receipts/tombstones. Migration tooling supports dry-run verification, isolated
import/export and rollback to a fresh Koofr namespace; it does not write the
active Koofr namespace. The current Koofr snapshot endpoint has a 2 MiB cap, so
production datasets above that size need a streaming source-export path before
they can be migrated safely. No Notes data was read to estimate size.

The previous Koofr compatibility adapter remains available for parity tests;
it is not the native design because it holds a whole-vault lock. Existing UI,
session/cache identity, draft/CAS API semantics, capability links and Code Inbox
request contract remain in their existing layers. Owner/share draft behavior,
revision fencing, and auth checks are retained in the repository contract.

## Evidence and remaining proof

- Initial full offline suite on Node 24: 169 passed, 0 failed. `npm test` uses fixture
  and in-memory fake implementations; this does **not** establish real
  Firestore transaction, IAM, latency, or billing behavior.
- Gemini reviewed one filtered architecture/race summary via `/home/admin/bin/gemini-task`.
  No note content, credentials, or private logs were sent. Its share/folder/
  purge concerns were checked against transaction guards and resume behavior.
  Its reference to a 500-write transaction ceiling was stale; current official
  release notes document removal of that old limit.
- The initial report preceded authorization. The user later completed the
  isolated NAS ADC sign-in, and the final direct NAS smoke is recorded below.
  No migration, billing action, production read/write or deployment occurred.

## Smallest next step: authorize the NAS smoke once

The NAS did not have Google Cloud CLI or ADC. A private Linux ARM64 Google Cloud
CLI 590.0.1 was installed at `/home/admin/.local/opt/notes-google-cloud-cli`;
its archive checksum matched Google's official value. The wrapper
`/home/admin/bin/notes-gcloud` sets an isolated Cloud SDK config under
`/home/admin/.local/state/notes-gcloud-home/.config/gcloud`. No credentials from
Gemini or another application were accessed. The isolated ADC file is absent.

The user completed this single authorization step for the NAS account with
`roles/datastore.user` on `notes-lab-56f0f`:

```sh
/home/admin/bin/notes-gcloud auth application-default login --no-launch-browser --disable-quota-project
```

It used user ADC only for the NAS smoke, did not set a quota project or enable
billing, and is separate from Vercel production OIDC. No credential value was
read or printed by Codex.

The smoke was fixed to project `notes-lab-56f0f`. It created two random,
synthetic `notesVaults/{vaultId}` roots, verifies init/save/open/CAS/share/revoke,
folder delete, trash/restore/purge, and snapshot count/hash restore, then removes
only those two roots. It does not create a project/database or enable billing.
The runner returned `PASS` on 2026-10-27 using Node 24 and the `(default)`
database. It verified both roots were absent afterward. Observed single-run
timings: initialize 1.35s, save 0.38s, owner open 0.40s, folder delete 0.95s,
trash/restore 1.06s, snapshot restore 2.02s, purge 2.06s. These are end-to-end
NAS observations, not a performance benchmark.

Two defects surfaced only in this real smoke and were fixed: creating a note in
a previously unseen folder used a timestamp before initialization; snapshot
capture incorrectly treated a completed deleted-folder tombstone as an active
deletion. Regression tests now cover both. The final full offline Node 24 suite
passes 170/170. Changes are being pushed to the same isolated branch; no
production release or real Notes data has been touched.

The native integration and migration/rollback tooling are review-ready, not
activated. Production still requires reviewed Vercel GCP Workload Identity
Federation configuration and IAM. The current Koofr snapshot endpoint is capped
at 2 MiB; if the real Notes snapshot is larger, a streaming Koofr export is a
pre-migration requirement. No production data size was read.

## Official references consulted

- [Google Cloud CLI Linux Arm installation and checksum](https://docs.cloud.google.com/sdk/docs/install-sdk)
- [Application Default Credentials for local development](https://docs.cloud.google.com/docs/authentication/set-up-adc-local-dev-environment)
- [ADC login using a browser on another device](https://docs.cloud.google.com/sdk/gcloud/reference/auth/application-default/login)
- [Firestore IAM roles](https://docs.cloud.google.com/firestore/docs/security/iam)
- [Firestore quotas](https://docs.cloud.google.com/firestore/quotas)
- [Firestore release notes](https://docs.cloud.google.com/firestore/docs/release-notes)
- [Vercel OIDC with Google Cloud](https://vercel.com/docs/oidc/gcp)

See Hunghvt-notes `docs/FIRESTORE-NATIVE.md` and
`docs/FIRESTORE-CLOUD-SMOKE.md` for schema, request-count model, migration and
rollback details. These notes distinguish local fixture evidence from future
real-cloud proof.
