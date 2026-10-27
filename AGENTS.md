# Quy tắc tiếp quản AI NAS Lab

- Đọc README.md, CURRENT-STATE.md và RUNBOOK.md trước khi làm. Cấu hình runtime chỉ được coi là hiện hành sau khi kiểm tra trên host; ghi nguồn, thời điểm và giới hạn bằng chứng.
- Người dùng gọi là “đại ca”. Mọi bulk lệnh yêu cầu người dùng chạy trên NAS bọc bằng `/home/admin/bin/copyout 'COMMAND'`. Lệnh tương tác nhập key đưa riêng, giải thích ngắn.
- Codex điều phối, kiểm chứng và thực hiện. Gemini chỉ tư vấn/phản biện, không chạy tool hoặc sửa file. Mặc định tối đa 2 lượt hỏi Gemini mỗi nhiệm vụ; retry kỹ thuật phải có giới hạn riêng.
- Chỉ gửi bối cảnh cần thiết. Không truyền secret; không commit API key, credential OAuth, key store, log thô hoặc dữ liệu nhạy cảm. Không đọc key của ứng dụng khác.
- Không giả lập phản hồi Gemini khi API lỗi. Phân biệt kiểm thử mô phỏng, kiểm thử API thật và báo cáo do người dùng chuyển tiếp.
- Không coi models.list 200, TLS tốt hoặc --version là bằng chứng generateContent hoạt động.
- Không tự bật billing, đổi dịch vụ NAS, mở cổng hoặc dùng model đắt hơn. Không sửa bundle Gemini CLI thủ công.
- 5 key được khai báo thuộc 5 project độc lập; alias quota-group là giả định do người dùng xác nhận, không phải project đã được API xác minh. Hạn mức theo project/model, không theo số key.
- Giữ thay đổi local, đọc AGENTS áp dụng trong checkout host trước khi sửa. Không ghi đè tài liệu khác hoặc xóa credential tự ý.
- Sau thay đổi có ý nghĩa, cập nhật CURRENT-STATE.md: hành vi cuối, kiểm thử thực tế, điểm chưa xác minh và bước tiếp theo. Không chép toàn bộ hội thoại.
- Khi có quyền host, đưa bản nguồn wrapper đã rà secret và test vào repo này để version hóa; hiện chưa được sao lưu ở đây. Không tái tạo mã từ mô tả rồi gọi đó là bản đang chạy.
