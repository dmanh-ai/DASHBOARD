# Kế Hoạch Cải Tiến Parser Word/Text → Web (Tối đa hoá độ ổn định & điểm chất lượng)
## Dự án: Market Overview Dashboard Parser

**Ngày cập nhật:** 2025-12-25  
**Dựa trên:** `review.md` (review khắt khe cho `tools/auto_parse.py`, `tools/smart_parser.py`)  
**Trạng thái:** Draft — sẵn sàng triển khai theo Phase  

---

## 1) Mục tiêu & Definition of Done (DoD)

### Mục tiêu kỹ thuật (bắt buộc)
- Parse thành công **16/16 items** (overview + 15 indices) trên fixture chính `reports/txt/baocao_full.txt`.
- Thời gian parse **< 2 giây** cho báo cáo 2–5MB (trên máy dev).
- File input được đọc **1 lần** (không lặp I/O theo index).
- Output JS **không thể vỡ cú pháp** vì dữ liệu (backtick, `${}`, `\u2028/\u2029`, quotes, backslash…).
- Fail phải **có phân loại** (không còn “false success” do protocol string).

### Quality gates (để “điểm tối đa”)
- Có **golden tests** (snapshot hoặc schema+assertions) cho ít nhất 2 fixtures: “full” + “industry”.
- Có **benchmark script** chạy được bằng stdlib (không phụ thuộc `psutil`).
- Parser tách bạch: **extract (data)** ≠ **render (JS)**.
- Log/summary cuối cùng cho mỗi run: success-rate, top error types, indices fail.

### Non-goals (để tránh scope creep)
- Không cố “hiểu ngữ nghĩa” sâu (LLM reasoning) — chỉ robust text parsing + rendering an toàn.
- Không đổi UI/dashboard; chỉ đảm bảo dữ liệu `full_data*.js` đúng và ổn định.

---

## 2) Hiện trạng (tóm tắt)

- Đã đúng hướng: tolerant regex, có parse overview.
- Vấn đề P0 từ `review.md`:
  - Đọc file lặp ~16 lần (chậm).
  - Section boundary O(P²), dễ sai khi tăng patterns.
  - Protocol lỗi bằng string `# LỖI` không nhất quán → “false success”.
  - HTML formatting không hợp lệ (li/ul), dễ render lỗi.
  - Template literal không escape đầy đủ → có thể vỡ JS.
- Vấn đề P1: nhóm ngành thường ở format `1. VNREAL - Bất động sản` nên `_find_index_header()` fail.

---

## 3) Nguyên tắc thiết kế (để đạt ổn định lâu dài)

1. **Read once**: `auto_parse.py` đọc file 1 lần → truyền `content` xuống.
2. **Normalize trước khi regex**: chuẩn hoá Unicode (NFC), newline/whitespace “lạ”, và strip BOM.
3. **Extract → Validate → Render**:
   - Extract trả về cấu trúc Python chuẩn (dict/list).
   - Validate schema + invariants (title, sections, tối thiểu 1 section, boundary hợp lệ…).
   - Render JS dùng **`json.dumps`** cho strings để auto-escape, tránh template literal khi không cần.
4. **1-pass tokenization theo vị trí**:
   - Index boundary: 1 `finditer` (union regex) trên toàn file.
   - Section boundary: 1 `finditer` (union regex) trên `index_content`.
5. **Observability first**: mỗi fail phải có `error_type`, `message`, và (tuỳ chọn) debug context (header line matched, pattern kind, start/end).

---

## 4) Kế hoạch theo Phase (ưu tiên theo ROI)

| Phase | Thời gian | Priority | Mục tiêu | Rủi ro |
|------:|-----------|----------|----------|--------|
| **Phase 1** | 1–2 ngày | P0 | An toàn output + read-once + error model + HTML hợp lệ + normalize | Thấp |
| **Phase 2** | 2–4 ngày | P0/P1 | O(N) boundary detection + cover ngành 16/16 + giảm false match | Trung bình |
| **Phase 3** | 2–3 ngày | P1/P2 | Golden tests + benchmark + tách parser/renderer + cleanup | Thấp |

---

## 5) Phase 1 — Nền tảng an toàn & giảm rủi ro (P0)

### Task 1.1 — Read file 1 lần (API refactor)
**File ảnh hưởng:** `tools/auto_parse.py`, `tools/smart_parser.py`  

**Thay đổi đề xuất:**
- `auto_parse.py`: đọc `content = Path(input_txt).read_text(encoding="utf-8")` đúng 1 lần.
- Đổi API:
  - `parse_overview_smart(filepath)` → `parse_overview_smart(content: str) -> ParsedResult`
  - `parse_smart(filepath, index_name, index_code)` → `parse_index(content: str, index_name: str, index_code: str) -> ParsedResult`

**Success criteria:**
- [ ] `open()/read_text()` chỉ xảy ra 1 lần trong `parse_all_indices()`.
- [ ] Output vẫn sinh được `full_data_new.js`.

---

### Task 1.2 — Chuẩn hoá error model (loại bỏ “string protocol”)
**File ảnh hưởng:** `tools/smart_parser.py`, `tools/auto_parse.py`

**Khuyến nghị:** kết hợp “exceptions nội bộ” + “structured result ở public API” để vừa clean code vừa dễ batch aggregate.

**Data model gợi ý:**
```python
from dataclasses import dataclass
from typing import Literal, Optional

Status = Literal["success", "error"]

@dataclass
class ParseError:
    error_type: str   # "index_header_not_found" | "no_sections" | "invalid_boundaries" | ...
    message: str
    debug: Optional[dict] = None

@dataclass
class ParsedIndex:
    key: str          # "vn30"
    title: str
    sections: list[dict]  # [{icon,title,content_html,alert?}, ...]

@dataclass
class ParsedResult:
    status: Status
    data: Optional[ParsedIndex] = None
    error: Optional[ParseError] = None
```

**Mẫu “hybrid” đề xuất:**
```python
class ParserError(Exception):
    error_type: str
    def to_error(self) -> ParseError: ...

class IndexHeaderNotFound(ParserError): ...
class NoSectionsFound(ParserError): ...

def _parse_index_internal(content: str, index_name: str, index_code: str) -> ParsedIndex:
    # raise ParserError subclasses khi fail
    ...

def parse_index(content: str, index_name: str, index_code: str) -> ParsedResult:
    try:
        return ParsedResult(status="success", data=_parse_index_internal(content, index_name, index_code))
    except ParserError as e:
        return ParsedResult(status="error", error=e.to_error())
```

**Nguyên tắc dùng trong repo:** chỉ `tools/auto_parse.py` (batch boundary) cần check `result.status`; phần còn lại dùng exceptions nội bộ để tránh “if error” rải rác.

**Success criteria:**
- [ ] Không còn case `"# LỖI"` với indent gây “false success”.
- [ ] Summary báo được: not_found vs no_sections vs invalid_output.

---

### Task 1.3 — Normalize input text trước parse (tăng hit-rate + giảm bug Unicode)
**File ảnh hưởng:** `tools/smart_parser.py`

**Thêm hàm:**
- NFC normalize (`unicodedata.normalize("NFC", text)`).
- Chuẩn newline: thay `\r\n`/`\r` → `\n`.
- Thay `\u2028/\u2029` → `\n` (hoặc giữ nhưng đảm bảo render escape).
- Strip BOM `\ufeff`.
- (Tuỳ chọn) collapse khoảng trắng chỉ cho **regex matching**, nhưng vẫn giữ bản gốc để render.

**Success criteria:**
- [ ] Không giảm accuracy hiện tại.
- [ ] Giảm fail do “kí tự lạ” (nếu có) khi chạy fixtures.

---

### Task 1.4 — HTML formatting hợp lệ (fix P0.4)
**File ảnh hưởng:** `tools/smart_parser.py` (`format_content_smart`)

**Yêu cầu tối thiểu:**
- Bullets phải bọc trong `<ul><li>...</li></ul>`.
- Paragraphs bọc `<p>...</p>` đúng.
- Quyết định rõ “HTML allowlist”:
  - Nếu content là plain-text → escape `<>&"` trước khi wrap.
  - Nếu content đã “có HTML” (hiện đang inject `<strong>`) → ít nhất đảm bảo cấu trúc list/paragraph hợp lệ.

**Success criteria:**
- [ ] Render ổn định trên browser, không HTML “rác”.
- [ ] Không tự sinh `<li>` trần không có `</li>`/`<ul>`.

---

### Task 1.5 — Render JS an toàn (không vỡ cú pháp vì dữ liệu)
**File ảnh hưởng:** `tools/smart_parser.py` (renderer), hoặc file mới `tools/renderer.py`

**Khuyến nghị mạnh:** tránh template literal cho data string; dùng `json.dumps` cho mọi string:
```python
import json

def js_str(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)
```

Sau đó render:
- `title: ${js_str(title)}`
- `content: ${js_str(content_html)}`
- `sections: ${json.dumps(sections, ensure_ascii=False)}`

**Success criteria:**
- [ ] `node --check full_data_new.js` luôn pass với test cases có `` ` ``, `${}`, backslash, quotes, `\u2028/\u2029`.
- [ ] Không còn phụ thuộc vào escape-template-literal thủ công để “chống vỡ JS”.

---

## 6) Phase 2 — O(N) algorithm & Coverage 16/16 (P0/P1)

### Task 2.1 — Index boundary detection bằng union regex (thực sự “1-pass”)
**File ảnh hưởng:** `tools/smart_parser.py`

**Vấn đề cần tránh:** “1-pass” nhưng lại `finditer` theo từng index/pattern (thực tế vẫn N×M).  
**Giải pháp:** build pattern động từ list code + precompile 1 lần + `finditer` 1 lần.

**Gợi ý pattern (minh hoạ):**
- Build:
  - `INDEX_CODES = ["VNINDEX", "VN30", "VNREAL", ...]`
  - `CODE_ALT = "|".join(map(re.escape, INDEX_CODES))`
- Precompile patterns once (anchor theo line để giảm false match):
```python
HEADER_PATTERN = re.compile(
    rf"^(?:PHẦN\\s+[IVXLC]+\\s*:.*\\b(?P<code>{CODE_ALT})\\b.*)$"
    rf"|^(?:\\d+\\.\\s*Chỉ\\s*số\\s+(?P<code2>{CODE_ALT})\\b.*)$"
    rf"|^(?:\\d+\\.\\s*(?P<code3>{CODE_ALT})\\b\\s*(?:-|—|:)?\\s*.*)$",
    re.MULTILINE | re.IGNORECASE,
)
```
- Khi iterate matches, unify code:
  - `code = m.group("code") or m.group("code2") or m.group("code3")`

**Rủi ro & mitigation (backtracking/độ dài pattern):**
- Giữ mỗi alternative càng “thẳng” càng tốt (tránh `.*` chồng chéo không cần thiết).
- Nếu regex vẫn khó kiểm soát: fallback plan B là scan theo dòng (O(N) lines) + 2–3 regex nhỏ/heuristics, dễ debug hơn.

**Chọn match “đúng” khi trùng lặp:**
- Gán `kind_priority` theo loại header (PHẦN/Chỉ số/Ngành/Bare code).
- Với cùng `code`, ưu tiên match có priority cao hơn và/hoặc xuất hiện sớm hợp lý.

**Success criteria:**
- [ ] Có `boundaries: dict[code] -> (start,end)` không overlap.
- [ ] Parse được nhóm ngành (VNREAL, VNIT, VNHEAL, VNFIN, VNENE, VNCONS, VNMAT, VNCOND).

---

### Task 2.2 — Section tokenizer O(N) bằng union regex + slicing theo match kế tiếp
**File ảnh hưởng:** `tools/smart_parser.py`

**Mục tiêu:** thay nested loop O(P²) bằng:
- `SECTION_RE = re.compile(r"^(?P<trend>... )|^(?P<volume>... )|...", re.M|re.I)`
- `matches = list(SECTION_RE.finditer(index_content))`
- slice `match_i.end() : match_{i+1}.start()`

**Bổ sung “prelude → THÔNG TIN CHUNG”:**
- Nếu section đầu tiên không phải INFO nhưng `index_content[:first_match.start()]` có nội dung đáng kể → tự gán section INFO.

**Success criteria:**
- [ ] Không còn nested loop “tìm section tiếp theo bằng re.search trên từng substring”.
- [ ] Ít nhất 1 section hợp lệ cho các indices có dữ liệu.

---

### Task 2.3 — Giảm false match & tăng độ bền boundary
**File ảnh hưởng:** `tools/smart_parser.py`

Checklist:
- Anchor regex theo line (`^...$` + `re.MULTILINE`) cho header/section.
- Ưu tiên match header nằm gần “đúng khu vực” (tránh match trong phần coverage ở đầu).
- Nếu header/section xuất hiện lại trong body, chỉ coi là header khi thỏa “dạng tiêu đề” (ví dụ có số thứ tự, hoặc nằm ở đầu dòng, hoặc có dấu `:` rõ).

**Success criteria:**
- [ ] Không “cắt nhầm” index_content vì match trong nội dung.
- [ ] 16/16 trên fixture chính, không regress.

---

## 7) Phase 3 — Tests, Benchmark, Refactor để ổn định dài hạn (P1/P2)

### Task 3.1 — Golden tests (ít nhất 2 fixtures)
**Tạo thư mục:** `tests/` (nếu repo chưa có)  
**Fixtures gợi ý:**
- `tests/fixtures/baocao_full.txt`
- `tests/fixtures/baocao_industry.txt` (hoặc cắt nhỏ từ report thật)

**Test tối thiểu nên có:**
- Parse overview có title + >= N sections.
- Parse all indices: đúng 16 keys, không key thiếu.
- Với mỗi index: `sections` không rỗng, các section title hợp lệ, `content_html` không vỡ.
- Output JS pass `node --check`.

---

### Task 3.2 — Benchmark (stdlib-only)
**File mới:** `tools/benchmark.py`

**Đo:**
- `time.perf_counter()` cho tổng thời gian parse.
- `tracemalloc` cho peak memory (tuỳ chọn).

**KPI mục tiêu:**
- Duration < 2s (2–5MB).
- Peak memory tăng < 100MB (tuỳ máy, dùng để phát hiện regression).

---

### Task 3.3 — Tách parser/renderer + validate schema
**Files đề xuất:**
- `tools/parser.py` (extract + normalize + tokenization)
- `tools/renderer.py` (render JS an toàn qua `json.dumps`)
- `tools/smart_parser.py` có thể giữ để tương thích, nhưng gọi sang module mới (hoặc migrate dần)

**Lợi ích:**
- Test parser trên dict dễ hơn test string JS.
- Dễ đổi output (JS → JSON) nếu cần.

---

## 8) Success metrics (có baseline & theo dõi regression)

| Metric | Baseline | Target |
|--------|----------|--------|
| Success rate | 8/16 | 16/16 |
| File reads | 16 | 1 |
| Section algorithm | O(P²) | O(N) |
| `node --check` | có thể fail | luôn pass |
| Tests | 0 | golden + smoke |
| Benchmark | 0 | có KPI + regression check |

---

## 9) Rủi ro & Mitigation

| Rủi ro | Ảnh hưởng | Mitigation |
|--------|-----------|------------|
| Regression vì refactor API | Cao | Làm Phase 1 theo từng task nhỏ + chạy smoke sau mỗi task |
| Union regex match “quá rộng” | Trung bình | Thêm priority + anchor + fixtures ngành + negative cases |
| Output đổi format ảnh hưởng dashboard | Trung bình | Giữ schema JS tương đương; chỉ thay cách escape/quote |
| Fixture không đại diện đủ biến thể AI | Trung bình | Thu thêm 2–3 report thật, tối thiểu 1 report “xấu” |

---

## 10) Checklist triển khai (để chạy mượt trong repo hiện tại)

- [ ] Chốt quyết định: structured result + renderer dùng `json.dumps`.
- [ ] Tạo fixture(s) và chạy baseline (lưu success-rate, danh sách indices fail, và thời gian parse hiện tại).
- [ ] Làm Phase 1 theo thứ tự: 1.1 → 1.2 → 1.3 → 1.4 → 1.5.
- [ ] Regression cadence: sau **mỗi task Phase 1** chạy `python tools/auto_parse.py ...` và `node --check full_data_new.js`.

---

## 11) Next steps (ngay sau khi phê duyệt)

1. Chốt interface `ParsedResult/ParsedIndex` + quyết định nơi render (giữ trong `smart_parser.py` hay tách `renderer.py`).
2. Thực hiện Phase 1 (Quick wins + safety), rồi mới sang Phase 2 (O(N) + 16/16).
