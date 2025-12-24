#!/bin/bash
# 🚀 DEPLOY SCRIPT - Push code lên GitHub Pages
# Sử dụng sau khi đã tạo repository trên GitHub

echo "🚀 DEPLOY DASHBOARD LÊN GITHUB PAGES"
echo "======================================"
echo ""

# Kiểm tra đã có remote chưa
if git remote get-url origin > /dev/null 2>&1; then
    echo "✅ Đã có remote origin:"
    git remote get-url origin
    echo ""
else
    echo "❌ CHƯA CÓ REMOTE ORIGIN"
    echo ""
    echo "Bạn cần tạo repository trên GitHub trước:"
    echo "1. Vào: https://github.com/new"
    echo "2. Đặt tên: vietnam-stock-dashboard (hoặc tên bạn thích)"
    echo "3. Click 'Create repository'"
    echo ""
    echo "Sau đó chạy lại script này với command:"
    echo "   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git"
    echo ""
    exit 1
fi

# Check xem có changes chưa commit
if git diff-index --quiet HEAD --; then
    echo "✅ Không có changes chưa commit"
else
    echo "⚠️  Có changes chưa commit!"
    echo ""
    git status --short
    echo ""
    read -p "Bạn muốn commit các changes này? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📝 Committing changes..."
        git add -A
        git commit -m "Update: $(date +%Y-%m-%d)"
        echo "✅ Done!"
    else
        echo "❌ Hủy deploy. Hãy commit changes trước."
        exit 1
    fi
fi

# Push lên GitHub
echo ""
echo "📤 Pushing code to GitHub..."
echo ""
git push origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ DEPLOY THÀNH CÔNG!"
    echo ""
    echo "📝 Các bước tiếp theo:"
    echo "1. Vào repository trên GitHub"
    echo "2. Click Settings → Pages (menu bên trái)"
    echo "3. Cấu hình:"
    echo "   - Source: Deploy from a branch"
    echo "   - Branch: main"
    echo "   - Folder: / (root)"
    echo "4. Click Save"
    echo ""
    echo "⏳ Chờ 1-3 phút để GitHub Pages deploy"
    echo ""
    echo "🌐 Dashboard sẽ có địa chỉ:"
    git remote get-url origin | sed 's|https://github.com/|https://|g' | sed 's|\.git|/COMPLETE.html|g'
    echo ""
    echo "🎉 Xong! Dashboard đã online!"
else
    echo ""
    echo "❌ PUSH THẤT BẠI"
    echo ""
    echo "Có thể lỗi:"
    echo "- Authentication: Kiểm tra username/password"
    echo "- Network: Kiểm tra internet"
    echo "- Repository chưa tồn tại trên GitHub"
    echo ""
    exit 1
fi
