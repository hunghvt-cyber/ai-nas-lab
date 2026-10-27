# Notes speed research results — 2026-10-27

## Scope and source checkpoint

Read the AI NAS Lab handoff (`AGENTS.md`, `CURRENT-STATE.md`, `RUNBOOK.md`, and the two requested research inputs) and the NAS handoff guidance before using `gemini-task`. No Notes data, runtime logs, credential, or secret was read or sent. No live Notes API, production Koofr content, deployment, migration, or service was touched.

Source checked: `hunghvt-cyber/Hunghvt-notes`, branch `release/minimal-notes`, commit `ee5d75f5795bf2ce79971c7a3dfe772119ad6d1a` (2026-10-27 10:30 +07). The read/auth/transport source files are the same as the documented 2026-10-26 deployment commit `0c8c0761c2625ae2be747e448a7259f974dccb34`; only two unrelated save/delete guards in `lib/store.mjs` differ. This is a source-to-documented-checkpoint comparison, **not** a live Vercel deployment check: Vercel CLI/project linkage was unavailable in this environment. The October 20 `docs/RELEASE.md` checkpoint is older; the October 26 shared-auth note is the later source checkpoint.

Key source: [`lib/store.mjs`](https://github.com/hunghvt-cyber/Hunghvt-notes/blob/ee5d75f5795bf2ce79971c7a3dfe772119ad6d1a/lib/store.mjs), [`lib/storage.mjs`](https://github.com/hunghvt-cyber/Hunghvt-notes/blob/ee5d75f5795bf2ce79971c7a3dfe772119ad6d1a/lib/storage.mjs), [`lib/shared-auth.mjs`](https://github.com/hunghvt-cyber/Hunghvt-notes/blob/ee5d75f5795bf2ce79971c7a3dfe772119ad6d1a/lib/shared-auth.mjs), [`lib/preview-api.mjs`](https://github.com/hunghvt-cyber/Hunghvt-notes/blob/ee5d75f5795bf2ce79971c7a3dfe772119ad6d1a/lib/preview-api.mjs), and [`public/app.js`](https://github.com/hunghvt-cyber/Hunghvt-notes/blob/ee5d75f5795bf2ce79971c7a3dfe772119ad6d1a/public/app.js).

## Findings: code facts, measured evidence, and unknowns

### Code facts

- A cold owner note open goes through the owner API authorization and then `NoteStore.readContent`: snapshot under root LOCK (LOCK, catalog GET, UNLOCK), immutable record GET and hash/identity validation, then a second root-LOCK snapshot (LOCK, catalog GET, UNLOCK) to validate current state. That is **7 sequential WebDAV calls** on a stable head. If the head moves, the whole sequence is retried once. A known revision uses one snapshot: **3 WebDAV calls**.
- The owner UI's full-content cache is a JavaScript session-memory map. A matching warm entry paints the editor immediately and then revalidates with the server; a cold open waits for the API response before filling the editor. IndexedDB persists list previews and drafts, not opened full-note content. Shared links do not use the owner content cache.
- With `NOTES_AUTH_MODE=homepage-v1`, every owner API request checks `passwordProvider.current()` before the Notes route. That calls Homepage server-to-server with `cache: no-store` and a 12-second timeout. This is a network hop outside the seven WebDAV calls. It is required by the current auth decision; a TTL cache would delay password-change revocation.
- `NoteStore` constructs one `https.Agent` per API request, `maxSockets: 1`; the handler destroys it in `finally`. This constrains concurrency inside that one server request. Calls in the open/save protocol are already sequential. It is **not a global queue across all Notes API requests**. Since the agent is destroyed at the end of each request, it also does not provide connection reuse across separate API requests; whether fresh DNS/TCP/TLS dominates is unmeasured. `storage.mjs` records DNS/TCP/TLS/TTFB and `reusedSocket` on per-call rows, but normal API logging emits operation totals/call counts, not those per-call timing rows.
- A normal update of an existing note verifies its old record, checks the new immutable path, writes and verifies the immutable record, then writes and verifies the catalog under the root lease. Including LOCK/catalog read/UNLOCK gives **9 sequential WebDAV calls** on the common successful path. This readback, CAS-by-lock, fencing, and operation receipt behavior protects acknowledged saves.
- Owner autosave is debounced by 900 ms after input. The UI only reports saved after a matching server acknowledgement; this delay and cloud acknowledgement are distinct from local typing responsiveness.
- Foreground GET may retry transient failures for up to 120 seconds / 32 attempts. This improves delivery, not baseline speed; a lock conflict or repeated network error can therefore create a long tail. A root lock also covers shared editors, not only the owner.
- Background refresh is scheduled every 60–70 seconds, and can be skipped while hidden, offline, a foreground request is active, a draft is dirty, or organization is in progress. It refreshes list metadata; an already open editor is not silently replaced with another device's content. Open/reopen fetches the current head; stale drafts retain their revision and conflict rather than overwriting.

### Direct local fixture observations

Using the checked-out source with the repository's in-memory WebDAV fixture and synthetic data only:

- A cold stable-head `get` emitted 7 WebDAV calls; a known-revision `get` emitted 3.
- A temporary candidate owner read that held the root lease across snapshot + immutable GET emitted 4 calls. With its content GET deliberately paused, a concurrent synthetic save received 423; after unlock it succeeded. This is a protocol/count and contention demonstration, not latency data and not a finished/authenticated implementation.
- `node --test test/read-snapshots.test.mjs test/cache.test.mjs`: 11/11 pass, including writer progress during the current unlocked content transfer, consistent reread after a write, and revocation/move/delete guards. `test/shared-auth.test.mjs`: 2/2 pass after installing the lockfile dependencies into the temporary clone only (Node 22 emitted the repository's Node 24 engine warning). No source files were changed in Hunghvt-notes.

### Historical evidence and unmeasured claims

`docs/RELEASE.md` reports a small 2026-10-18 smoke: three owner save server durations of 3.025, 6.447, and 7.400 seconds and one shared save of 4.042 seconds. This predates the current October 26 auth checkpoint and is not an open-note measurement, current p50/p95, or device/browser timing. No current cold-open, editor-ready, save-ack, second-device visibility, or per-phase production timings are available. Do not claim a specific percentage or number of milliseconds improvement.

The code establishes serial round trips and the Homepage auth dependency. It does not establish which dominates real user latency. A slow Homepage request, Koofr RTT/TLS, lock wait/423 retry, Vercel execution, or browser/phone rendering remain unmeasured contributors.

## Gemini consultation and Codex verification

One actual `gemini-task` call succeeded: key alias `key1`, model `gemini-3.5-flash-lite`; the answer was advisory and no secret or Notes content was sent.

Agree with Gemini that phase timing should precede architectural changes; that 7 serial WebDAV calls are a cold-open cost; and that an owner-only four-call variant is a reasonable experiment. Also agree that persistent full-content cache, per-note locks, materialized read models, and Native Koofr API are not free wins and lack current evidence to justify a switch.

Reject/correct three Gemini claims:

1. `maxSockets: 1` does not queue every user or API request globally: the agent is instantiated and destroyed per request. This is visible in `NoteStore` and the handler's `finally`.
2. The stated “50–150 ms per WebDAV request” and resulting latency estimates were not measured and have no supporting source in this research. They are not used.
3. The owner is not the only possible writer. Live edit links are supported; all these operations contend on the root lock. The four-call path can reduce an uncontended cold open, but holding the exclusive root lease during the immutable transfer can make another owner/shared read or save return 423 and enter the patient retry path. Local fixture reproduced the writer 423.

## Recommendation and tradeoffs

Keep Koofr + Vercel and all current draft/CAS/fencing/idempotency/share checks. Do not enable persistent full-note cache or weaken server acknowledgement. Current session-memory warm opens already paint before revalidation; a cold open after page reload is the case a four-call owner path could improve.

Priority 1 is a **small sanitized timing-only qualification**, not a production optimization: expose already-collected WebDAV call label/method/status/DNS/TCP/TLS/TTFB/duration/reused-socket fields to an isolated preview observer, and time Homepage auth separately. Never capture URL credentials, headers, body, note contents, cookies, prompt, or raw errors. This distinguishes auth, connection setup, provider wait, and lock/retry. No such telemetry was deployed or run against production in this task.

Priority 2, if timing shows serial WebDAV calls dominate, test owner-only single-lease open behind an experiment flag in a dedicated synthetic namespace. Keep shared opens on the current two-snapshot protocol. Revalidate the snapshot inside the lease, verify immutable record hashes/identity, preserve the lease token and always release/expire it safely. The defensible upside is **3 fewer serial WebDAV calls (7→4, 43% fewer calls on that path)**, not a 43% end-to-end latency promise. The costs are a longer exclusive root-lock hold, possible 423s for other tabs/shared editors and increased tail latency under contention. Do not change the default or deploy until the synthetic contention comparison passes and shows useful latency improvement.

Persistent owner full-content cache could paint after reload but changes the 2026-10-19 private-device decision, increases local exposure/staleness risk, and does not improve Koofr save acknowledgement or a cold second device. It needs explicit product/security approval. Per-note locks require redesigning catalog-wide folder/share/delete/restore invariants and a safe lock ordering; not a small patch. A materialized read model brings staleness and a synchronization protocol. No source or official evidence here shows Koofr's native API is faster or supplies the required CAS. A different transactional backend is the only broad architectural route to much faster cold cloud acknowledgement, but violates today's provider constraint.

## Separate performance outcomes

| Outcome | Current behavior/evidence | How to qualify |
| --- | --- | --- |
| Editor ready / typing | Warm same-page owner content can paint from memory before a 3-call revision check. Cold open waits for the 7-call API path. Once open, typing is local; autosave waits 900 ms after input. No phone/browser timings. | Measure click-to-editable for cold and warm separately; measure keystroke-to-render separately from network. |
| Koofr save confirmation | Successful existing-note save is 9 sequential WebDAV calls plus owner Homepage auth; UI waits for matching operation acknowledgement. Historical 3.025–7.400 sec samples are old save-only smoke. | Measure last-keystroke-to-ack (including debounce) and request-start-to-ack, successful p50/p95, with 423/retries separately. |
| Other-device visibility | Background list refresh nominally every 60–70 sec when eligible; it may skip on hidden/dirty/busy states. It does not replace an already-open editor's body. | Measure server-ack on device A to revision/list appearance on B, then separately time B's open/reopen to current content. |

## Smallest next experiment

After approval to alter/deploy an isolated preview (not production): use a dedicated synthetic Koofr namespace and no real Notes. First capture the current cold-open/auth/WebDAV phase baseline; then run the four-call owner experiment with the same fixture. Include a deliberately slow immutable read with one concurrent shared/owner writer to record lease hold and 423/retry effects. Keep shared flow unchanged. Compare successful cold-open p50/p95, lock hold, writer acknowledgement, and all 423/retry counts. Pick an acceptance threshold only after observing baseline; a small sequential sample is qualification, not p95-grade capacity proof. Keep save ack and cross-device freshness as separate criteria. No deployment or benchmark was done here.
