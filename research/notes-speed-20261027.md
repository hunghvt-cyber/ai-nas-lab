# Notes: nghiên cứu tốc độ ngày 27/10/2026 (Asia/Ho_Chi_Minh)

## Trạng thái nhiệm vụ
Yêu cầu: ChatGPT cùng Gemini nghiên cứu Notes Koofr chậm, mục tiêu cảm giác nhanh như thời Blob/gần Google Keep.
ChatGPT đã đọc source và tài liệu. Chưa gọi được Gemini từ phiên ChatGPT vì không có kết nối NAS; prompt tối thiểu không chứa dữ liệu người dùng đã chuẩn bị tại notes-speed-gemini-prompt-20261027.txt. Không giả lập kết luận Gemini. Chưa sửa/deploy Notes, đọc nội dung Notes thật hoặc chạy benchmark production. Chưa có số đo hiện tại hay chứng minh ngang Google Keep.

## Nguồn và giới hạn
Repository hunghvt-cyber/Hunghvt-notes, ref release/minimal-notes. Không dùng main như production.
Đọc README, AGENTS, docs/ARCHITECTURE.md, docs/RELEASE.md, PERFORMANCE-20261019.md, PERFORMANCE-STEP1/STEP2/STEP4 và SHARED-PASSWORD-DECISION-20261026.md.
README ghi Code Inbox source a258ffc5; release metadata cũ ghi 09bf7dd; chưa kiểm deployment hiện tại. Số call bên dưới là source-count không retry, không phải số ms runtime.
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
1. Trong ràng buộc hiện hành, thử owner-only single-lease open: LOCK/catalog GET/immutable GET/UNLOCK, share vẫn hai snapshot. Giữ CAS/fencing/hash/ACL; kiểm lease hết hạn và cạnh tranh writer. Đây là tái sử dụng đánh đổi step1 có chọn lọc, không ý tưởng hoàn toàn mới; ít request hơn không tự bảo đảm p95 tốt hơn.
2. Đo auth/Homepage, cold/warm DNS/TCP/TLS, từng WebDAV method, hold-time/root423, client queue và retry riêng trước khi chọn tối ưu. Không đổi region chỉ từ phỏng đoán Koofr EU; fra1 là metadata lịch sử.
3. Xem connection reuse có affinity theo đúng credential/namespace và cleanup giới hạn, tránh log secret, crosstenant cache và global single-socket queue. In-flight auth coalescing chỉ gộp request đang chạy; không tự cache TTL vì sẽ đổi thời điểm vô hiệu hóa mật khẩu.
4. Muốn mở nhanh qua reload: owner content cache cục bộ + background sync là thay đổi quyết định cache 19/10, chưa được duyệt triển khai. Cần phân biệt Đã giữ trên máy với Đã đồng bộ Koofr, tránh ghi đè draft/session, giữ CAS. Không áp shared persistent cache, không hứa nhanh trên thiết bị mới/cache lạnh. Không giảm cloud ack.
5. Per-note locks/split catalog/materialized read models cần thiết kế schema và giao thức cross-note folder/share/delete/restore nhất quán; không thể chỉ bỏ root lock. Không giả định native Koofr API có CAS hoặc nhanh hơn WebDAV.
6. Muốn cloud ack/multi-device gần tức thì có thể cần backend transaction khác; trái quyết định hiện hành Koofr-only/no new DB, chỉ so sánh như lựa chọn cần đổi quyết định, không tự thêm dịch vụ.

## Tiêu chí đề xuất
Tách editor-ready, durable-local-draft, server-confirmed ack và máy thứ hai thấy thay đổi. Ví dụ mục tiêu thử nghiệm owner cache hit editor-ready <=150ms là mục tiêu, không kết quả đo.
Đo fresh-open/cache-hit/reload/save và có/không một writer; báo thành công p50/p95 riêng với 423, số lượt retry và tổng request. Chỉ làm thử nghiệm isolated synthetic namespace khi có quyền phù hợp, không dùng note thật hoặc bật benchmark production. Giữ dữ liệu gốc và mọi draft.

## Bước tiếp theo
Chạy một lượt Gemini với prompt đã chuẩn bị, tối đa 2 lượt theo quy tắc AI NAS Lab. Ghi kết quả như tư vấn, Codex tự đối chiếu. Sau đó chọn một thử nghiệm nhỏ, ưu tiên owner-only single lease và đo pha auth/socket nếu Gemini không chỉ ra rủi ro loại trừ.

## Tham khảo chính thức
- https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API
- https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria
IndexedDB là lưu cục bộ; có quota/eviction, không thay thế backup cloud.
- https://koofr.eu/help/koofr_with_webdav/what-is-the-difference-between-webdav-and-rclone/
Koofr phân biệt WebDAV và native API; tài liệu này không chứng minh API nhanh hơn hoặc có CAS.
