# Personal Hub - API کامل توسعه فردی و مدیریت زندگی

پروژه **Django + DRF** کاملاً قابل توسعه برای ثبت عادات، تسک‌ها (Todo)، یادآورها، تراکنش‌های مالی و اتصال به ربات تلگرام.

- **API-first**: مناسب وب، اپ موبایل، و ربات
- **Single Database** (SQLite پیش‌فرض، آماده PostgreSQL)
- **JWT Authentication** برای همه کلاینت‌ها
- **ربات تلگرام** داخل پروژه (بدون نیاز به API جدا)
- **ساختار ماژولار** برای اضافه کردن فیچرهای جدید (مثل Journal، Mood Tracker، Goals و ...)

## ساختار پروژه

```
personal_hub/
├── personal_hub/          # تنظیمات اصلی
├── accounts/              # User + Profile (تلگرام chat_id)
├── habits/                # عادات + لاگ روزانه + استریک
├── todos/                 # تسک‌ها با ساب‌تسک و اولویت
├── reminders/             # یادآور با GenericForeignKey (قابل لینک به همه چیز)
├── finance/               # درآمد/هزینه + دسته‌بندی + گزارش
├── telegram_bot/          # ربات تلگرام (دستورات سریع + polling)
├── core/                  # BaseModel, Permissions, Utils (قابل استفاده در اپ‌های جدید)
├── manage.py
├── requirements.txt
└── README.md
```

## نصب و راه‌اندازی

1. **کلون یا دانلود زیپ**

2. **ایجاد محیط مجازی و نصب وابستگی‌ها**
   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/Mac
   # venv\Scripts\activate   # Windows

   pip install -r requirements.txt
   ```

3. **تنظیمات**
   - فایل `personal_hub/settings.py` را باز کنید
   - `SECRET_KEY` را تغییر دهید
   - `TELEGRAM_BOT_TOKEN` را ست کنید (از @BotFather)
   - اگر از PostgreSQL استفاده می‌کنید، بخش DATABASES را تغییر دهید

4. **مایگریشن‌ها**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **ایجاد سوپر یوزر**
   ```bash
   python manage.py createsuperuser
   ```

6. **اجرای سرور**
   ```bash
   python manage.py runserver
   ```

   API در `http://127.0.0.1:8000/api/` در دسترس است.

## استفاده از API

### احراز هویت (JWT)
- ثبت‌نام: `POST /api/register/`
  ```json
  {"username": "yasin", "email": "...", "password": "...", "password2": "..."}
  ```
- لاگین: `POST /api/token/` → access + refresh token بگیرید
- استفاده: هدر `Authorization: Bearer <access_token>`

- اطلاعات کاربر: `GET /api/me/`

### عادات (Habits)
- لیست/ایجاد: `GET/POST /api/habits/`
- ثبت سریع امروز: `POST /api/habits/{id}/log/`
  ```json
  {"completed": true, "count": 1, "notes": "عالی بود"}
  ```
- آمار: `GET /api/habits/stats/`

### تسک‌ها (Todos)
- `GET/POST /api/todos/`
- تغییر وضعیت: `POST /api/todos/{id}/change_status/`
- تسک‌های عقب‌افتاده: `GET /api/todos/overdue/`

### یادآورها (Reminders)
- `GET/POST /api/reminders/`
- نزدیک‌ترین‌ها: `GET /api/reminders/upcoming/`

### مالی (Finance)
- تراکنش‌ها: `GET/POST /api/finance/transactions/`
- گزارش: `GET /api/finance/transactions/summary/?period=month`
- دسته‌بندی‌ها: `GET /api/finance/transactions/categories/`

## ربات تلگرام

1. توکن را در settings.py بگذارید.
2. ربات را اجرا کنید:
   ```bash
   python manage.py runbot
   ```
3. در تلگرام `/start` بزنید.
4. Chat ID خود را از ربات بگیرید و در پروفایل وب/اپ (`PATCH /api/me/`) وارد کنید تا حساب لینک شود.

دستورات ربات:
- `/habits` , `/log ورزش` , `/todos` , `/addtodo خرید نان` , `/balance` , `/reminders`

## گسترش پروژه (Extensibility)

برای اضافه کردن ماژول جدید (مثل Journal):

1. `python manage.py startapp journal`
2. در `journal/models.py` از `core.models.BaseModel` ارث ببرید.
3. ViewSet + Serializer بسازید (مشابه habits).
4. در `personal_hub/urls.py` اضافه کنید: `path('api/journal/', include('journal.urls'))`
5. در `INSTALLED_APPS` اضافه کنید.
6. مایگریت کنید.

همه چیز آماده است: permissions، filtering، pagination، JWT.

## نکات

- **دیتابیس واحد**: همه اپ‌ها از یک DB استفاده می‌کنند.
- **توسعه‌پذیری بالا**: GenericForeignKey در reminders، BaseModel مشترک، utils مشترک.
- **فارسی**: تنظیمات TIME_ZONE و LANGUAGE_CODE روی ایران است.
- **Production**: DEBUG=False،ALLOWED_HOSTS را محدود کنید، از gunicorn + nginx + PostgreSQL استفاده کنید.
- **Celery** (اختیاری): برای ارسال نوتیفیکیشن‌های یادآور در بک‌گراند می‌توانید اضافه کنید.

ساخته شده برای **یاسین** - توسعه فردی قدرتمند و قابل گسترش 🚀

هر سوالی داشتی یا خواستی فیچر جدیدی اضافه کنم، بگو!
