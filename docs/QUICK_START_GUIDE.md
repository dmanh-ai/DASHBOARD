# Quick Start Guide (Updated)

Mục tiêu: tạo data mới (`full_data_new.js`) từ file báo cáo `.txt`, kiểm tra syntax, rồi thay `full_data.js`.

```bash
# 1) Convert Word → Text (macOS)
textutil -convert txt -stdout "reports/word/BaoCao_MOI.docx" > reports/txt/baocao_moi.txt

# 2) Generate data
python3 tools/auto_parse.py reports/txt/baocao_moi.txt full_data_new.js

# 3) Verify + replace
node --check full_data_new.js
cp full_data_new.js full_data.js

# 4) Mở dashboard
open index.html
```

Ghi chú:
- Script chính: `tools/auto_parse.py`, `tools/smart_parser.py`
- Script cũ: `tools/legacy/`
