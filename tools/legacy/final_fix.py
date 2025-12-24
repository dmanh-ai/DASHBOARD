import re
import subprocess

print("🔧 FINAL FIX - Extract only content...\n")

# Đọc vnindex_data.js
with open('vnindex_data.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Trích xuất TỪ "vnindex:" đến trước "};"
# Không bao gồm "const FULL_DATA = {"
match = re.search(r'vnindex:\s*{(.+?)};\s*$', content, re.DOTALL)
if not match:
    # Thử pattern khác
    match = re.search(r'FULL_DATA\s*=\s*{\s*vnindex:\s*{(.+)};', content, re.DOTALL)

if match:
    # Lấy nội dung, thêm lại "vnindex: {" ở đầu
    inner_content = match.group(1)
    vnindex_part = "    vnindex: {" + inner_content + "\n    }"
    print("✅ Extracted vnindex successfully")
else:
    print("❌ Cannot extract with regex, using alternative method")
    # Alternative: Đọc từ dòng 4 đến 606
    lines = content.split('\n')
    # Bỏ 3 dòng đầu và dòng cuối
    vnindex_part = '\n'.join(lines[3:606])
    # Thêm indent
    vnindex_part = '    ' + vnindex_part.replace('\n', '\n    ')
    print("✅ Extracted using line range")

# Đọc industry và special
with open('full_data_remaining.js', 'r', encoding='utf-8') as f:
    industry = f.read().strip()

with open('full_data_special.js', 'r', encoding='utf-8') as f:
    special = f.read().strip()

# Build final output
output = """// ==========================================
// DỮ LIỆU HOÀN CHỈNH CHO TẤT CẢ CHỈ SỐ
// 100% Coverage - Phiên bản hoàn chỉnh
// ==========================================

const FULL_DATA = {
""" + vnindex_part + """,
    // ==========================================
    // 7 Chỉ Số Ngành
    // ==========================================
    """ + industry + """,
    // ==========================================
    // 3 Chỉ Số Đặc Biệt
    // ==========================================
    """ + special + """

};"""

# Ghi file
with open('full_data.js', 'w', encoding='utf-8') as f:
    f.write(output)

print("✅ File created")

# Verify syntax
result = subprocess.run(['node', '--check', 'full_data.js'], 
                       capture_output=True, text=True, timeout=10)

print("\n" + "="*60)
if result.returncode == 0:
    print("✅✅✅ JAVASCRIPT SYNTAX: VALID! ✅✅✅")
    
    indices = re.findall(r'(\w+):\s*{', output)
    sections = output.count('icon:')
    
    print(f"\n🎉🎉🎉 SUCCESS! 🎉🎉🎉")
    print(f"="*60)
    print(f"   ✅ {len(set(indices))} chỉ số")
    print(f"   ✅ {sections}+ sections")
    print(f"\n✨ DASHBOARD HOÀN CHỈNH! ✨")
    
    # Mở lại các trang
    import os
    os.system('open COMPLETE.html')
    os.system('open TEST_VERIFICATION.html')
    print(f"\n🚀 Đã mở lại dashboard trong browser!")
else:
    print(f"❌ Syntax Error:\n{result.stderr[:200]}")

