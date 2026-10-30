# Vận hành Gemini Task

## Nhập/thay key

Trong SSH Termius Android trên NAS, chạy tương tác (không copyout vì cần nhập ẩn):

```sh
/home/admin/bin/gemini-task keys add key1
```

Chỉ nhập key, không nhập tên/project. Đổi alias thành key2…key5 để bổ sung. Chờ thông báo lưu thành công. Không gửi key vào chat. Đã đọc mã: nếu alias tồn tại, lệnh thông báo thay credential rồi ghi key mới và reset invalid. Lệnh còn reset group/priority mọi alias về mặc định theo số; chưa kiểm thử tương tác thay key thật. Không cần nhập lại 5 key đang được status liệt kê.

## Kiểm tra giao diện và trạng thái

```sh
/home/admin/bin/copyout '
/home/admin/bin/gemini-task --help
/home/admin/bin/gemini-task status
'
```

Lưu ý status có tạo/ghi state/lock qua state_snapshot, dù không gọi API. Không dùng cat để in keys.json. status không được lộ key. Các option ngoài --key và đầu vào stdin/file cần kiểm tra --help, không đoán tên cờ.

## Gọi thử ngắn

```sh
/home/admin/bin/copyout '
printf "%s\\n" "Chỉ trả lời đúng một dòng: OK" | /home/admin/bin/gemini-task --key key1
'
```

Gọi tự động thì bỏ --key key1. Với --key chỉ định, wrapper không chuyển nguồn. Lời gọi có thể tiêu thụ quota hoặc có phí theo project; không bật billing tự động.

## Phối hợp

Người dùng giao việc cho Codex trên NAS: “Làm việc này, nhờ Gemini phản biện trước khi chốt.” Codex đưa bối cảnh tối thiểu qua gemini-task, kiểm tra stdout và exit code, tự đánh giá phản hồi. Không truyền token/mật khẩu/file credential. Không cho Gemini tool hoặc quyền ghi file. Tối đa 2 lượt tư vấn mỗi nhiệm vụ mặc định.

### Chia luồng an toàn và đo hiệu quả

- Trước khi chạy đồng thời, đọc `--help` và kiểm tra wrapper có serialize model call hay khóa trạng thái dùng chung. Chỉ song song hóa câu hỏi độc lập; giữ mỗi luồng một key tường minh nếu cần cô lập quota.
- Gửi cùng phạm vi/source nhưng không gửi dữ liệu người dùng, credential, session, log riêng hoặc ảnh có nội dung riêng. Gemini chỉ tư vấn; Codex xác minh nhận định trên code/test trước khi sửa.
- Ghi thời điểm bắt đầu/kết thúc từng luồng, exit code, lỗi/retry và số luồng đồng thời. Thời gian chờ của một batch song song là thời gian tường trình của batch, không phải tổng thời lượng các luồng.
- Đánh giá lợi ích bằng phát hiện cụ thể được xác minh và áp dụng. Ghi riêng nhận định sai/trùng lặp/bác bỏ; không suy ra tiết kiệm thời gian nếu không có baseline tương đương. Nếu review chỉ nhận mô tả screenshot thì không gọi đó là đã xem screenshot.
- Chỉ dùng lượt follow-up khi code hoặc bằng chứng liên quan thay đổi; thu hẹp prompt vào phần đó thay vì lặp lại review toàn bộ.

## Khi lỗi

- Chưa cấu hình key: từng gặp exit 78, stdout rỗng. Nhập key và chờ lưu thành công; không suy ra key bị Google từ chối.
- Timeout tổng: từng gặp exit 124; cần phân biệt chưa nhận headers với treo đọc body/retry. Không chỉ tăng timeout liên tục.
- 429: kiểm tra cooldown, Retry-After/retryDelay và quota-group; không coi key cùng project là quota riêng.
- 503: tối đa 2 retry bổ sung cùng key; không xoay 5 key cho cùng model. Không coi 503 là hết quota hoặc key sai.
- models.list 200 chưa đủ: cần generateContent có câu trả lời thật.
- Hết mọi nguồn: báo lỗi, không giả lập kết quả và không retry vô hạn.

## Khôi phục/gỡ

Đã có bản nguồn nguyên trạng tại src/gemini-task; checksum và giới hạn kiểm chứng trong REVIEW-20261027.md. Bộ tests/test_baseline.py là test mới chạy offline, không phải test lịch sử NAS. Khi phục hồi cần kiểm tra SHA-256 và đặt quyền thực thi; chưa thử phục hồi trên NAS và không lưu key store vào Git. Source baseline còn ba hành vi lỗi đã tái hiện; không coi đây là bản đã sửa. Trước khi gỡ cần xác minh file/symlink và nguồn bản gốc trên NAS; chỉ gỡ thành phần gemini-task riêng, không xóa Node/CLI/credential hoặc sửa dịch vụ khác tự ý.

## Nguồn chính thức để kiểm tra lại

- https://ai.google.dev/gemini-api/docs/models
- https://ai.google.dev/gemini-api/docs/pricing
- https://ai.google.dev/gemini-api/docs/rate-limits
- https://ai.google.dev/gemini-api/docs/api-key
- https://ai.google.dev/gemini-api/docs/api-errors

Các liên kết này là nguồn tham khảo, không thay bằng chứng runtime và không phải xác nhận lại chính sách OAuth ở thời điểm đọc.
