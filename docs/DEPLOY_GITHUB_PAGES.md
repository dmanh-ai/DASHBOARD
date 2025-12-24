# 🚀 HƯỚNG DẪN DEPLOY DASHBOARD LÊN GITHUB PAGES

## ✅ Đã hoàn thành:
- [x] Khởi tạo Git repository
- [x] Tạo .gitignore
- [x] Commit lần đầu (62 files, 32,992 lines)
- [x] Sẵn sàng push lên GitHub

## 📝 BƯỚC TIẾP THEO (Bạn cần làm):

### 1️⃣ Tạo Repository trên GitHub

1. Vào: https://github.com/new
2. Đặt tên repository: **vietnam-stock-dashboard** (hoặc tên bạn thích)
3. Chọn: **Public** hoặc **Private** (Public thì miễn phí GitHub Pages)
4. **KHÔNG** check:
   - ❌ Add a README file
   - ❌ Add .gitignore
   - ❌ Choose a license
5. Click **Create repository**

### 2️⃣ Push code lên GitHub

Sau khi tạo repo, GitHub sẽ hiện hướng dẫn. Chạy các lệnh sau:

```bash
# Thêm remote (THAY YOUR_USERNAME bằng username GitHub của bạn)
git remote add origin https://github.com/YOUR_USERNAME/vietnam-stock-dashboard.git

# Đổi tên branch main (nếu cần)
git branch -M main

# Push code lên GitHub
git push -u origin main
```

**Ví dụ thực tế:**
```bash
# Nếu username là "nguyenvan"
git remote add origin https://github.com/nguyenvan/vietnam-stock-dashboard.git
git push -u origin main
```

### 3️⃣ Kích hoạt GitHub Pages

1. Vào repository trên GitHub
2. Click **Settings** (tab ở trên)
3. Menu bên trái, chọn **Pages**
4. Cấu hình:
   - **Source**: Deploy from a branch
   - **Branch**: `main`
   - **Folder**: `/ (root)`
5. Click **Save**

### 4️⃣ Chờ deploy hoàn tất

- GitHub sẽ mất khoảng **1-3 phút** để deploy
- Trang sẽ cập nhật tự động khi có commit mới
- Xem进度 ở tab **Actions** hoặc **Pages**

### 5️⃣ Truy cập Dashboard

Sau khi deploy xong, dashboard sẽ có địa chỉ:

```
https://YOUR_USERNAME.github.io/vietnam-stock-dashboard/COMPLETE.html
```

**Hoặc đơn giản hơn:**
```
https://YOUR_USERNAME.github.io/vietnam-stock-dashboard/
```
(Sẽ tự động mở index.html hoặc COMPLETE.html)

---

## 🎯 Cách update khi có file Word mới:

```bash
# 1. Parse file mới
python3 tools/auto_parse.py baocao_new.txt full_data_new.js

# 2. Verify syntax
node --check full_data_new.js

# 3. Replace data (nếu OK)
cp full_data_new.js full_data.js

# 3. Commit thay đổi
git add full_data.js
git commit -m "Update: Báo cáo ngày $(date +%Y-%m-%d)"

# 4. Push lên GitHub
git push origin main

# GitHub Pages sẽ tự động cập nhật sau 1-3 phút!
```

---

## 📊 Files quan trọng trên GitHub Pages:

```
vietnam-stock-dashboard/
├── COMPLETE.html          ← Dashboard chính
├── test_all_16.html       ← Test page
├── full_data.js           ← Data (auto-load)
├── docs/                  ← Tài liệu
└── tools/                 ← Parser tools
```

**Trang chính:** `COMPLETE.html` - hiển thị 16 data objects (1 overview + 15 indices)

---

## ⚠️ Lưu ý quan trọng:

1. **File text nguồn (*.txt) đã bị ignore** - không push lên GitHub để:
   - Giảm kích thước repo
   - Bảo vệ dữ liệu gốc

2. **File Word (*.docx) cũng bị ignore** - lý do tương tự

3. **Chỉ push các file cần thiết** cho dashboard:
   - HTML files
   - JavaScript data files
   - Parser scripts
   - Documentation

4. **Public repository = Miễn phí GitHub Pages**
   - Private vẫn dùng được GitHub Pages nhưng cần GitHub Pro

---

## 🆘 Troubleshooting:

### Error: "failed to push some refs"
```bash
# Pull trước khi push (nếu có conflict)
git pull origin main --allow-unrelated-histories
git push origin main
```

### GitHub Pages không hiển thị
- Kiểm tra tab **Pages** trong Settings
- Chờ thêm 2-3 phút
- Xem tab **Actions** để biết lỗi gì

### Data không load
- Kiểm tra **Console** trong browser (F12)
- Verify syntax: `node --check full_data.js`
- Kiểm tra đường dẫn đến `full_data.js` trong HTML

---

## ✅ Sau khi deploy xong:

Dashboard của bạn sẽ có:
- 🌐 URL công khai: `https://YOUR_USERNAME.github.io/vietnam-stock-dashboard/`
- 📱 Responsive: hoạt động trên mobile, tablet, desktop
- ⚡ Nhanh: Static files, CDN của GitHub
- 🔄 Auto-update: Push code → Deploy tự động
- 💾 Free: Hosting vĩnh viễn miễn phí

---

## 📞 Cần hỗ trợ?

Nếu gặp lỗi:
1. Copy error message
2. Gửi cho tôi kèm screenshot
3. Tôi sẽ giúp bạn fix ngay!

**Chúc bạn deploy thành công! 🚀**
