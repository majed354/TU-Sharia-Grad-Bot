# 🎓 بوت مساعد الدراسات العليا — Telegram RAG Bot

بوت تيليغرام ذكي يجيب عن تساؤلات الدراسات العليا بناءً على المستندات المُدخلة، مع نظام تصعيد تلقائي للمشرف عند عدم وجود إجابة واثقة.

## 🏗️ الهندسة المعمارية

```
المستخدم ← Telegram ← Webhook (FastAPI)
                              ↓
                    تحويل السؤال إلى Embedding (OpenAI)
                              ↓
                    بحث في ChromaDB (أقرب 5 مقاطع)
                              ↓
                   ┌─ درجة تشابه كافية؟
                   │
                   ├─ نعم → توليد إجابة (Kimi 2.5 via OpenRouter)
                   │         → تقييم الثقة
                   │         → إرسال للمستخدم
                   │
                   └─ لا → تصعيد للمشرف مع السياق الكامل
```

## 📁 هيكلية المشروع

```
grad-assistant-bot/
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── requirements.txt
├── app/
│   ├── main.py           # FastAPI + Webhook
│   ├── bot.py            # معالجات البوت
│   ├── config.py         # الإعدادات
│   ├── escalation.py     # نظام التصعيد
│   └── rag/
│       ├── engine.py     # محرك RAG
│       └── ingest.py     # تجهيز المستندات
├── documents/            # ضع ملفات .txt هنا
└── data/                 # تخزين ChromaDB
```

## 🚀 التشغيل السريع

### 1. استنساخ المشروع
```bash
git clone https://github.com/YOUR_USER/grad-assistant-bot.git
cd grad-assistant-bot
```

### 2. إعداد المتغيرات
```bash
cp .env.example .env
nano .env  # عدّل القيم
```

### 3. إضافة المستندات
```bash
# ضع ملفات .txt في مجلد documents/
cp your_docs/*.txt documents/
```

### 4. تشغيل بـ Docker
```bash
docker compose up -d --build
```

### 5. تجهيز قاعدة المعرفة (مرة واحدة)
```bash
docker compose exec bot python -m app.rag.ingest
```

### 6. ربط Webhook تيليغرام
```bash
# يتم تلقائياً عند التشغيل، أو يدوياً:
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<YOUR_DOMAIN>/webhook"
```

## 🔧 الإعداد على VPS (Hostinger KVM)

```bash
# 1. تحديث النظام
sudo apt update && sudo apt upgrade -y

# 2. تثبيت Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 3. تثبيت Docker Compose
sudo apt install docker-compose-plugin -y

# 4. تثبيت Nginx + Certbot
sudo apt install nginx certbot python3-certbot-nginx -y

# 5. إعداد SSL (بعد توجيه الدومين)
sudo certbot --nginx -d yourdomain.com

# 6. إعداد Nginx كـ reverse proxy — انظر nginx.conf في المشروع
```

## 📝 إضافة مستندات جديدة

```bash
# 1. أضف الملفات الجديدة إلى documents/
# 2. أعد تشغيل عملية التجهيز
docker compose exec bot python -m app.rag.ingest
```

## 🔑 المتطلبات

- مفتاح OpenRouter API (لـ Kimi 2.5)
- مفتاح OpenAI API (للـ Embeddings فقط)
- توكن بوت تيليغرام (من @BotFather)
- معرّف تيليغرام الخاص بك (من @userinfobot)
