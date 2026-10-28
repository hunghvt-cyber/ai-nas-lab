# Trạng thái ngày 27/10/2026

## Xác minh wrapper Gemini — 28/10/2026

Ngày 28/10, phiên NAS chạy trực tiếp wrapper hiện có `/home/admin/bin/gemini-task`; một lời gọi API thật tới `gemini-3.5-flash-lite` bằng alias được ghim trả phản hồi mong đợi. Không đọc/đổi key, không xoay key; lượt smoke test này chỉ xác nhận một alias/model tại thời điểm đó. Bài học tái sử dụng được lưu tại [GEMINI-API-WRAPPER-SMOKE-20261028.md](GEMINI-API-WRAPPER-SMOKE-20261028.md). Các nhận định riêng của ứng dụng vẫn phải lưu trong repo ứng dụng.

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

## Phạm vi repo

Repo này chỉ quản lý công cụ Codex/Gemini, wrapper API, quota/retry và bài học phối hợp AI. Bàn giao/vận hành của từng ứng dụng lưu trong repo ứng dụng tương ứng. Các báo cáo Notes trước đây đã chuyển nguyên nội dung và đối chiếu Git blob sang [Hunghvt-notes](https://github.com/hunghvt-cyber/Hunghvt-notes/tree/main/docs/history/ai-nas-lab); không dùng các mốc Notes cũ trong lịch sử repo này như trạng thái runtime mới.
