# Review (Khắt khe) — Parser Word/Text → Web

Tác giả: **GPT-5.2 (Codex CLI)**  
Ngày: 2025-12-24  
Phạm vi review: chủ yếu **`tools/auto_parse.py`** và **`tools/smart_parser.py`** (trái tim chuyển đổi Word/Text → `full_data.js`).

---

## 1) Tóm tắt điều hành (Executive Summary)

Hệ thống hiện tại **đã có đường hướng đúng**: dùng các “mốc” (header/index/section) trong file `.txt` để tự động tách phần và sinh `full_data.js` cho dashboard tĩnh. Tuy nhiên, ở trạng thái hiện tại, parser **chưa đạt tiêu chuẩn ổn định lâu dài** vì:

1. **Độ tin cậy chưa đạt**: với dữ liệu mẫu `reports/txt/baocao_full.txt`, `tools/auto_parse.py` chỉ parse thành công **8/16** mục; fail toàn bộ nhóm ngành: `VNREAL`, `VNIT`, `VNHEAL`, `VNFIN`, `VNENE`, `VNCONS`, `VNMAT`, `VNCOND`.  
2. **Hiệu năng kém theo cấu trúc thuật toán**: file được đọc và quét regex lặp lại nhiều lần (đặc biệt theo số index × số section), không scale tốt khi report dài hơn hoặc số pattern tăng.
3. **Thiết kế output “string JS” thiếu an toàn/định dạng**: ghép chuỗi JS/HTML bằng template literals mà không escape đầy đủ; có nguy cơ lỗi cú pháp, HTML lỗi, hoặc injection (dù nguồn từ AI).
4. **Thiếu kiểm thử & quan sát (observability)**: không có unit tests / golden tests / benchmark; khi fail khó biết vì sao (header không match? section không match? slice boundary sai?).

Kết luận khắt khe: **parser cần tái cấu trúc nhẹ nhưng đúng hướng** (1-pass tokenize + render) để đạt ổn định và hiệu năng.

---

## 2) Điểm mạnh hiện có

- **Workflow rõ ràng**: `Word → txt → tools/auto_parse.py → full_data_new.js → replace full_data.js → mở dashboard`.
- **Tư duy “tolerant parsing”**: section patterns dạng fuzzy regex (`XU.*HƯỚNG.*GIÁ`, …) giúp chịu được sai khác spacing/case.
- **Tách được phạm vi “overview”**: `parse_overview_smart()` tránh match nhầm index trong đoạn coverage.
- **Cấu trúc repo sạch dần**: đã gom `reports/`, `docs/`, `tools/` giúp giảm rối.

---

## 3) Vấn đề nghiêm trọng (P0) — cần sửa trước khi mở rộng

### P0.1 — Parser đọc file lặp lại 16 lần (wasteful I/O + CPU)
Trong `tools/auto_parse.py`, mỗi index gọi `parse_smart(filepath, ...)` và `parse_overview_smart(filepath)`; cả hai đều `open(...).read()` → **đọc toàn bộ file lặp 16 lần**.

Hậu quả:
- Chậm không cần thiết (I/O + decode UTF-8 lặp).
- Tốn RAM/GC, đặc biệt khi report lớn.

Mức ưu tiên: **cao nhất**, vì cải thiện hiệu năng “rẻ” và giảm nhiều rủi ro.

### P0.2 — Thuật toán tìm section là O(P²) và dễ sai boundary
Trong `parse_smart()`:
- Mỗi `pattern` dùng `re.search()` trên toàn `index_content` (P lần).
- Với mỗi match, lại loop toàn bộ pattern để tìm “section tiếp theo” bằng `re.search()` trên substring (P lần) → **O(P²)** tìm boundary.

Hậu quả:
- Chậm khi thêm nhiều section/pattern.
- Dễ cắt nhầm nếu pattern overlap, hoặc nếu một section header xuất hiện trong body.

### P0.3 — Cơ chế báo lỗi không nhất quán (có thể làm “false success”)
Các hàm trả lỗi theo nhiều kiểu:
- `parse_smart()` (missing index): `"# LỖI: ..."`
- `generate_js_object_smart()` (no sections): `"    # LỖI: ..."` (có indent)

Trong `tools/auto_parse.py` lại kiểm tra `not js_obj.startswith("# LỖI")`, nên case `"    # LỖI..."` **không bị coi là lỗi ngay**, dẫn tới đường đi logic “WARNING invalid structure” thay vì “FAILED vì không parse được section”.

Đây là lỗi thiết kế API (string protocol), làm giảm khả năng quan sát và dễ hiểu nhầm “parser OK”.

### P0.4 — Output HTML/list không chuẩn (format_content_smart)
`format_content_smart()` thay bullet marker bằng `<li>` nhưng:
- Không tạo `<ul>`/`</ul>`
- Không tạo `</li>`
- Sau đó lại bọc `<p>...</p>` và collapse whitespace → rất dễ thành HTML “rác”, render tuỳ browser.

Khi dữ liệu tăng/đa dạng, phần hiển thị sẽ xuống cấp hoặc khó debug.

### P0.5 — Rủi ro vỡ JS do template literal không escape đầy đủ
Output JS dùng template literal (backticks) cho `content: \`...\``:
- Nếu text có ký tự backtick `` ` `` → vỡ cú pháp JS.
- Nếu text có `${...}` → có thể bị JS interpolation ngoài ý muốn.
- Nếu text có `</script>` (hiếm) → có thể phá DOM khi nhúng script.

Nguồn AI không đảm bảo “không có backticks”, nên đây là rủi ro thực tế.

---

## 4) Vấn đề quan trọng (P1) — ảnh hưởng ổn định dài hạn

### P1.1 — Tìm header index chưa cover format “ngành” (nguyên nhân fail 8/16)
`_find_index_header()` hiện match tốt các dạng:
- `PHẦN ...: ... VNINDEX`
- `1. Chỉ số VN30`
- `PHÂN TÍCH CHỈ SỐ VN30`

Nhưng nhiều report (đặc biệt phần ngành) hay có dạng:
- `1. VNREAL - Bất động sản` (không có chữ “Chỉ số”)

Điều này giải thích vì sao hiện tại fail toàn bộ nhóm ngành trong dữ liệu mẫu.

### P1.2 — Không có fallback cho “THÔNG TIN CHUNG”/đoạn mở đầu
Nhiều index có block “Giá hiện tại/Thay đổi/Khối lượng…” trước khi tới “Xu hướng giá”. Nếu report không có tiêu đề “THÔNG TIN CHUNG”, parser có thể bỏ mất phần mở đầu (tùy format).

### P1.3 — Validation output đang là heuristic chuỗi
`tools/auto_parse.py` kiểm tra `"sections:" in js_obj and "title:" in js_obj` để coi là hợp lệ. Đây là heuristic yếu:
- false positive nếu content chứa chuỗi đó
- false negative nếu format thay đổi nhỏ

### P1.4 — Không có “lý do fail” theo index
Hiện fail chỉ báo `❌ FAILED` mà không phân loại:
- không tìm thấy header index
- tìm thấy index nhưng không tìm thấy section
- section boundary sai

Không có log/trace khiến việc nâng độ robust tốn thời gian.

---

## 5) Đề xuất cải thiện hiệu năng parse (ưu tiên theo ROI)

### Đề xuất A (ROI cao nhất): đọc file 1 lần, parse nhiều lần
Thiết kế lại API:
- `parse_overview_smart(content: str) -> ParsedIndex`
- `parse_index_smart(content: str, index_name: str, index_code: str) -> ParsedIndex`
- `tools/auto_parse.py` đọc file **1 lần** rồi truyền `content` xuống.

Tác động:
- Giảm I/O ~16×.
- Giảm overhead decode UTF-8.

### Đề xuất B: “1-pass header indexing” để cắt index_content O(N)
Thay vì với mỗi index lại search từ đầu:
1. Chạy một pass `re.finditer()` để tìm tất cả header của các index theo nhiều biến thể.
2. Sort theo vị trí xuất hiện.
3. Slice `content[start:end]` cho từng index.

Tác động:
- Tìm boundary chính xác hơn.
- O(N) + O(K log K) thay vì O(K*N) (K = số index).

### Đề xuất C: Tokenize section headers theo thứ tự xuất hiện (thay O(P²))
Thay loop pattern-nested:
- Dùng một regex “hợp nhất” (union) với named group/ID cho các section headers.
- `finditer` → danh sách (section_id, start_pos, end_pos_header).
- Slice theo vị trí kế tiếp.

Tác động:
- O(N) trên đoạn index_content.
- Tránh cắt nhầm do overlap.

### Đề xuất D: Precompile regex + normalize text
Precompile `re.compile(..., flags)` cho:
- index header patterns
- section header patterns
Normalize input trước khi parse:
- chuẩn hoá Unicode (NFC)
- thay “weird whitespace” (U+2028, U+000c formfeed) thành `\n`

Tác động:
- tăng tốc và tăng độ ổn định match.

### Đề xuất E: Escape an toàn cho JS template literal
Tạo hàm:
- escape backslash `\\`
- escape backtick ``\` ``
- escape `${` → `\${`

Đây là bắt buộc nếu muốn parser “chịu được AI text” trong dài hạn.

---

## 6) Đề xuất cải thiện độ tin cậy (correctness/robustness)

### Đề xuất F: Chuẩn hoá format header index (cover ngành)
Mở rộng `_find_index_header()` và `_find_next_index_header_start()` để match thêm dạng:
- `^\s*\d+\.\s*(VN[A-Z0-9]+)\b.*$` (không cần “Chỉ số”)
- `^\s*(VNREAL|VNIT|...)\s*-\s*.+$` (nếu AI dùng “CODE - Name”)

### Đề xuất G: “prelude → THÔNG TIN CHUNG”
Nếu tìm thấy section đầu tiên (ví dụ `XU HƯỚNG GIÁ`) ở vị trí `pos_first`,
thì mọi text từ đầu index_content đến `pos_first` (sau khi trim) có thể là section `THÔNG TIN CHUNG`.

### Đề xuất H: Tách extraction và rendering
Không return “string JS” từ parser nữa.
Return cấu trúc Python (list/dict) rồi render ra JS ở 1 nơi:
- validate được schema (title str, sections list, …)
- dễ test hơn
- dễ đổi output format (JSON/JS) sau này

### Đề xuất I: Thông báo lỗi có cấu trúc
Thay `"# LỖI"` bằng:
- exception có type (IndexHeaderNotFound, NoSectionsFound, …)
hoặc return `(ok: bool, data|error)` để auto_parse log rõ.

---

## 7) Kế hoạch kiểm thử & benchmark (để dự án ổn định lâu dài)

### 7.1 Golden tests (khuyến nghị)
- Tạo thư mục `tests/fixtures/` chứa 2–3 file `.txt` đại diện (AI format A/B/C).
- Kỳ vọng output:
  - số index parse được
  - mỗi index có tối thiểu N section
  - output JS pass `node --check`
- So sánh snapshot (golden file) hoặc so sánh schema + một vài string mẫu.

### 7.2 Benchmark (đơn giản nhưng hiệu quả)
- Đo thời gian parse trên 1–3 report (small/medium/large).
- KPI gợi ý:
  - parse 1 report 2–5MB < 1s–2s (tuỳ máy)
  - 0 lần đọc file lặp
  - 0 regex nested-quadratic theo số section

### 7.3 Runtime validation
Sau khi generate:
- `node --check full_data_new.js`
- Mở `test_all_16.html` trên GitHub Pages để check key set (overview + 15 indices).

---

## 8) Lộ trình đề xuất (thực dụng)

**Phase 1 (1–2 ngày):**  
- Refactor đọc file 1 lần + escape template literal + lỗi có cấu trúc (A + E + I)

**Phase 2 (2–4 ngày):**  
- 1-pass index boundary + section tokenizer (B + C)  
- Fix case ngành (F) để đạt 16/16 trên report mẫu

**Phase 3 (liên tục):**  
- Golden tests + benchmark (7.x)  
- Chuẩn hoá output (H), cải thiện HTML formatting (P0.4)

---

## 9) Kết luận

Ở trạng thái hiện tại, parser **đủ để demo** và chạy với một số format quen thuộc, nhưng **chưa đủ chuẩn “trái tim” cho hệ thống dài hạn** (vì fail 8/16 trên dữ liệu mẫu và có các vấn đề P0 về hiệu năng/escape/HTML).

Nếu triển khai các đề xuất Phase 1–2, hệ thống sẽ:
- nhanh hơn rõ rệt (giảm quét/đọc lặp)
- ổn định hơn (cover ngành + boundary chính xác)
- dễ bảo trì/mở rộng (test + structured errors)

— **GPT-5.2 (Codex CLI)**
