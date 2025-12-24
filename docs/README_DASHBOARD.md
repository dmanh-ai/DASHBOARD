# 📊 Stock Dashboard System - Hướng Dẫn Sử Dụng

## 🎯 Tính Năng Chính

✅ **100% Coverage** - Không bỏ sót chi tiết nào từ báo cáo gốc
✅ **Tái sử dụng được** - Dùng cho mọi báo cáo Word khác nhau
✅ **Dynamic Rendering** - Content load từ JavaScript data
✅ **Responsive Design** - Hiển thị tốt trên mọi thiết bị

---

## 📁 Cấu Trúc File

```
UI GLM/
├── dashboard_template.html          # Template HTML chính (TÁI SỬ DỤNG)
├── stock_dashboard_full.js           # File data cho báo cáo hiện tại
├── dashboard_100percent.html         # Dashboard hoàn chỉnh (đã render)
├── reports/txt/baocao_full.txt       # File text từ Word gốc
└── README_DASHBOARD.md              # File hướng dẫn này
```

---

## 🚀 Cách Sử Dụng Cho Báo Cáo Mới

### Bước 1: Chuyển Word sang Text

```bash
textutil -convert txt -stdout "reports/word/BaoCao_MOI.docx" > reports/txt/baocao_moi.txt
```

### Bước 2: Tạo File Data JS Mới

Tạo file `baocao_moi_data.js` với cấu trúc:

```javascript
const FULL_DATA = {
    vnindex: {
        title: "VNINDEX - PHÂN TÍCH ĐẦY ĐỦ",
        sections: [
            {
                icon: "📊",
                title: "THÔNG TIN CHUNG",
                content: `
                    <div class="info-box">
                        <h4>Tiêu đề</h4>
                        <p>Nội dung ở đây...</p>
                    </div>
                `
            },
            {
                icon: "📈",
                title: "XU HƯỚNG GIÁ",
                content: `...`
            },
            {
                icon: "🎯",
                title: "KHUYẾN NGHỊ",
                alert: true,  // true = hiển thị như alert box
                content: `...`
            }
            // ... thêm các sections khác
        ]
    },
    vn30: {
        title: "VN30 - PHÂN TÍCH ĐẦY ĐỦ",
        sections: [ ... ]
    }
    // ... thêm các chỉ số khác
};
```

### Bước 3: Copy Template & Sửa Link

1. Copy `dashboard_template.html` → `dashboard_baocao_moi.html`

2. Sửa dòng này trong file HTML mới:
```html
<!-- Đổi từ: -->
<script src="stock_dashboard_full.js"></script>

<!-- Thành: -->
<script src="baocao_moi_data.js"></script>
```

### Bước 4: Mở File HTML

```bash
open dashboard_baocao_moi.html
```

---

## 🎨 Cấu Trúc Section

### Section Thường

```javascript
{
    icon: "📊",
    title: "TÊN SECTION",
    content: `
        <div class="info-box">
            <h4>Tiêu đề con</h4>
            <p>Nội dung...</p>
        </div>
    `
}
```

### Section Alert (viền tím, nổi bật)

```javascript
{
    icon: "🎯",
    title: "KHUYẾN NGHỊ",
    alert: true,  // ← Thêm dòng này
    content: `
        <p><strong>Hành động:</strong> ...</p>
        <p>Nội dung...</p>
    `
}
```

### Các Class CSS Có Sẵn

```javascript
// Màu chữ
<span class="highlight">Tin cậy cao</span>  // Xanh lá
<span class="warning">Cảnh báo</span>        // Cam
<span class="danger">Nguy hiểm</span>        // Đỏ

// Info box background
<div class="info-box success">...</div>   // Xanh nhạt
<div class="info-box warning">...</div>   // Cam nhạt
<div class="info-box danger">...</div>    // Đỏ nhạt
```

---

## 📊 Template Đã Có Sẵn

### 1. VNINDEX (100% Complete) ✅

File: `stock_dashboard_full.js`

**14 Sections đầy đủ:**
1. Thông tin chung
2. Xu hướng giá (ngắn/trung/dài + divergence)
3. Xu hướng khối lượng
4. Kết hợp giá & khối lượng
5. Cung-Cầu
6. Mức giá quan trọng
7. Biến động giá
8. Mô hình giá - Mô hình nến
9. Market Breadth & Tâm lý
10. Lịch sử & Xu hướng Breadth
11. Rủi ro (ngắn/trung/dài + 3 điều kiện thất bại)
12. Khuyến nghị vị thế
13. Giá mục tiêu
14. Kịch bản What-if (4 kịch bản)

**Cách dùng:**
```html
<!-- Sử dụng file data có sẵn -->
<script src="stock_dashboard_full.js"></script>
```

---

## 🔄 Quy Trình Tự Động

### Manual (Hiện tại)

```
1. Chuyển Word → Text
2. Tạo file data JS thủ công
3. Render HTML
```

### Tự Động (Tương lai)

Có thể phát triển thêm:
- Python script parse text → JSON
- Auto-extract sections từ Word structure
- Generate JS data file tự động

---

## ✅ Check List Trước Khi Xuất Bản

- [ ] Đã convert Word → Text thành công
- [ ] File data JS có cấu trúc đúng
- [ ] Tất cả sections đều có icon & title
- [ ] Content sử dụng đúng HTML classes
- [ ] Test trên browser (Chrome/Safari)
- [ ] Responsive trên mobile
- [ ] Đổi tên file data trong HTML
- [ ] Update title/subtitle trong header

---

## 🐛 Troubleshooting

### Lỗi: "FULL_DATA is not defined"

**Nguyên nhân:** File data JS chưa được load

**Giải pháp:** Kiểm tra `<script src="...">` trong HTML

---

### Lỗi: Sections không hiển thị

**Nguyên nhân:** Cấu trúc data sai

**Giải pháp:**
```javascript
// SAI
{ title: "ABC", content: "..." }  // Thiếu sections array

// ĐÚNG
{
    title: "ABC",
    sections: [  // ← Phải có sections array
        { icon: "...", title: "...", content: "..." }
    ]
}
```

---

### Lỗi: HTML không render đúng

**Nguyên nhân:** Template literals không đúng

**Giải pháp:** Sử dụng backticks (`), không dùng quotes (' hoặc ")

```javascript
// SAI
content: '<div class="info-box">...</div>'

// ĐÚNG
content: `
    <div class="info-box">
        ...
    </div>
`
```

---

## 📞 Support

Khi gặp vấn đề:
1. Check console (F12 → Console tab)
2. Verify data structure
3. Test with known-good template (VNINDEX)

---

## 🎯 Next Steps

1. ✅ VNINDEX 100% - DONE
2. ⏳ Thêm VN30, VN100, VNMIDCAP...
3. ⏳ Tạo script tự động parse text → data
4. ⏳ Add export feature (HTML → PDF)

---

**Created:** 2024-12-24
**Version:** 1.0
**Status:** Production Ready ✅
