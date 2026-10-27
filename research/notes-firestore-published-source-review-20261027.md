# Blocking review: published Firestore source corruption — 27/10/2026

Scope: independent source review of Hunghvt-notes commit 6dc6d183ac53bc80d7b01987dc72ac5cef9be956. No NAS access, production writes, migration or deployment.

## P0: published module is not valid JavaScript
File: lib/firestore-native-repository.mjs
Published Git blob: afad35cbdfccd23e26e7a7a6f2feb3e89b6ef4c8

The first two actual file lines are:
    Warning: truncated output (original token count: 11878)
    Total output lines: 563

Actual file line 298 contains:
    const…1878 tokens truncated…ning',createdAt:this.now()});

These markers are not just presentation truncation. A separate GitHub fetch of lines 1–15 and 285–315 returns the same markers. Writing the received file locally and running git hash-object reproduces the published blob exactly:
    afad35cbdfccd23e26e7a7a6f2feb3e89b6ef4c8

Node v24.22.1 syntax check fails at line 1:
    SyntaxError: Unexpected identifier 'output'

Even removing the first three lines is insufficient: the middle section is missing, including method code. Do not synthesize replacements from the clipped text.

Parent commit 4ef6be251dde9692f18b0b0f7364b7acebc5d5d4 has a different blob, 5df460ce35058139c523f6404e79699a6073d980; its first 12 lines do not contain the warning. This is only a possible recovery source, not a full validation of the parent.

## Consequence
The current GitHub source cannot be the same executable module as the reported successful 170 tests/cloud smoke. This does not disprove the NAS smoke; it means the reported test evidence is not yet bound to this published artifact. Do not deploy this commit or reuse its test counts to approve it.

## Required repair and verification
1. On NAS, preserve work and compare the module used for PASS with git show HEAD:path and remote Git blob.
2. Recover the complete module from the tested local file or a verified complete parent, then apply the two real-smoke fixes. Do not merely delete warning lines.
3. Scan tracked sources for embedded output truncation markers.
4. Run syntax check and offline test suite from a fresh checkout of the actual candidate commit, with Node 24 and no Koofr/provider credentials.
5. Repeat only necessary isolated Firestore smoke after code repair, using the candidate checkout, and bind report to its commit/blob hashes.
6. Push and independently verify remote HEAD/module bytes against those tested. Correct review-ready status and stale documentation.
7. Resume Vercel WIF/migration preparation only after artifact integrity is restored.

## Performance evidence already documented
docs/FIRESTORE-NATIVE.md records one real NAS run: save ~0.38s, owner open ~0.40s. These are useful single-run observations, not p50/p95 or Vercel/browser timings. Do not treat functionality PASS as proof of Google Keep-equivalent latency.

## Repair and artifact-bound verification — 27/10/2026

The finding was valid. In addition to the repository module, the published
`package-lock.json` was also corrupted by captured output, which made `npm ci`
fail on a clean checkout. Neither file was repaired by deleting marker lines.

Recovered the complete source from the local file used for the successful smoke,
including the two real-smoke fixes. Restored the complete lockfile from the
verified local tree. The repaired remote candidate is
[`082824c`](https://github.com/hunghvt-cyber/Hunghvt-notes/commit/082824c51f305a9c94ecdea6aafb9a479a4ccf5e)
on the same isolated branch. Its tree equals the tested local candidate tree.

Verification was run from a fresh detached checkout of that exact commit using
Node 24.22.1: `npm ci` installed 143 packages, `node --check
lib/firestore-native-repository.mjs` passed, the truncation-marker scan found no
matches in 124 tracked code/docs/config files (excluding the Inbox data file),
and `npm test` passed 170/170. The isolated real Firestore smoke then returned
`PASS` for all 11 checks on `notes-lab-56f0f` / `(default)`; a separate read
confirmed its two synthetic roots were deleted.

Integrity is bound to Git objects: the exact commit references module blob
`3454137816de08aaf9e7ab302c37b4f9ae1d9aea` and lockfile blob
`8c4e1c62ffba93eb05f2b1bf1eecbdfd0a848892`. Both hashes match the clean tested
checkout and were independently fetched from GitHub. Remote branch HEAD is the
candidate commit above. WIF, deployment and migration remain paused until this
review is accepted; Koofr production remains unchanged.

## Independent recheck and closure — 27/10/2026

ChatGPT independently fetched the full repaired module in bounded line ranges from commit 082824c51f305a9c94ecdea6aafb9a479a4ccf5e, reconstructed its bytes and obtained git hash-object 3454137816de08aaf9e7ab302c37b4f9ae1d9aea, identical to the published module blob. Node v24.22.1 node --check passed on those bytes. GitHub also returns lockfile blob 8c4e1c62ffba93eb05f2b1bf1eecbdfd0a848892, matching the NAS report. The 170-test and repeated real-smoke results remain NAS-reported evidence; ChatGPT did not rerun them or access NAS. The specific published-source-corruption blocker is resolved for this candidate. This is not a complete security review or production rollout approval; Vercel identity/integration and migration remain pending.
