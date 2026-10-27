# AI NAS Lab

Nguồn bàn giao cho Codex phối hợp Gemini API trên NAS. Cập nhật 27/10/2026 (Asia/Ho_Chi_Minh).

## Đọc trước

1. [AGENTS.md](AGENTS.md): quy tắc tiếp quản.
2. [CURRENT-STATE.md](CURRENT-STATE.md): cấu hình và bằng chứng mới nhất.
3. [RUNBOOK.md](RUNBOOK.md): thao tác vận hành.

## Trạng thái

Theo báo cáo Codex trên NAS do người dùng cung cấp trong hội thoại ngày 27/10: `gemini-task` gọi API thành công bằng key1 và `gemini-3.5-flash-lite`; có câu trả lời thử OK và tác vụ phân tích thực tế. Phiên ChatGPT ghi tài liệu này không trực tiếp SSH hoặc đọc mã wrapper trên NAS.

Repo hiện lưu tài liệu bàn giao, **chưa chứa mã nguồn wrapper hoặc bộ test**. Không dùng tài liệu như bằng chứng đã sao lưu/khôi phục được triển khai.

Mục tiêu: Codex điều phối, Gemini tư vấn/phản biện qua API; tối đa 5 key được thành viên đồng ý cung cấp từ 5 project độc lập. Không cần Chrome, OAuth hay cổng dịch vụ mới.
