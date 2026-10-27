# Notes: nghiên cứu tốc độ ngày 27/10/2026 (Asia/Ho_Chi_Minh)

## Trạng thái nhiệm vụ
Yêu cầu: ChatGPT/Codex cùng Gemini nghiên cứu Notes Koofr chậm, mục tiêu cảm giác nhanh như thời Blob/gần Google Keep.
Đã gọi `/home/admin/bin/gemini-task` một lần thành công bằng prompt đã lọc, rồi Codex đối chiếu từng nhận định với source và fixture local. Không giả lập phản hồi. Chưa sửa/deploy Notes, đọc nội dung Notes thật hoặc chạy benchmark production. Chưa có số đo hiện tại hay chứng minh ngang Google Keep. Kết luận và bằng chứng mới nhất nằm trong [notes-speed-results-20261027.md](notes-speed-results-20261027.md).

## Nguồn và giới hạn
Repository hunghvt-cyber/Hunghvt-notes, ref release/minimal-notes. Không dùng main như production.
Đọc README, AGENTS, docs/ARCHITECTURE.md, docs/RELEASE.md, PERFORMANCE-20261019.md, PERFORMANCE-STEP1/STEP2/STEP4 và SHARED-PASSWORD-DECISION-20261026.md.
Source checkout tại `ee5d75f5795bf2ce79971c7a3dfe772119ad6d1a`. Tài liệu 26/10 ghi deployment source `0c8c0761c2625ae2be747e448a7259f974dccb34`; các file read/auth/transport liên quan giống nhau tại hai checkpoint, trừ hai guard save không liên quan. Không có Vercel CLI/project link để kiểm tra deployment đang phục vụ lúc nghiên cứu. Số call bên dưới là source-count/fixture, không phải số ms runtime.
Các file source/blob đã đọc:
- lib/store.mjs b9f16e08018c4e148d2ba5ae3e6b97662696ebd1
- lib/storage.mjs 21c1336db366b80c972fa67ea7d8d0a3d73bca51
- lib/preview-api.mjs ded684e03f78cd3d00245cffaca1a3ecbadbc220
- lib/shared-auth.mjs 65a8af37360c455f0fe64d13a00c1badc016d820
- public/app.js 9a0a0ca2b81ca38ede9bd51ac1c4cf5b0e4022bf

## Các nút thắt có căn cứ
| Đường đi | Lượt WebDAV tuần tự thông thường |
| --- | --- |
| Danh sách và thư mục | 3: LOCK/GET catalog/UNLOCK |
| Mở note chưa cache | 7: snapshot 3 + immutable GET 1 + final snapshot 3 |
| Kiểm revision owner không đổi | 3 |
| Lưu note cũ, chưa replay | 9: LOCK, catalog GET, old-record GET, new-path GET, immutable PUT/GET verify, catalog PUT/GET verify, UNLOCK |

Lưu ý đây là đường thành công; lỗi/retry/replay có số lượt khác.
Khóa toàn kho còn gây 423 giữa các tab, owner và share. Retry 120s/max32 giúp tiếp tục giao hàng nhưng không giảm latency cơ sở.
Mỗi owner request trong homepage-v1 còn chờ Homepage password version; chưa đo ms. Trước store nên storageMetrics không thể hiện riêng chi phí này.
Mỗi request tạo mới NoteStore/https.Agent maxSockets=1. keepAlive trong một request không chứng minh socket được dùng lại qua nhiều request. Đây là hướng đo TLS/connection, không khuyến nghị tăng socket ngay vì từng có lỗi inherited lock token trên parallel sockets.
UI cache full content chỉ trong session memory; mở note cache miss đợi API xong mới fill. Preview IndexedDB và durable draft đã có; không đề xuất lại như cải tiến mới.

## Vì sao cải tiến trước chưa giải quyết
Step1 giảm duplicate lock, open 4 calls dưới một lease. Step2 chuyển content GET ra ngoài lease để nhường writer và kiểm ACL cuối: open tăng 4 lên7. Đây là đánh đổi concurrency/latency, không tự chứng minh nhanh hơn một người.
Các việc đã có: list+folders bootstrap, inline save ack, lazy share list, gộp GET, ưu tiên ghi/foreground, giảm poll, session cache, durable drafts và retry lệch nhịp.

## Hướng nghiên cứu, chưa phải quyết định triển khai
1. Bước đầu đã làm trong fixture: xác nhận current open 7 calls và candidate owner single-lease 4 calls; candidate khiến writer đồng thời nhận 423 khi content GET đang giữ root lock. Chỉ tiếp tục thử nếu đo cho thấy WebDAV serial RTT chiếm đáng kể và chấp nhận được tác động contention.
2. Trước quyết định triển khai cần đo riêng Homepage auth, DNS/TCP/TLS/TTFB từng WebDAV call, lock hold/423, retry và UI phases trên preview namespace tổng hợp. Chưa có phép đo mới; không đổi region chỉ từ phỏng đoán Koofr EU hoặc metadata region cũ.
3. Xem connection reuse có affinity theo đúng credential/namespace và cleanup giới hạn, tránh log secret, crosstenant cache và global single-socket queue. In-flight auth coalescing chỉ gộp request đang chạy; không tự cache TTL vì sẽ đổi thời điểm vô hiệu hóa mật khẩu.
4. Muốn mở nhanh qua reload: owner content cache cục bộ + background sync là thay đổi quyết định cache 19/10, chưa được duyệt triển khai. Cần phân biệt Đã giữ trên máy với Đã đồng bộ Koofr, tránh ghi đè draft/session, giữ CAS. Không áp shared persistent cache, không hứa nhanh trên thiết bị mới/cache lạnh. Không giảm cloud ack.
5. Per-note locks/split catalog/materialized read models cần thiết kế schema và giao thức cross-note folder/share/delete/restore nhất quán; không thể chỉ bỏ root lock. Không giả định native Koofr API có CAS hoặc nhanh hơn WebDAV.
6. Muốn cloud ack/multi-device gần tức thì có thể cần backend transaction khác; trái quyết định hiện hành Koofr-only/no new DB, chỉ so sánh như lựa chọn cần đổi quyết định, không tự thêm dịch vụ.

## Tiêu chí đề xuất
Tách editor-ready, durable-local-draft, server-confirmed ack và máy thứ hai thấy thay đổi. Ví dụ mục tiêu thử nghiệm owner cache hit editor-ready <=150ms là mục tiêu, không kết quả đo.
Đo fresh-open/cache-hit/reload/save và có/không một writer; báo thành công p50/p95 riêng với 423, số lượt retry và tổng request. Chỉ làm thử nghiệm isolated synthetic namespace khi có quyền phù hợp, không dùng note thật hoặc bật benchmark production. Giữ dữ liệu gốc và mọi draft.

## Bước tiếp theo
Nếu được duyệt sửa/deploy preview riêng: chạy baseline rồi candidate owner-only single lease trong namespace Koofr tổng hợp; giữ shared path hiện tại, thêm phép thử một writer đồng thời, và so p50/p95 editor-ready/server request/save ack/lock hold riêng. Không dùng Notes thật hoặc production và chưa thay mặc định cho tới khi có số liệu.

## Tham khảo chính thức
- https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API
- https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria
IndexedDB là lưu cục bộ; có quota/eviction, không thay thế backup cloud.
- https://koofr.eu/help/koofr_with_webdav/what-is-the-difference-between-webdav-and-rclone/
Koofr phân biệt WebDAV và native API; tài liệu này không chứng minh API nhanh hơn hoặc có CAS.
