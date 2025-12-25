# Market Overview Dashboard - Financial Theme

Báo cáo thị trường chứng khoán Việt Nam với giao diện chuyên nghiệp, nền sáng.

## 🌐 Mở Dashboard

- **Local**: Mở `index.html` (sẽ tự động redirect đến `DASHBOARD.html`)
- **GitHub Pages**: https://thanhtan-165.github.io/

## 📊 Dashboard Features

### Theme
- ✅ **Financial Light Theme** - Nền sáng chuyên nghiệp
- 🎨 Màu xanh dương tài chính
- 📱 Responsive hoàn toàn (Desktop/Tablet/Mobile)
- 🔍 Tìm kiếm & filter realtime
- 📁 Sidebar với 5 categorized groups

### Nội dung
- 📊 **1 Overview** (9 sections) - Báo cáo tổng hợp thị trường
- 📈 **15 Indices** (mỗi index 14 sections):
  - **Chỉ số chính**: VNINDEX, VN30, VN100
  - **Vốn hóa**: VNMIDCAP, VNSML
  - **Ngành hàng**: VNREAL, VNIT, VNHEAL, VNFIN, VNENE, VNCONS, VNMAT, VNCOND
  - **Đặc biệt**: VNFINSELECT, VNDIAMOND

### Tổng cộng: **16 data objects | 218 sections**

---

## 📁 File Structure

```
marketoverview.github.io/
├── index.html                  ← Entry point (redirect to DASHBOARD.html)
├── DASHBOARD.html              ← Main dashboard (Financial Light Theme)
├── test_all_16.html            ← Test verification page
├── full_data.js                ← Data file (16 objects, 218 sections)
│
├── tools/                      ← Parser tools
│   ├── auto_parse.py           ← Main parser script
│   ├── smart_parser.py         ← O(N) parsing logic
│   ├── renderer.py             ← JS generation
│   ├── parser_models.py        ← Data structures & errors
│   └── benchmark.py            ← Performance testing
│
├── tests/                      ← Golden tests
│   └── test_parser.py
│
├── reports/
│   └── txt/baocao_full.txt     ← Input data source
│
└── archive/                    ← Old versions
    ├── ELEGANT_CHRISTMAS_christmas_theme.html
    └── _old_files/
```

---

## 🔄 Update Workflow

Khi có file Word mới:

```bash
# 1. Parse file Word mới
python3 tools/auto_parse.py reports/txt/baocao_new.txt full_data.js

# 2. Verify syntax
node --check full_data.js

# 3. Test locally
python3 -m http.server 8080
# Mở http://localhost:8080

# 4. Commit & push (auto deploy sau 1-3 phút)
git add full_data.js
git commit -m "Update: $(date +%Y-%m-%d)"
git push origin main
```

---

## 🧪 Testing

```bash
# Run parser tests
python3 -m pytest tests/test_parser.py -v

# Run benchmark
python3 tools/benchmark.py reports/txt/baocao_full.txt

# KPI Targets:
# - Time: < 2s (achieved: 0.054s)
# - Memory: < 100 MB (achieved: 1.57 MB)
# - Success rate: 16/16 (achieved: 16/16)
```

---

## 🎯 Performance Metrics

| Metric | Target | Achieved | Status |
|--------|--------|----------|--------|
| Parse time | < 2s | 0.054s | ✅ 37× faster |
| Memory usage | < 100 MB | 1.57 MB | ✅ 98% under |
| Success rate | 16/16 | 16/16 | ✅ 100% |
| Algorithm | O(N) | O(N) | ✅ Optimal |

---

## 📚 Documentation

- Parser implementation: `tools/smart_parser.py`
- Test suite: `tests/test_parser.py`
- Data models: `tools/parser_models.py`
- Renderer: `tools/renderer.py`

---

## 🆘 Troubleshooting

### Dashboard không load?
- Mở browser Console (F12) để kiểm tra lỗi
- Verify `full_data.js` tồn tại và đúng format
- Test với `node --check full_data.js`

### Parser lỗi?
- Kiểm tra input file format: `reports/txt/baocao_full.txt`
- Run tests: `python3 -m pytest tests/test_parser.py -v`
- Run benchmark: `python3 tools/benchmark.py`

### GitHub Pages không update?
- Chờ 1-3 phút cho deploy
- Xem tab **Actions** để check lỗi
- Force refresh browser (Cmd+Shift+R)

---

## 🎉 Done!

**Dashboard đã online với Financial Light Theme chuyên nghiệp!**

### URL: https://thanhtan-165.github.io/
