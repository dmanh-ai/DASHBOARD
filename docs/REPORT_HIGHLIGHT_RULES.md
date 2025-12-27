# Report Highlight Rules (Word → UI)

Mục tiêu: từ text (convert từ Word) → UI có “điểm nhấn” rõ ràng, ổn định theo thời gian, đặc biệt hiệu quả trong dark theme.

Nguồn áp dụng hiện tại:
- `scripts/content_formatter.js` (client-side) là nơi tự động “nhận diện” các dòng quan trọng và bọc vào các callout boxes.

## Nguyên tắc

1) **Chỉ highlight theo “dòng/đoạn 1 dòng”** để tránh phá cấu trúc list/paragraph dài và giảm false-positive.
   - Nghĩa là: chỉ các paragraph có đúng 1 dòng (sau normalize) mới được nâng cấp thành box.
2) **Ưu tiên “signal” cao** (headline/summary/action/risk) hơn các dòng mô tả.
3) **Dark-theme first**: dùng token (`--success`, `--danger`, `--warning`, `--primary`, `--indigo`, `--lg-*`) để đảm bảo đổi theme không làm mất tương phản.
4) **Không flood UI**: giới hạn số box được tạo ra cho mỗi section (mặc định tổng `10`), tránh “highlight mọi thứ”.

## Thứ tự ưu tiên (priority)

Mặc định chỉ highlight **các dòng sát với kết luận** (để UI không bị “đậm đặc”):

1. **Kết luận ngắn**: `Kết luận ngắn:` → `conclusion-box`
2. **Kết luận**: `Kết luận:` → `conclusion-box`
3. **Hành động/khuyến nghị**: `Ý nghĩa/Hành động:`, `Ý nghĩa:`, `Hành động đề xuất:` và header `Khuyến Nghị Vị Thế` → `action-box`
4. **Rủi ro/cảnh báo**: `Rủi ro:`, `Cảnh báo rủi ro:` → `risk-box`
5. **Điều kiện phản biện**: `Điều kiện khiến kết luận sai:`, `Điều kiện sai:` hoặc `3 Điều kiện...` → `conditions-box`

## Output classes

Các class này được style trong `DASHBOARD_V3.html`:
- `hero-box`, `conclusion-box`, `action-box`, `risk-box`, `conditions-box`, `levels-box`, `scenario-box`, `confidence-box`, `metrics-box`, `evidence-box`

## Lưu ý về false-positive

- “ALL CAPS” được kiểm tra theo **chữ cái** (Unicode) và giới hạn độ dài để tránh biến thành “highlight everything”.
- Không highlight các dòng bắt đầu bằng `PHẦN I/II/III...` như hero headline.
- Không dùng `%` để suy ra `confidence-box` (vì % xuất hiện quá nhiều trong số liệu); chỉ dùng khi có `Mức độ tự tin` / `Độ tin cậy` / `x/10`.
- `levels-box` ưu tiên các dòng `Hỗ trợ/Kháng cự/H1/R1...` (không auto-match theo MA/VWAP để tránh quá nhiều).
