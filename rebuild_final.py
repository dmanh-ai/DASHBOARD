import re
import subprocess

print("🔨 FINAL rebuild...\n")

# Đọc và trích xuất vnindex
with open('vnindex_data.js', 'r', encoding='utf-8') as f:
    content = f.read()

match = re.search(r'FULL_DATA\s*=\s*({.+)', content, re.DOTALL)
if not match:
    print("❌ Cannot extract vnindex")
    exit(1)

vnindex_all = match.group(1)
# Tìm }; cuối cùng
last_brace = vnindex_all.rfind('};')
vnindex_obj = vnindex_all[:last_brace].rstrip()

print(f"✅ Extracted VNINDEX")

# Đọc industry và special
with open('full_data_remaining.js', 'r', encoding='utf-8') as f:
    industry = f.read().strip().rstrip(';')

with open('full_data_special.js', 'r', encoding='utf-8') as f:
    special = f.read().strip().rstrip(';')

# Build output
output = """// ==========================================
// DỮ LIỆU HOÀN CHỈNH CHO TẤT CẢ CHỈ SỐ
// 100% Coverage - Phiên bản hoàn chỉnh
// ==========================================

const FULL_DATA = {
""" + vnindex_obj + """
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

# Check syntax
result = subprocess.run(['node', '--check', 'full_data.js'], 
                       capture_output=True, text=True, timeout=10)
if result.returncode == 0:
    print("✅ VALID JavaScript!")
    
    indices = re.findall(r'(\w+):\s*{', output)
    sections = output.count('icon:')
    
    print(f"\n🎉 SUCCESS!")
    print(f"   • {len(set(indices))} indices")
    print(f"   • {sections} sections")
    print(f"\n✨ READY TO USE!")
else:
    print(f"❌ Error:\n{result.stderr[:300]}")

