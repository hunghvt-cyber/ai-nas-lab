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
