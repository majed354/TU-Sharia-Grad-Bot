#!/bin/bash
# ═══════════════════════════════════════════════
# 🔧 أوامر إدارة البوت
# الاستخدام: ./manage.sh [أمر]
# ═══════════════════════════════════════════════

case "$1" in
  start)
    echo "🚀 تشغيل البوت..."
    docker compose up -d --build
    ;;
  stop)
    echo "🛑 إيقاف البوت..."
    docker compose down
    ;;
  restart)
    echo "🔄 إعادة تشغيل..."
    docker compose restart
    ;;
  logs)
    echo "📋 عرض السجلات..."
    docker compose logs -f --tail=100
    ;;
  ingest)
    echo "📚 تجهيز قاعدة المعرفة..."
    docker compose exec bot python -m app.rag.ingest
    ;;
  status)
    echo "📊 حالة البوت..."
    docker compose ps
    echo ""
    curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "⚠️ الخادم لا يستجيب"
    ;;
  shell)
    echo "🐚 دخول الحاوية..."
    docker compose exec bot bash
    ;;
  update)
    echo "⬆️ تحديث من GitHub..."
    git pull
    docker compose up -d --build
    echo "✅ تم التحديث"
    ;;
  *)
    echo "═══════════════════════════════════════"
    echo " 🎓 إدارة بوت الدراسات العليا"
    echo "═══════════════════════════════════════"
    echo ""
    echo "الأوامر المتاحة:"
    echo "  start    — تشغيل البوت"
    echo "  stop     — إيقاف البوت"
    echo "  restart  — إعادة تشغيل"
    echo "  logs     — عرض السجلات"
    echo "  ingest   — تجهيز قاعدة المعرفة"
    echo "  status   — حالة البوت"
    echo "  shell    — دخول الحاوية"
    echo "  update   — تحديث من GitHub"
    echo ""
    ;;
esac
