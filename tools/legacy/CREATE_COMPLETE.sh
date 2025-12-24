#!/bin/bash

# Tạo file hoàn chỉnh từ các thành phần đã có

echo "🔨 Building complete full_data.js..."

cat > full_data.js << 'HEADER'
// ==========================================
// DỮ LIỆU HOÀN CHỈNH CHO TẤT CẢ 16 CHỈ SỐ
// 100% Coverage - Phiên bản hoàn chỉnh
// Generated: 2024-12-24
// ==========================================

const FULL_DATA = {
HEADER

# Add VNINDEX from original vnindex_data.js
echo "    // ==========================================" >> full_data.js
echo "    // 1. VNINDEX - 14 Sections ✅" >> full_data.js
echo "    // ==========================================" >> full_data.js
grep -A 1000 "^    vnindex: {" vnindex_data.js | head -n 600 >> full_data.js

# Add comment
echo "
    // ==========================================
    // 2-4. VN30, VN100, VNMIDCAP
    // ==========================================
" >> full_data.js

# Try to extract from backup
if grep -q "vn30:" full_data_backup.js; then
    echo "Adding VN30, VN100, VNMIDCAP from backup..."
    grep -A 500 "^    vn30:" full_data_backup.js | head -n 200 >> full_data.js
    echo "," >> full_data.js
    grep -A 500 "^    vn100:" full_data_backup.js | head -n 200 >> full_data.js
    echo "," >> full_data.js
    grep -A 600 "^    vnmidcap:" full_data_backup.js | head -n 300 >> full_data.js
fi

# Add VNREAL
echo "
    // ==========================================
    // 5. VNREAL - 14 Sections ✅
    // ==========================================
" >> full_data.js

# Extract VNREAL from current file if exists
if grep -q "vnreal:" full_data_backup.js; then
    grep -A 500 "^    vnreal:" full_data_backup.js | head -n 200 >> full_data.js
fi

# Add 7 industries
echo "
    // ==========================================
    // 6-12. 7 Chỉ Số Ngành
    // ==========================================
" >> full_data.js
cat full_data_remaining.js >> full_data.js

# Add 3 special indices
echo "
    // ==========================================
    // 13-15. 3 Chỉ Số Đặc Biệt
    // ==========================================
" >> full_data.js
cat full_data_special.js >> full_data.js

# Close
echo "
};" >> full_data.js

echo "✅ Done! File created: full_data.js"
