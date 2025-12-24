# 📋 HƯỚNG DẪN SỬ D DỤNG PARSER CHO WORD MỚI

## ⚠️ VẤN ĐỀ VỚI PARSER CŨ

### Rủi ro khi file Word thay đổi:

1. **Hardcoded Line Numbers** ❌
   ```python
   start_line=224,  # ❌ Nếu Word mới khác → SAI!
   ```

2. **Format Rigid** ❌
   - Phải đúng: `"XU HƯỚNG GIÁ"`
   - Sai: `"XU HƯỚNG GIÁ "` (có space)

3. **Cấu trúc cố định** ❌
   - Thêm/bớt sections → Lỗi
   - Thay đổi tên → Không match

## ✅ GIẢI PHÁP: SMART PARSER

### Tính năng mới:

1. ✅ **Auto-detect vị trí index**
   - Không cần hardcode line numbers
   - Tự động tìm "VN30", "VN100", etc.

2. ✅ **Flexible section detection**
   - Tolerates với spacing, format variations
   - Regex patterns thông minh

3. ✅ **Auto-extract content**
   - Tự động xác định boundaries
   - Format HTML tự động

4. ✅ **Error handling**
   - Báo lỗi rõ ràng nếu không tìm thấy index
   - Skip sections thay vì crash

## 🚀 CÁCH SỬ DỤNG KHI CÓ WORD MỚI:

### Bước 1: Convert Word → Text
```bash
# Mac (sử dụng textutil)
textutil -convert txt "BaoCao_20251226.docx" -stdout > baocao_new.txt

# Hoặc copy paste từ Word vào text editor
```

### Bước 2: Chạy Smart Parser
```python
#!/usr/bin/env python3
from smart_parser import parse_smart

filepath = 'baocao_new.txt'

# Parse tất cả indices - không cần line numbers!
indices = [
    ('VNINDEX', 'vnindex'),
    ('VN30', 'vn30'),
    ('VN100', 'vn100'),
    ('VNMIDCAP', 'vnmidcap'),
    ('VNREAL', 'vnreal'),
    ('VNIT', 'vnit'),
    ('VNHEAL', 'vnheal'),
    ('VNFIN', 'vnfin'),
    ('VNENE', 'vnene'),
    ('VNCONS', 'vncons'),
    ('VNMAT', 'vnmat'),
    ('VNCOND', 'vncond'),
    ('VNSML', 'vnsml'),
    ('VNFINSELECT', 'vnfinselect'),
    ('VNDIAMOND', 'vndiamond')
]

# Generate full_data.js
with open('full_data.js', 'w', encoding='utf-8') as f:
    f.write("const FULL_DATA = {\n")

    for index_name, index_code in indices:
        print(f"🔄 Processing {index_name}...")
        js_obj = parse_smart(filepath, index_name, index_code)

        if js_obj and not js_obj.startswith("# LỖI"):
            f.write(js_obj + ",\n")
            print(f"✅ {index_name} done!")
        else:
            print(f"❌ {index_name} FAILED!")

    f.write("};\n")

print("✅ full_data.js generated successfully!")
```

### Bước 3: Kiểm tra
```bash
# Verify syntax
node --check full_data.js

# Test dashboard
open COMPLETE.html
```

## 🛡️ BẢO VỆ THÊM:

### 1. Validation Files
```python
def validate_parsed_data(index_data, expected_sections=14):
    """Validate parsed data has expected structure"""

    # Check section count
    if len(index_data['sections']) < expected_sections * 0.5:  # At least 50%
        print(f"⚠️ WARNING: Only {len(index_data['sections'])} sections found")

    # Check required sections
    required = ['THÔNG TIN', 'XU HƯỚNG', 'KHUYẾN NGHỊ']
    for req in required:
        found = any(req in s['title'] for s in index_data['sections'])
        if not found:
            print(f"⚠️ WARNING: Missing required section: {req}")
```

### 2. Backup Trước Khi Parse
```bash
# Backup current working version
cp full_data.js full_data_backup_$(date +%Y%m%d).js
```

### 3. Incremental Testing
```bash
# Test từng index trước khi merge all
python test_parse_one.py --index vn30
python test_parse_one.py --index vn100
# ... sau đó merge
```

## 📊 SO SÁNH PARSER CŨ vs MỚI:

| Tính năng | Parser Cũ | Smart Parser |
|-----------|-----------|--------------|
| Line numbers | Hardcoded ❌ | Auto-detect ✅ |
| Format tolerance | Rigid ❌ | Flexible ✅ |
| Section detection | Exact match ❌ | Regex fuzzy ✅ |
| Error handling | Crash ❌ | Graceful ✅ |
| Maintains ability | Khó ❌ | Dễ ✅ |

## 🎯 KHUYẾN:

1. **Luôn backup** trước khi parse file mới
2. **Test từng index** trước khi merge tất cả
3. **Verify syntax** với `node --check`
4. **Visual check** trong browser
5. **Keep old parser** as fallback if needed

## 📞 SUPPORT:

Nếu gặp lỗi khi parse file Word mới:
1. Gửi sample của file mới
2. Mô tả lỗi cụ thể (index nào? section nào?)
3. Cung cấp expected output vs actual output

Smart Parser sẽ được cải thiện dần dựa trên feedback! 🚀
