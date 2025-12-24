import subprocess
import re

print("🔧 Fix quotes...\n")

with open('full_data.js', 'r') as f:
    content = f.read()

# Thay title: "..." thành title: '...'
fixed = re.sub(r'title:\s*"([^"]*)"', r"title: '\1'", content)

with open('full_data.js', 'w') as f:
    f.write(fixed)

print("✅ Done")

result = subprocess.run(['node', '--check', 'full_data.js'], capture_output=True, text=True, timeout=15)

if result.returncode == 0:
    print("\n" + "="*70)
    print("✅ SUCCESS!")
    print("="*70)
    
    indices = re.findall(r'(\w+):\s*{', fixed)
    sections = fixed.count('icon:')
    
    print(f"\n📊 {len(set(indices))} chỉ số, {sections} sections\n")
    
    for i, idx in enumerate(sorted(set(indices)), 1):
        pat = rf'{idx}:\s*{{[^}}]*sections:\s*\[([^\]]*)\]'
        m = re.search(pat, fixed, re.DOTALL)
        cnt = m.group(1).count('icon:') if m else 0
        print(f"   {i:2d}. {idx.upper():15s} - {cnt:2d} sections")
    
    print("\n✨ DASHBOARD READY!")
    print("="*70 + "\n")
    
    import os
    os.system('open COMPLETE.html')
    os.system('sleep 2 && open TEST_VERIFICATION.html')
else:
    print(f"\n❌ {result.stderr[:200]}")
    os.system('open COMPLETE.html')

