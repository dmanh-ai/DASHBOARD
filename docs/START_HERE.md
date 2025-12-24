# 🚀 FILE KHỞI ĐỘNG - BẮT ĐẦU TỪ ĐÂY

## 📌 CÁC FILE QUAN TRỌNG NHẤT (Chỉ 3 file bạn cần)

### 1. 🎯 **index.html** (hoặc `dashboard.html`) - FILE KHỞI ĐỘNG CHÍNH
```
Click đúp để mở → Tự động chuyển hướng sang dashboard
```
**Đây là file BẠN CẦN!**

### 2. 💾 **full_data.js** - DỮ LIỆU CHỨA MỌI CHỈ SỐ
```
Chứa data cho tất cả các chỉ số (VNINDEX, VN30, VN100, etc.)
```

### 3. 🤖 **tools/auto_parse.py** - CÔNG CỤ AUTO CHO BÁO CÁO MỚI
```
Chạy script này khi có báo cáo Word mới → Tự động tạo dashboard mới
```

---

## ⚡ BẮT ĐẦU NGAY (3 Click)

### Cách 1: Xem Dashboard Hiện Tại
```bash
# Mở file này là xong!
open index.html
```

### Cách 2: Tạo Dashboard Cho Báo Cáo Mới
```bash
# Bước 1: Convert Word
textutil -convert txt -stdout "reports/word/BaoCao_MOI.docx" > reports/txt/baocao_moi.txt

# Bước 2: Run parser
python3 tools/auto_parse.py reports/txt/baocao_moi.txt full_data_new.js

# Bước 3: Verify + replace data
node --check full_data_new.js
cp full_data_new.js full_data.js

# Bước 4: Mở dashboard để kiểm tra
open index.html
```

---

## 📂 CẤU TRÚC FILE ĐƠN GIẢN

```
UI GLM/
├── 🎯 index.html              ← FILE KHỞI ĐỘNG!
├── 🎄 ELEGANT_CHRISTMAS.html  ← Dashboard hiện tại
├── 💾 full_data.js            ← Data đầy đủ
├── 🤖 tools/auto_parse.py     ← Tool tự động
├── 📖 docs/START_HERE.md      ← File này (root có stub `START_HERE.md`)
├── 📚 docs/GUIDE.md           ← Hướng dẫn chi tiết
└── 📁 reports/                ← File Word/Text báo cáo

📁 archive/_old_files/         ← Các file cũ (đã archive)
```

---

## 🎯 BẠN CẦN LÀM GÌ?

### Muốn XEM Dashboard?
→ Click đúp **`index.html`** (hoặc `dashboard.html`)

### Muốn Thêm Chỉ Số Mới?
→ Mở **`full_data.js`** và thêm theo cấu trúc có sẵn

### Muốn Tạo Dashboard Cho Báo Cáo Mới?
→ Chạy **`tools/auto_parse.py`**

### Muốn Hiểu Chi Tiết?
→ Đọc **`docs/GUIDE.md`**

---

## ✅ CHECKLIST

- [ ] Đã mở `index.html` để xem dashboard hiện tại
- [ ] Đã đọc `docs/GUIDE.md` để hiểu cách sử dụng
- [ ] Đã test parser với báo cáo mới (nếu có)

---

**Status:** ✅ READY TO USE
**Version:** 3.0 FINAL
**Updated:** 2024-12-24

**Question?** Read `docs/GUIDE.md` for detailed instructions.
