import re
import subprocess

print("🔧 Fix double braces...\n")

# Đọc vnindex_data.js
with open('vnindex_data.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Trích xuất nội dung BÊN TRONG object FULL_DATA
# Tìm từ "vnindex:" đến cuối
match = re.search(r'(const FULL_DATA = \{)?(.+)', content, re.DOTALL)
if match:
    # Lấy tất cả content sau FULL_DATA = {
    all_data = match.group(2)
    # Tìm }; cuối cùng
    end_pos = all_data.rfind('};')
    if end_pos > 0:
        vnindex_data = all_data[:end_pos].rstrip()
    else:
        vnindex_data = all_data.rstrip().rstrip('};')
    
    # Xóa dấu mở ngoặc đầu tiên nếu có
    vnindex_data = vnindex_data.lstrip('{').lstrip()
    
    print(f"✅ Extracted clean data")
else:
    print("❌ Failed")
    exit(1)

# Đọc industry và special
with open('full_data_remaining.js', 'r', encoding='utf-8') as f:
    industry = f.read().strip().rstrip(';')

with open('full_data_special.js', 'r', encoding='utf-8') as f:
    special = f.read().strip().rstrip(';')

# Build output chính xác
output = """// ==========================================
// DỮ LIỆU HOÀN CHỈNH CHO TẤT CẢ CHỈ SỐ
// 100% Coverage - Phiên bản hoàn chỉnh
// ==========================================

const FULL_DATA = {
""" + vnindex_data + """
},

    // ==========================================
    // 7 Chỉ Số Ngành
    // ==========================================
    """ + industry + """
},

    // ==========================================
    // 3 Chỉ Số Đặc Biệt
    // ==========================================
    """ + special + """

};"""

# Ghi file
with open('full_data.js', 'w', encoding='utf-8') as f:
    f.write(output)

print("✅ File created")

# Test syntax
result = subprocess.run(['node', '--check', 'full_data.js'], 
                       capture_output=True, text=True, timeout=10)

if result.returncode == 0:
    print("✅✅✅ VALID JAVASCRIPT!")
    
    indices = re.findall(r'(\w+):\s*{', output)
    sections = output.count('icon:')
    
    print(f"\n" + "="*50)
    print(f"🎉🎉🎉 SUCCESS! 🎉🎉🎉")
    print(f"="*50)
    print(f"   • {len(set(indices))} chỉ số")
    print(f"   • {sections} sections")
    print(f"\n✨ DASHBOARD SẴN SÀNG! ✨")
    
    # Reload browser
    import os
    os.system('open COMPLETE.html')
    
else:
    print(f"❌ Error:\n{result.stderr[:200]}")

