import subprocess
import os

print("🔧 WORKING VERSION - Fix double closing brace\n")

# Đọc vnindex_data.js - chỉ lấy từ "vnindex:" KHÔNG bao gồm dấu mở ngoặc
with open('vnindex_data.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Tìm vị trí bắt đầu của vnindex
start_pos = content.find('vnindex:')
if start_pos == -1:
    print("❌ Cannot find vnindex")
    exit(1)

# Tìm vị trí kết thúc (}; cuối cùng)
# Bắt đầu tìm từ start_pos
end_pos = content.rfind('};')
if end_pos == -1 or end_pos < start_pos:
    print("❌ Cannot find end")
    exit(1)

# Trích xuất từ start_pos đến end_pos
vnindex_extract = content[start_pos:end_pos]
# Bỏ dấu đóng ngoặc cuối
vnindex_extract = vnindex_extract.rstrip().rstrip('}')

print(f"✅ Extracted vnindex: {len(vnindex_extract)} chars")

# Đọc các file khác
with open('full_data_remaining.js', 'r', encoding='utf-8') as f:
    industry = f.read().strip()

with open('full_data_special.js', 'r', encoding='utf-8') as f:
    special = f.read().strip()

# Build output - chú ý KHÔNG có dấu ngoặc kép xung quanh placeholder
output = f"""// ==========================================
// DỮ LIỆU HOÀN CHỈNH CHO TẤT CẢ CHỈ SỐ
// ==========================================

const FULL_DATA = {{
    {vnindex_extract}
}},
    // ==========================================
    // 7 Chỉ Số Ngành
    // ==========================================
    {industry}
}},
    // ==========================================
    // 3 Chỉ Số Đặc Biệt
    // ==========================================
    {special}
}};"""

# Ghi file
with open('full_data.js', 'w', encoding='utf-8') as f:
    f.write(output)

print("✅ File written")

# Verify
result = subprocess.run(['node', '--check', 'full_data.js'], 
                       capture_output=True, text=True, timeout=15)

if result.returncode == 0:
    print("\n" + "="*70)
    print("✅✅✅ JAVASCRIPT VALID! DASHBOARD HOÀN CHỈNH! ✅✅✅")
    print("="*70)
    
    import re
    indices = re.findall(r'(\w+):\s*{{', output)
    sections = output.count('icon:')
    
    print(f"\n🎉 KẾT QUẢ:")
    print(f"   • {len(set(indices))} chỉ số")
    print(f"   • {sections}+ sections")
    
    print(f"\n✨ MỬ DASHBOARD NGAY! ✨\n")
    
    # Mở dashboard
    time.sleep(1)
    os.system('open COMPLETE.html')
    time.sleep(1)  
    os.system('open TEST_VERIFICATION.html')
    print("🚀 Đã mở dashboard với đầy đủ data!\n")
else:
    print(f"\n❌ Error: {result.stderr[:300]}")

