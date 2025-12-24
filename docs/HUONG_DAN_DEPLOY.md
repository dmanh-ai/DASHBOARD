# 🚀 HƯỚNG DẪN DEPLOY DASHBOARD LÊN GITHUB PAGES

## ✅ Đã hoàn thành:
- [x] Tạo GitHub repository: https://github.com/Thanhtran-165/marketoverview.github.io
- [x] Tạo SSH key cho authentication
- [x] Chuẩn bị tất cả code để deploy

## 📝 BƯỚC TIẾP THEO (Bạn làm ngay):

### 1️⃣ Thêm SSH Key vào GitHub

**Public Key của bạn:**
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILhHIggA24oxeX+b7bDxCb16KBI2ll1uZv0jyQMYvTUd thanhtran165@github.com
```

**Các bước:**
1. Vào: https://github.com/settings/keys
2. Click **New SSH key**
3. **Title:** MacBook Pro
4. **Key:** Paste public key ở trên vào
5. Click **Add SSH key**

✅ **Xong bước này rồi? Chạy command:**
```bash
./tools/test_and_deploy.sh
```

---

### 2️⃣ Script sẽ tự động làm:
- ✅ Test SSH connection với GitHub
- ✅ Đổi remote URL sang SSH
- ✅ Push toàn bộ code lên GitHub
- ✅ Hướng dẫn enable GitHub Pages

---

### 3️⃣ Kích hoạt GitHub Pages

Sau khi push thành công, làm thêm bước này:

1. **Vào Settings Pages:**
   - Link: https://github.com/Thanhtran-165/marketoverview.github.io/settings/pages

2. **Cấu hình:**
   - **Source:** Deploy from a branch
   - **Branch:** `main`
   - **Folder:** `/ (root)`
   - Click **Save**

3. **Chờ deploy:** 1-3 phút

4. **Truy cập dashboard:**
   - 🌐 https://thanhtan-165.github.io/

---

## 🎯 Dashboard của bạn sẽ có:

✅ **URL:** https://thanhtan-165.github.io/  
✅ **16 data objects:** 1 Overview + 15 Indices  
✅ **218 sections:** Phân tích đầy đủ  
✅ **Responsive:** Hoạt động trên mọi thiết bị  
✅ **Miễn phí:** Hosting vĩnh viễn từ GitHub  
✅ **Auto-update:** Push code → Deploy tự động  

---

## 📋 Cách update khi có file Word mới:

```bash
# 1. Parse file mới
python3 tools/auto_parse.py baocao_new.txt full_data_new.js

# 2. Verify syntax
node --check full_data_new.js

# 3. Replace data (nếu OK)
cp full_data_new.js full_data.js

# 3. Commit & push
git add full_data.js
git commit -m "Update: $(date +%Y-%m-%d)"
git push origin main

# GitHub Pages sẽ tự động update sau 1-3 phút!
```

---

## ❓ Nếu gặp lỗi:

### Lỗi: "Permission denied (publickey)"
→ Bạn chưa thêm SSH key vào GitHub. Làm lại Bước 1.

### Lỗi: "Could not resolve hostname"
→ Kiểm tra internet connection.

### GitHub Pages không hiển thị
1. Kiểm tra: https://github.com/Thanhtran-165/marketoverview.github.io/settings/pages
2. Đảm bảo branch là `main`, folder là `/ (root)`
3. Chờ thêm 2-3 phút
4. Xem tab **Actions** để biết lỗi gì

### Data không load
1. Mở browser Console (F12)
2. Xem có lỗi gì không
3. Verify: `node --check full_data.js`
4. Kiểm tra đường dẫn đến `full_data.js` trong HTML

---

## 📞 Cần hỗ trợ?

Nếu gặp lỗi:
1. Copy error message
2. Chụp screenshot
3. Gửi cho tôi

**Chúc bạn deploy thành công! 🚀**

---

## 🔗 Links quan trọng:

- **Repository:** https://github.com/Thanhtran-165/marketoverview.github.io
- **Settings Pages:** https://github.com/Thanhtran-165/marketoverview.github.io/settings/pages
- **SSH Keys:** https://github.com/settings/keys
- **Dashboard (sau khi deploy):** https://thanhtan-165.github.io/
