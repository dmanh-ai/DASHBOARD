# Reports (Input Files)

Để tránh làm rối cấu trúc repo, hãy để file báo cáo ở đây:

- `reports/word/`: file Word gốc (`.docx`)
- `reports/txt/`: file text đã convert từ Word (`.txt`)

Workflow gợi ý:

```bash
# Convert Word → Text (macOS)
textutil -convert txt -stdout "reports/word/BaoCao_MOI.docx" > "reports/txt/baocao_moi.txt"

# Generate data
python3 tools/auto_parse.py "reports/txt/baocao_moi.txt" full_data_new.js

# Verify + replace
node --check full_data_new.js
cp full_data_new.js full_data.js
```
