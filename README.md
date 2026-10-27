# AI NAS Lab

Nguồn bàn giao cho Codex phối hợp Gemini API trên NAS. Cập nhật 27/10/2026 (Asia/Ho_Chi_Minh).

## Phạm vi

Chỉ chứa công cụ, cấu hình không nhạy cảm, quy trình và bài học phối hợp Codex/Gemini/AI. Kết quả vận hành, backup, migration và cleanup của ứng dụng phải nằm trong repo ứng dụng đó. Tài liệu Notes đã chuyển sang [Hunghvt-notes](https://github.com/hunghvt-cyber/Hunghvt-notes); lịch sử Git cũ được giữ, không tiếp tục dùng repo AI làm kho bàn giao cho Notes/NAS.

## Đọc trước

1. [AGENTS.md](AGENTS.md): quy tắc tiếp quản.
2. [CURRENT-STATE.md](CURRENT-STATE.md): cấu hình và bằng chứng mới nhất.
3. [RUNBOOK.md](RUNBOOK.md): thao tác vận hành.

## Trạng thái

Theo báo cáo Codex trên NAS do người dùng cung cấp trong hội thoại ngày 27/10: `gemini-task` gọi API thành công bằng key1 và `gemini-3.5-flash-lite`; có câu trả lời thử OK và tác vụ phân tích thực tế. Phiên ChatGPT không trực tiếp SSH vào NAS; đã đọc bản nguồn do người dùng chuyển tiếp và đối chiếu checksum.

Repo đã lưu [wrapper nguyên bản](src/gemini-task), SHA-256 khớp file NAS được báo cáo, và [11 kiểm thử offline mới](tests/test_baseline.py). Đây chưa phải bằng chứng phục hồi/triển khai trên NAS. Bộ test cũ trên NAS chưa được cung cấp.

Status mới liệt kê đủ 5 alias; chỉ key1 có bằng chứng API thành công được báo cáo. Xem [rà soát và ba lỗi còn tồn tại](REVIEW-20261027.md), gồm xử lý câu trả lời bị cắt, cooldown lẻ và lọc error.status.

Mục tiêu: Codex điều phối, Gemini tư vấn/phản biện qua API; tối đa 5 key được thành viên đồng ý cung cấp từ 5 project độc lập. Không cần Chrome, OAuth hay cổng dịch vụ mới.
