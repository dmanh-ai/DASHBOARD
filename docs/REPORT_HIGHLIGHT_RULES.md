# Report Highlight Rules (Word → UI)

Mục tiêu: từ text (convert từ Word) → UI có “điểm nhấn” rõ ràng, ổn định theo thời gian, đặc biệt hiệu quả trong dark theme.

Nguồn áp dụng hiện tại:
- `scripts/content_formatter.js` (client-side) là nơi tự động “nhận diện” các dòng quan trọng và bọc vào các callout boxes.

## Nguyên tắc

1) **Chỉ highlight theo “dòng/đoạn 1 dòng”** để tránh phá cấu trúc list/paragraph dài và giảm false-positive.
   - Nghĩa là: chỉ các paragraph có đúng 1 dòng (sau normalize) mới được nâng cấp thành box.
2) **Ưu tiên “signal” cao** (headline/summary/action/risk) hơn các dòng mô tả.
3) **Dark-theme first**: dùng token (`--success`, `--danger`, `--warning`, `--primary`, `--indigo`, `--lg-*`) để đảm bảo đổi theme không làm mất tương phản.

## Thứ tự ưu tiên (priority)

1. **Hero**: headline 1 dòng (trong ngoặc kép hoặc ALL CAPS) → `hero-box`
2. **Kết luận ngắn**: `Kết luận ngắn:` → `conclusion-box`
3. **Kết luận**: `Kết luận:` → `conclusion-box`
4. **Hành động**: `Ý nghĩa/Hành động:`, `Ý nghĩa:`, `Hành động đề xuất:` → `action-box`
5. **Rủi ro**: `Rủi ro:`, `Cảnh báo rủi ro:` hoặc chứa keyword (Black Swan / RỦI RO LỚN / Tuyệt đối / cắt lỗ / stop-loss) → `risk-box`
6. **Điều kiện phản biện**: `Điều kiện khiến kết luận sai:`, `Điều kiện sai:` hoặc `3 Điều kiện...` → `conditions-box`
7. **Mức giá/level**: `Hỗ trợ:`, `Kháng cự:`, `Hỗ trợ then chốt:`, `Mức quan trọng cần theo dõi:` hoặc chứa marker (H1/R1/MA/VWAP/POC/Value Area/HVN) → `levels-box`
8. **Kịch bản**: `Kịch bản ...` hoặc chứa `Xác suất` → `scenario-box`
9. **Độ tin cậy**: `Mức độ tự tin:`, `Độ tin cậy:` hoặc có `7/10`, `%` → `confidence-box`
10. **Snapshot metrics**: `Độ rộng:` hoặc chứa `TRIN`, `A/D`, `Volume Ratio`, `52W` → `metrics-box`
11. **Dẫn chứng**: `Dẫn chứng:` → `evidence-box`

## Output classes

Các class này được style trong `DASHBOARD_V3.html`:
- `hero-box`, `conclusion-box`, `action-box`, `risk-box`, `conditions-box`, `levels-box`, `scenario-box`, `confidence-box`, `metrics-box`, `evidence-box`

## Lưu ý về false-positive

- “ALL CAPS” được kiểm tra theo **chữ cái** (Unicode) và giới hạn độ dài để tránh biến thành “highlight everything”.
- Không highlight các dòng bắt đầu bằng `PHẦN I/II/III...` như hero headline.

