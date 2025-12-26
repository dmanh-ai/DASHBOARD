# PARSING_REPORT.md (deprecated)

File report này thuộc workflow cũ (manual parsing + absolute paths).

Dùng thay thế:
- `README.md`
- `docs/GUIDE.md`
- `tools/auto_parse.py` (tạo `full_data_new.js` từ file `.txt`)

---

## Reliability notes (workflow hiện tại)

Mục tiêu: chuyển `BaoCao_YYYYMMDD_HHMMSS.docx` (từ `outputs/market/reports/`) → UI dashboard **ổn định**, không “đứt pipeline” khi Word thiếu một vài phần.

### Các rủi ro chính

1. **Report market không chứa đủ 16 index** (thường gặp ở report đời cũ / report lỗi phần tổng hợp).
2. **DOCX→TXT thay đổi formatting** (xuống dòng/ký tự control), khiến match section/header khó hơn.
3. **Template drift** (heading đổi nhẹ) làm parser miss `IndexHeader` hoặc `SectionHeader`.

### Guardrails đã áp dụng (UI GLM)

- `tools/auto_parse.py` luôn sinh đủ **16 keys** trong `FULL_DATA`.
  - Nếu một index không có trong báo cáo: sinh **placeholder section** với nội dung “không có dữ liệu trong báo cáo hôm nay” (không lấy dữ liệu cũ, không dùng report khác).
- Có **quality gate** để tránh update UI khi report quá lỗi:
  - Env: `UI_GLM_MIN_SUCCESS_ITEMS` (default `10`)
  - Nếu parse thành công < ngưỡng này → `auto_parse.py` exit non-zero → automation dừng (không update `full_data.js`).

### Chẩn đoán nhanh

```bash
# Convert 1 file BaoCao (market) sang txt rồi parse thử
textutil -convert txt -stdout ../outputs/market/reports/BaoCao_YYYYMMDD_HHMMSS.docx > reports/txt/tmp.txt
python3 tools/auto_parse.py reports/txt/tmp.txt /tmp/full_data_new.js
node --check /tmp/full_data_new.js
```
