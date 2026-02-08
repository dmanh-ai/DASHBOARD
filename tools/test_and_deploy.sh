#!/bin/bash
# 🚀 TEST SSH & DEPLOY

echo "🔐 Bước 1: Test SSH connection với GitHub..."
echo ""

ssh -T git@github.com 2>&1 | grep "successfully authenticated"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SSH authentication THÀNH CÔNG!"
    echo ""

    echo "🔄 Bước 2: Đổi remote URL sang SSH..."
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "$SCRIPT_DIR"
    git remote set-url origin git@github.com:Dmanh-ai/DASHBOARD.git

    echo "✅ Done! Remote URL:"
    git remote get-url origin
    echo ""

    echo "📤 Bước 3: Push code lên GitHub..."
    echo ""
    git push -u origin main

    if [ $? -eq 0 ]; then
        echo ""
        echo "🎉 PUSH THÀNH CÔNG!"
        echo ""
        echo "📝 Bước tiếp theo - KÍCH HOẠT GITHUB PAGES:"
        echo "1. Vào: https://github.com/Dmanh-ai/DASHBOARD/settings/pages"
        echo "2. Configure:"
        echo "   - Source: Deploy from a branch"
        echo "   - Branch: main"
        echo "   - Folder: / (root)"
        echo "3. Click Save"
        echo ""
        echo "⏳ Chờ 1-3 phút để GitHub Pages deploy"
        echo ""
        echo "🌐 Dashboard sẽ online tại:"
        echo "   https://dmanh-ai.github.io/DASHBOARD/"
        echo ""
    else
        echo ""
        echo "❌ PUSH THẤT BẠI"
        echo "Kiểm tra lại network và permissions"
    fi
else
    echo ""
    echo "❌ SSH authentication THẤT BẠI"
    echo ""
    echo "Bạn cần:"
    echo "1. Thêm SSH key vào GitHub: https://github.com/settings/keys"
    echo "2. Đảm bảo đã thêm đúng public key:"
    echo "   [PASTE_YOUR_SSH_PUBLIC_KEY_HERE]"
    echo "3. Chạy lại script này sau khi đã thêm key"
fi
