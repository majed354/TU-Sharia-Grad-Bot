#!/bin/bash
# ═══════════════════════════════════════════════════════════
# 🚀 سكريبت إعداد VPS — مساعد الدراسات العليا
# يُشغّل مرة واحدة فقط على VPS جديد (Hostinger KVM 2)
# ═══════════════════════════════════════════════════════════

set -e

echo "═══════════════════════════════════════════"
echo " 🔧 بدء إعداد الخادم"
echo "═══════════════════════════════════════════"

# --- 1. تحديث النظام ---
echo "📦 تحديث النظام..."
sudo apt update && sudo apt upgrade -y

# --- 2. تثبيت الأدوات الأساسية ---
echo "🛠️ تثبيت الأدوات..."
sudo apt install -y curl wget git ufw nano htop

# --- 3. تثبيت Docker ---
echo "🐳 تثبيت Docker..."
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# --- 4. تثبيت Docker Compose ---
echo "🐳 تثبيت Docker Compose..."
sudo apt install -y docker-compose-plugin

# --- 5. تثبيت Nginx ---
echo "🌐 تثبيت Nginx..."
sudo apt install -y nginx

# --- 6. إعداد الجدار الناري ---
echo "🔒 إعداد الجدار الناري..."
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw --force enable

# --- 7. تثبيت Certbot ---
echo "🔐 تثبيت Certbot..."
sudo apt install -y certbot python3-certbot-nginx

# --- 8. إنشاء مجلد المشروع ---
echo "📁 إنشاء مجلد المشروع..."
mkdir -p ~/grad-assistant-bot

echo ""
echo "═══════════════════════════════════════════"
echo " ✅ تم إعداد الخادم بنجاح!"
echo "═══════════════════════════════════════════"
echo ""
echo "الخطوات التالية:"
echo "  1. أعد تسجيل الدخول (لتفعيل Docker بدون sudo):"
echo "     exit && ssh user@your-server"
echo ""
echo "  2. استنسخ المشروع:"
echo "     cd ~ && git clone https://github.com/YOUR_USER/grad-assistant-bot.git"
echo "     cd grad-assistant-bot"
echo ""
echo "  3. أنشئ ملف .env:"
echo "     cp .env.example .env && nano .env"
echo ""
echo "  4. أضف المستندات في documents/"
echo ""
echo "  5. شغّل بـ Docker:"
echo "     docker compose up -d --build"
echo ""
echo "  6. جهّز قاعدة المعرفة:"
echo "     docker compose exec bot python -m app.rag.ingest"
echo ""
echo "  7. أعد Nginx + SSL:"
echo "     sudo cp nginx.conf /etc/nginx/sites-available/grad-bot"
echo "     sudo ln -s /etc/nginx/sites-available/grad-bot /etc/nginx/sites-enabled/"
echo "     # عدّل الدومين في الملف"
echo "     sudo nano /etc/nginx/sites-available/grad-bot"
echo "     sudo nginx -t && sudo systemctl reload nginx"
echo "     sudo certbot --nginx -d yourdomain.com"
echo ""
