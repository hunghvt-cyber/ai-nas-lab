> **Artifact-integrity blocker resolved — 27/10/2026:** candidate `082824c51f305a9c94ecdea6aafb9a479a4ccf5e` replaces the corrupted `6dc6d18`. Independent GitHub full-module reconstruction matches blob `3454137816de08aaf9e7ab302c37b4f9ae1d9aea`, and Node 24.22.1 syntax check passes. Lockfile blob `8c4e1c62ffba93eb05f2b1bf1eecbdfd0a848892` matches the NAS report. Clean-checkout 170/170 and repeated cloud smoke PASS are NAS-reported. **Vercel WIF/integration and migration still pending; Koofr remains production.** See [review and closure](research/notes-firestore-published-source-review-20261027.md).

# Trạng thái ngày 27/10/2026

## Nguồn và mức xác minh

Tổng hợp từ báo cáo Codex chạy trên NAS được người dùng chuyển tiếp trong hội thoại. Phiên ChatGPT không trực tiếp SSH vào NAS. Ngày 27/10/2026 (Asia/Ho_Chi_Minh), người dùng chuyển tiếp output --help/status, symlink và toàn bộ wrapper. Bản lưu src/gemini-task có SHA-256 khớp byte với checksum host được chuyển tiếp: 29481dc45c6461b5f993a29f7caba32871cd826c6885abcf99a4928652c8ec00. Đây là bằng chứng đối chiếu nội dung chuyển tiếp, không phải xác minh trực tiếp filesystem NAS.

## Môi trường được báo cáo

- Debian 12 ARM64, user admin, RAM khoảng 3.6 GiB; Codex chạy systemd.
- Node user-local 22.23.4; Gemini CLI 0.65.0 còn cài nhưng **không dùng trong luồng API**.
- Wrapper: /home/admin/bin/gemini-task; ~/.local/bin/gemini-task trỏ wrapper mới.
- HOME=/home/admin, uid=1000 trong shell Codex.
- Key store: /home/admin/.config/gemini-task/keys.json; thư mục 700, file trạng thái/key/lock 600 theo báo cáo.
- Tài liệu host cũ: /home/admin/0219nas-aio-issue12/CONFIG-AND-ACCESS.md và AGENTS.md. Repo này đã lưu bản nguồn wrapper nhận qua chat; chưa sửa checkout hoặc runtime host.

## Hành vi wrapper

Gọi Gemini API trực tiếp; không qua CLI/OAuth. Prompt từ stdin/file; --key keyN khóa vào một nguồn, không tự failover. stdout được buffer trước khi in; chưa bảo đảm câu trả lời hoàn chỉnh về nội dung (MAX_TOKENS vẫn được nhận là thành công). stderr không in body lỗi, nhưng trường error.status chưa được lọc ký tự/giới hạn. Không khai báo tools. Có timeout tổng, retry giới hạn và khóa/ghi trạng thái an toàn khi đồng thời.

Tối đa key1…key5; output status mới liệt kê đủ key1…key5: key1 active, key2…key5 ready. keys add chỉ hỏi key ẩn; member/quota-group mặc định alias, ưu tiên theo số, project ID trống (unknown). Không bắt nhập metadata. Người dùng xác nhận 5 nguồn dự kiến thuộc 5 project độc lập; chưa xác minh danh tính project qua API. ready chỉ là trạng thái local, không xác nhận generateContent thành công.

Key đang hoạt động được ưu tiên. Lỗi key đánh dấu không khả dụng; quota/cooldown theo nhóm và model. Không đổi key với lỗi prompt/model/policy. 503 retry cùng key tối đa 2 lần bổ sung, backoff 1 rồi 2 giây, nằm trong timeout tổng; sau đó dừng, không xoay key khác.

Model mặc định cuối cùng được báo cáo: **gemini-3.5-flash-lite**. Không mặc định quay lại gemini-3.8-flash vì nguồn cũ từng gặp 503. Tên model/giá/khả dụng phải kiểm tra lại khi đổi, không bảo đảm vĩnh viễn.

## Bằng chứng runtime được báo cáo

- key1 models.list HTTP 200 qua urllib và curl (khoảng 0.3–0.4 giây tổng).
- gemini-3.8-flash generateContent: key1 HTTP 503 sau khoảng 1.9 giây; key2 HTTP 503 sau khoảng 4.1 giây. Chưa xác định nguyên nhân phía dịch vụ; không gọi đây là lỗi key/quota.
- gemini-3.5-flash-lite bằng key1: prompt ngắn giới hạn 8 output tokens HTTP 200, nội dung OK.
- Qua gemini-task: trả OK; thêm một tác vụ phân tích thực tế thành công từ môi trường Codex.
- Chưa có bằng chứng generateContent thành công bằng key2…key5, failover quota thực tế hoặc bài phản biện 2 lượt hoàn chỉnh. Đã có output status liệt kê 5 alias.

## Sửa lỗi timeout

Wrapper cũ đọc hết body HTTPError trước khi phân loại status. Body lỗi có thể treo khiến timeout tổng che HTTP status. Đã sửa giữ 503 ngay khi nhận headers, không đợi body lỗi. Đây là đường lỗi được xác định trong code theo báo cáo, **không chứng minh hồi tố** nguyên nhân của các timeout 35/90 giây vì lần cũ thiếu đo pha.

## Kiểm thử mô phỏng được báo cáo

Thành công, 429/Retry-After, bỏ qua cùng quota-group, key lỗi/failover, retry network/5xx, lỗi prompt không đổi nguồn, tất cả nguồn lỗi, --key không failover, quota cạn theo lỗi có cấu trúc, status không lộ key, 8 tiến trình ghi trạng thái đồng thời. Có kiểm tra timeout tổng, nhập key giả, quyền 700/600, cú pháp và git diff --check. Sau sửa 503: tối đa 3 request cùng key và không thử key2. Bộ test lịch sử trên NAS chưa được cung cấp. Bản nguồn thật đã lưu tại src/gemini-task; bộ test mới tests/test_baseline.py được viết trong phiên này và chạy offline thành công 11/11 trong container ChatGPT, dùng key giả và mock API, không gọi Google. Trong đó 3 test characterization xác nhận lỗi còn tồn tại, không phải xác nhận đã sửa. Xem REVIEW-20261027.md.

## OAuth đã dừng

Nhiều lần nhập code trước đây đã đổi token và lưu thành công theo log chẩn đoán, nhưng UI restart lặp lại. Lỗi cuối hiển thị client không còn được hỗ trợ cho Gemini Code Assist cá nhân. Quyết định: bỏ OAuth cá nhân, không tiếp tục debug hoặc nhập code; dùng API.

Theo báo cáo dọn dẹp: gỡ patch/instrumentation, khôi phục bundle từ tarball chính thức, xóa log thử; không còn tmux gemini-oauth-diag hay listener 53682. Đã gỡ biến ép OAuth/callback khỏi profile/wrapper; credential OAuth cũ vẫn giữ quyền 600. Không tạo firewall rule. Rule Termius trên Android do người dùng quản lý, **chưa có xác nhận đã xóa**.

## Việc tiếp theo

1. Sửa ba hành vi đã tái hiện trong REVIEW-20261027.md trên bản phát triển, chuyển test characterization sang kỳ vọng an toàn. Chưa thay runtime NAS.
2. Tìm bộ test lịch sử trên NAS nếu còn; kiểm tra key2…key5 bằng prompt nhỏ khi cần, không nhập lại key chỉ vì trạng thái ready.
3. Kiểm tra bài Codex → Gemini phản biện → Codex tổng hợp; giới hạn 2 lượt.
4. Giữ nguyên model hoạt động, không tiếp tục chẩn đoán OAuth/3.8 nếu không có yêu cầu mới.

## Notes speed research — 27/10/2026

Đã đọc AI NAS Lab handoff và `Hunghvt-notes` nhánh `release/minimal-notes` tại
`ee5d75f5795bf2ce79971c7a3dfe772119ad6d1a`. Gemini được gọi trực tiếp qua
`gemini-task` một lần bằng `key1` / `gemini-3.5-flash-lite`; Codex đã kiểm chứng
phản biện với code và fixture. Không đọc Notes thật, không benchmark production,
không deploy hoặc đổi cấu hình.

Code cold-open hiện tại gồm 7 WebDAV call tuần tự; known-revision 3. Owner API
còn kiểm Homepage auth version mỗi request. Agent WebDAV `maxSockets:1` thuộc
mỗi request và bị destroy cuối request, không phải global queue. Fixture local
xác nhận candidate owner single-lease là 4 call nhưng làm writer đồng thời nhận
423 cho tới khi unlock. Chưa có số đo cold-open hoặc p50/p95 production; chỉ có
smoke save lịch sử 3.025–7.400 giây, không áp làm kết quả hiện hành.

Giữ Koofr + Vercel, draft/CAS/fencing/idempotency/live ACL và xác nhận lưu.
Ưu tiên đo riêng auth và WebDAV trên preview namespace tổng hợp trước khi quyết
định thử candidate 4-call; chưa deploy/benchmark preview. Báo cáo, nguồn và test
chi tiết: [research/notes-speed-results-20261027.md](research/notes-speed-results-20261027.md).

### Notes owner-open experiment preparation — 27/10/2026

Prepared local-only branch `codex/notes-owner-open-experiment-20261027` in
Hunghvt-notes; no Preview deploy, Koofr namespace/data, or production access.
Added opt-in Preview-only owner single-lease read, sanitized auth/WebDAV phase
telemetry, a fixture comparison script, and concurrency/redaction tests. Share
reads and writer/draft/CAS/fencing/ACL/idempotency paths stay on the current
protocol. Node 24 suite: 147/147 passed; fake 5 ms/call fixture: owner cold-open
p50/p95 47/57 ms current vs 27.1/33.1 ms candidate. In forced owner/share
contention, current got 0/1 save 423s; candidate got 1/2 attempts 423 and added
1,000 ms virtual retry delay. These numbers are synthetic and do not justify
deployment; retain current default pending real isolated Preview results.

Final Notes commit `8c75625f1756ddac91a766071557eb7c0afefcc7`, checkout
`/home/admin/Hunghvt-notes`. Branch is not pushed because Vercel automatic Preview
behavior was not verified. Real measurement still needs a dedicated lab Preview
target/authorization, Preview-only session and Koofr credentials, and a fresh
synthetic namespace. Existing Preview auth is local/synthetic and cannot time
the Homepage auth hop; that requires a separately approved synthetic auth source
or explicitly authorized safe measurement. See
[research/notes-speed-results-20261027.md](research/notes-speed-results-20261027.md).

## Notes Firestore exploration — 27/10/2026

Checked the NAS shell: no Firebase CLI, gcloud, Java, ADC config, or Google Cloud
project variables; no suitable cloud session was verifiable. RAM available was
about 2 GiB, system volume had about 1.4 GiB free, and port 8080 was already in
use. A temporary Java 21 download was canceled due very slow transfer before
install; no emulator started and no system packages/services changed.

Prepared a dependency-injected Firestore compatibility transport, chunk/hash
storage, lock/fencing adapter tests, demo-only emulator config guarded on
loopback:8089, and smoke runner. Koofr remains active; `api/app.js` does not
select Firestore. Node 24 full tests: 154/154 pass, all against the existing
suite plus an in-memory Firestore-compatible fake. **No real Firebase emulator,
cloud permission, Firestore database, billing, migration, or deployment has been
verified or used.**

Gemini advised a direct Firestore repository as the cleaner permanent design;
Codex keeps the adapter as a limited parity prototype to reuse existing CAS,
ACL, fencing, idempotency and recovery logic while the backend stays disabled.
The fake does not establish Firestore transaction behavior or latency. Vercel
OIDC federation is officially supported as a no-long-lived-key auth path, but
needs an existing GCP project administrator to set up IAM/WIF and a service
account. Details and mobile console links:
[research/notes-firestore-20261027.md](research/notes-firestore-20261027.md).

Notes commit `8e6d0dbfe63396fa2fc5b1e8c7e707a7db3cb66a` is local on branch
`codex/notes-owner-open-experiment-20261027` at `/home/admin/Hunghvt-notes`.
Nothing is pushed or deployed from Hunghvt-notes; do not migrate or create a cloud database
until emulator parity, project authorization and cost/rollback are reviewed.

### Native Firestore repository direction — 27/10/2026

Continued on local branch `codex/notes-firestore-native-20261027`; compatibility
adapter remains unchanged and Koofr remains active. Added an unwired native
repository prototype and architecture/cost handoff in `Hunghvt-notes` and this
repo’s `research/notes-firestore-20261027.md`. Focused Node 24 tests pass 8/8
against an in-memory fake only; no emulator/cloud proof. Native code covers
per-note CAS, idempotent saves, shared authorization/revoke, version history,
chunk/hash validation and Inbox share guards. Folder/order/trash/purge and
backup parity are not implemented yet and block integration. Gemini critique
was one filtered advisory; Codex corrected unsupported fixed 1-write/sec and
500-total-op claims against current official docs.

No gcloud/firebase CLI or ADC was present in the checked NAS shell. Least-work
cloud path is a synthetic namespaced probe from Cloud Shell on phone/iPad,
using an existing authorized dedicated non-production project/database plus
`roles/datastore.user` (project-level access); NAS ADC and Vercel production
OIDC are separate setups. No billing, database, cloud
call, migration, or deploy occurred. Full repository tests could not load six
files because `iron-session` is absent; existing fixture cleanup reported only
39 allowlisted synthetic folders removed and production root unchanged. Details
and official links: `research/notes-firestore-20261027.md` and
`Hunghvt-notes/docs/firestore-native-design.md`.

### Isolated Cloud Shell smoke ready — 27/10/2026

Updated Hunghvt-notes branch `codex/notes-firestore-cloudshell-20261027`, commit
`ebd704d3a149f5756dbc8b9a41eda5f326efe09b` (GitHub). `npm ci` with the committed
lockfile succeeded under Node 24; the repository's default test command now
uses an offline harness that strips Koofr/OIDC configuration and blocks network
requests outside loopback. Local Node 24 suite passed 163/163, and GitHub Actions
was running the branch CI at handoff. Vercel's exact-branch auto-deploy flag is
disabled; Vercel returned zero deployments for that branch. No Cloud Firestore
probe has run yet.

For the smallest cloud check, use an already existing dedicated non-production
project with default Firestore Native DB and a user granted `roles/datastore.user`.
On phone/iPad choose it in [Google Cloud Console](https://console.cloud.google.com/),
open [Cloud Shell](https://shell.cloud.google.com/?show=terminal), and paste the
fully prepared single command in `Hunghvt-notes/docs/FIRESTORE-CLOUD-SMOKE.md`.
It downloads Node 24 only under `/tmp`, uses the selected `gcloud` project and
Cloud Shell human auth, creates one random synthetic note/share, measures
owner/save/CAS/share/revoke, then removes those exact documents. It will not
create a project/database or enable billing. This path is separate from NAS ADC
and Vercel production OIDC. See the branch's smoke guide; no secret or credential
is needed in chat.

### Native Firestore integration prepared — 27/10/2026

Supersedes the Cloud Shell-only smoke instructions above for the next step: the
user asked to avoid Cloud Shell and result relay. On NAS, installed official
Google Cloud CLI 590.0.1 for Linux ARM64 under
`/home/admin/.local/opt/notes-google-cloud-cli`; the downloaded archive SHA-256
matched Google's published checksum. Wrapper `/home/admin/bin/notes-gcloud`
uses only its isolated config home at
`/home/admin/.local/state/notes-gcloud-home/.config/gcloud`. No ADC/account
credential exists there yet, and no Gemini or other app credential was read.

Hunghvt-notes safe branch
`codex/notes-firestore-cloudshell-20261027` now contains native Firestore
repository/runtime integration, explicit backend selection (Koofr remains the
default), migration/verification/rollback tooling, and integration tests.
GitHub commit: `4ef6be251dde9692f18b0b0f7364b7acebc5d5d4`. Full offline Node 24
suite: 169/169 pass. The tests use in-memory fakes and prove application
invariants only; they are not evidence of Firestore cloud behavior. No deploy,
billing change, real-note access, or migration occurred. Release branch was not
changed. Gemini reviewed a filtered technical summary once; its concern about
the old 500-write cap was stale, while the review highlighted share/folder/purge
race cases now covered by checks or documented as migration gates.

The Cloud Firestore smoke runner is prepared for project
`notes-lab-56f0f`, with random isolated vault names and cleanup scoped to those
two exact vaults. It exercises init, save/open, CAS, share/revoke, folder
deletion, trash/restore, backup/restore and purge. Required real-cloud proof is
still blocked by missing NAS ADC. To authorize just this NAS-only check, run the
following in an interactive NAS terminal, open Google's URL on the phone, sign
in to an account granted `roles/datastore.user` on the test project, then paste
the one-time code only into that terminal (never into chat):

```sh
/home/admin/bin/notes-gcloud auth application-default login --no-launch-browser --disable-quota-project
```

This creates ADC only in the isolated Notes gcloud config. It does not set a
quota project, enable billing, use Cloud Shell, or configure production Vercel
OIDC. Afterward Codex can run and inspect the cloud smoke itself; the user need
not relay output. Cloud authorization and a successful real smoke are still
unverified. See `research/notes-firestore-implementation-20261027.md` and the
Hunghvt-notes branch documents `docs/FIRESTORE-NATIVE.md` and
`docs/FIRESTORE-CLOUD-SMOKE.md`.

### Real Firestore smoke complete — 27/10/2026

The user completed the isolated NAS ADC sign-in. Codex ran the smoke directly
against `notes-lab-56f0f` / `(default)`; it returned `PASS` for init, owner
save/open, known-revision read, CAS conflict, share/open/revoke, folder delete,
trash/restore, snapshot count/hash restore and purge. Both synthetic vault roots
were deleted and an independent read confirmed they are absent. This was a real
Firestore API test, not an offline mock. One run's end-to-end operation timings
are recorded in Hunghvt-notes `docs/FIRESTORE-NATIVE.md`; they include network
overhead and are not a benchmark.

The first real attempts found and fixed two defects missed by fakes: first save
into a new folder used its timestamp before initialization, and backup refused
a completed folder-deletion tombstone as if work remained in progress. Both have
regression tests. A later artifact review found the published source and lockfile
had been clipped by output capture; that specific published artifact was not
valid and must not be used. It is now repaired and verified as described below.
No release branch, production deployment, Koofr data, billing, or real Notes
migration was touched.

Implementation and migration/rollback are prepared for review, not activated.
Production still needs a reviewed Vercel GCP Workload Identity Federation
configuration, exact project/service-account IAM, and production switch approval.
The current Koofr snapshot export limit remains 2 MiB; larger real data requires
a streaming snapshot export before migration. No production data size was read.

### Published source repair verified — 27/10/2026

The source-integrity review was correct: remote commit `6dc6d18` contained a
truncated `lib/firestore-native-repository.mjs`; inspection also found the
published `package-lock.json` was clipped. Both full files were restored from
verified local versions. Candidate [commit `082824c`](https://github.com/hunghvt-cyber/Hunghvt-notes/commit/082824c51f305a9c94ecdea6aafb9a479a4ccf5e)
is now remote HEAD of the same safe branch.

From a fresh checkout of that exact commit on Node 24.22.1: syntax check passed,
marker scan found no hits in 124 tracked code/docs/config files, `npm ci`
installed 143 packages, full `npm test` passed 170/170, and the isolated real
Firestore smoke passed all 11 checks. A separate read confirmed both synthetic
vault roots were removed. Git blob hashes match the tested checkout:
repository `3454137816de08aaf9e7ab302c37b4f9ae1d9aea`, lockfile
`8c4e1c62ffba93eb05f2b1bf1eecbdfd0a848892`. WIF/deploy/migration remain paused;
Koofr production is unchanged. Details are in
`research/notes-firestore-published-source-review-20261027.md`.


## Firestore Vercel preparation — 2026-10-27

Prepared test-only WIF/IAM in `notes-lab-56f0f`: exact Vercel Preview subject, team audience, no user-managed SA keys; IAM readback passed. Vercel branch-scoped Preview env creation is blocked because project `hunghvt-notes` is not connected to Git. No environment variables, deployment, billing or production data were changed. The required owner action is to reconnect it to `hunghvt-cyber/Hunghvt-notes`; then Codex can finish a branch-scoped synthetic Preview check.

Migration review confirms Koofr export stops at 2,000,000 bytes. No real Notes snapshot was inspected. If exceeded, stop before import until a bounded streaming exporter is implemented. Rollback plan freezes writes, exports current Firestore state and restores it to a fresh Koofr namespace, preserving post-cutover edits and verifying hashes before switching. Details: `research/notes-firestore-vercel-migration-review-20261027.md` and Notes candidate `docs/FIRESTORE-VERCEL-MIGRATION-REVIEW.md`.


## Vercel per-deployment Preview attempt — 2026-10-27

New path checked separately from the previous branch-scoped env attempt. Official CLI v65.4.0 help confirms `--env KEY=VALUE` and explicit `--environment preview`, but secret values would be process arguments, so none were passed. CLI auth check returned `loggedIn:false`; harmless dry-run failed with `You do not have access to the specified account` for scope `hunghvt`. Vercel REST API v13 documents no per-deployment env body field. No deployment or environment mutation occurred; WIF unchanged. Minimum next step is authenticate local Vercel CLI for team `hunghvt` (device/browser flow); no Git linkage is required for this CLI path. Details: `research/notes-vercel-per-deployment-env-20261027.md`.


## Direct Vercel Preview → Firestore verified — 2026-10-27

The previous branch-scoped project env attempt remains blocked by absent Git linkage, but a separate direct CLI deployment now works without linking Git. Authenticated Vercel CLI 65.4.0 deployed exact candidate commit `082824c51f305a9c94ecdea6aafb9a479a4ccf5e` to `hunghvt-notes` with explicit `--environment preview` and a 0600 external `--local-config` runtime env file. No secret was placed in argv, Git or emitted logs; temporary files were removed. No shared Preview variable or Production setting changed.

Deployment `dpl_H1L38KavsPzE4CbYnpSetZUGnW38` is READY, target Preview (`target:null`), no aliases: https://hunghvt-notes-7akbwqjy0-hunghvt.vercel.app. Readback confirms exact existing Vercel OIDC issuer/audience/subject. Live health, login, Firestore create/read, trash and purge all passed. The synthetic note is purged; the dedicated test vault has no active/trash note data. Two earlier trial deployments were deleted. Production remains Koofr and untouched. Details: `research/notes-vercel-direct-preview-firestore-result-20261027.md`.


### Production Firestore migration package — 27/10/2026

Supersedes the earlier statements that NAS ADC, Vercel Preview OIDC, and a real
Firestore smoke were unverified. The isolated NAS ADC now succeeds against
`notes-lab-56f0f/(default)`; the synthetic smoke passed. A direct deployment of
the verified Notes candidate to Vercel Preview also passed the synthetic app and
OIDC→STS→Firestore flow without linking Git. Production remains Koofr.

Read-only GCP inspection currently sees only the test project `notes-lab-56f0f`
(Notes Lab), whose only database is `(default)`. The Preview service account has
unconditional project-level `roles/datastore.user`; it must not be reused for
real Notes. No dedicated Production GCP project is currently discoverable, so
Production WIF/service account are intentionally not provisioned and no billing
was enabled.

Added to the Notes candidate: a GET-only Koofr exporter with before/after
catalog verification, per-record hash/ID checks, private 0700/0600 local output,
and no 2 MB endpoint cap; plus a rollback helper that writes the current
Firestore snapshot under the original Koofr namespace lock, verifies the exact
pre-cutover catalog hash/epoch, and preserves token-box/share links and edits.
Node 24 focused migration/rollback tests: 38/38 PASS. This is fixture evidence only. Real Koofr
snapshot size/count/hash remain unknown because Vercel Production variables are
Secrets and the CLI reports six values cannot be pulled. No Koofr read/write or
Production deployment occurred.

Vercel CLI identity was verified as team `hunghvt`, project `hunghvt-notes`.
An `env run` argument parsing failure briefly created the empty project
`notes-migration-runner`; Vercel confirmed it had zero deployments and zero
variables, and the exact project was deleted. The accidental local `.vercel`
link and `.gitignore` were removed. Current next blockers and exact cutover plan:
[research/notes-firestore-production-package-20261027.md](research/notes-firestore-production-package-20261027.md).

### Koofr snapshot and Production identity update — 27/10/2026

Supersedes the previous blockers above: the owner chose `notes-lab-56f0f` for
Notes after Preview access is revoked. Preview Firestore and exact-subject
impersonation grants were removed, its WIF pool disabled, and two real requests
from the old Preview identity were denied after propagation. A separate
Production SA/pool/provider now uses only the exact Production subject and a
database-scoped Firestore grant. No service-account key or billing change.

An SSO-protected staged Production deployment verified the exact Production
Vercel OIDC → STS → Firestore read against a synthetic nonexistent document.
The GET-only Koofr exporter passed access/POST-denial checks, verified each
record hash/ID and stable source catalog, and exported a private 1,829,423-byte
raw snapshot (404,736-byte gzip) to mode-0600 storage beneath mode-0700
directory. Migration verification returned VALID: 28 notes (6 active, 22 in
trash), 2 folders, 11 share records, 24 receipts, no erased tombstones,
fingerprint `5d652b5743f3d79735a1df1f917ff378649a89a767e80073934a9e78192235b5`.
Snapshot contents remain outside Git and chat.

Temporary export routes and all three staged deployments were removed. The two
existing production aliases were verified to remain on their original
deployments. Koofr still serves production; nothing was imported to Firestore,
no write freeze or production backend change occurred. Candidate now supports
private gzip snapshot verification/import and rollback input up to 50 MB, and
Firestore rollback export has an explicit 50 MB migration limit while the app
backup path retains its 2 MB cap. Remaining task is a reviewed cutover with a
fresh final snapshot after a short write freeze; rollback must export the latest
Firestore state first and publish it into the original Koofr namespace using
the recorded baseline catalog hash. Downtime duration remains unmeasured.
An optional final read-only Resource Manager policy refresh from NAS was
rate-limited with HTTP 429; no IAM changes followed the successful runtime
deny/allow checks. Re-read current bindings in cutover preflight before changing
the Production runtime config.
