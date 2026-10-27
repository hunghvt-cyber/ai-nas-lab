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
