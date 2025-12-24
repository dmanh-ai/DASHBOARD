#!/bin/bash
# 🔐 SETUP SSH KEY CHO GITHUB
# Script này giúp bạn tạo SSH key và cấu hình với GitHub

echo "🔐 SETUP SSH KEY CHO GITHUB"
echo "================================"
echo ""

# Kiểm tra SSH key đã có chưa
if [ -f ~/.ssh/id_ed25519.pub ]; then
    echo "✅ Đã có SSH key (ed25519)"
    echo ""
    echo "Public key:"
    cat ~/.ssh/id_ed25519.pub
    echo ""
    echo "📝 Copy public key trên và thêm vào GitHub:"
    echo "1. Vào: https://github.com/settings/keys"
    echo "2. Click 'New SSH key'"
    echo "3. Title: 'MacBook Pro' (hoặc tên bạn thích)"
    echo "4. Paste public key vào 'Key' field"
    echo "5. Click 'Add SSH key'"
    echo ""
    echo "Sau đó chạy command để test:"
    echo "   ssh -T git@github.com"
    echo ""
else
    echo "❌ Chưa có SSH key. Đang tạo..."
    echo ""
    ssh-keygen -t ed25519 -C "thanhtran165@github.com" -f ~/.ssh/id_ed25519 -N ""

    echo ""
    echo "✅ Đã tạo SSH key!"
    echo ""
    echo "📝 Public key của bạn:"
    echo "---"
    cat ~/.ssh/id_ed25519.pub
    echo "---"
    echo ""
    echo "📝 BƯỚC TIẾP THEO:"
    echo "1. Copy public key ở trên"
    echo "2. Vào: https://github.com/settings/keys"
    echo "3. Click 'New SSH key'"
    echo "4. Title: 'MacBook Pro'"
    echo "5. Paste public key vào 'Key'"
    echo "6. Click 'Add SSH key'"
    echo ""
    echo "📝 Sau khi thêm key xong, chạy command để test:"
    echo "   ssh -T git@github.com"
    echo ""
    echo "📝 Nếu test thành công, sẽ hiện:"
    echo "   'Hi Thanhtran-165! You've successfully authenticated...'"
    echo ""
fi

echo ""
echo "🔄 Sau khi SSH key đã hoạt động, chạy lệnh này để đổi sang SSH:"
echo "   git remote set-url origin git@github.com:Thanhtran-165/marketoverview.github.io.git"
echo ""
echo "   Sau đó push:"
echo "   git push -u origin main"
echo ""
