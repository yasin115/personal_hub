# ربات تلگرام Personal Hub

بازطراحی کامل با **aiogram 3.x**، تجربه کاربری کامل با دکمه‌های منویی (Reply Keyboard) و شیشه‌ای (Inline Keyboard)، فرم‌های چند مرحله‌ای (FSM) و اتصال حساب با کد یکبار مصرف.

## اجرا

```bash
export TELEGRAM_BOT_TOKEN="توکن ربات شما از BotFather"
python manage.py migrate          # برای ساخت جدول TelegramLinkCode
python manage.py runbot           # اجرای ربات با polling
```

## ساختار پوشه

```
telegram_bot/
├── bot.py                  # نقطه ورود: Dispatcher، Middleware، اتصال روترها
├── models.py               # TelegramLinkCode (کد اتصال حساب)
├── states.py               # FSM StatesGroup برای فرم‌های چند مرحله‌ای
├── middlewares.py          # DjangoUserMiddleware: کاربر جنگو را برای هر پیام پیدا می‌کند
├── utils.py                # همه‌ی دسترسی‌های ORM (async) + فرمت‌دهی و پارس تاریخ/مبلغ
├── views.py / urls.py      # وبهوک (اختیاری) + API اتصال/قطع اتصال حساب برای سایت/اپ
├── admin.py, migrations/   # مدیریت TelegramLinkCode در پنل ادمین
├── keyboards/
│   ├── menus.py            # منوی پایین صفحه (Reply Keyboard) - همیشه ثابت
│   └── inline.py           # همه دکمه‌های شیشه‌ای: لیست‌ها، ویزاردها، تاییدها، صفحه‌بندی
└── handlers/
    ├── __init__.py          # همه روترها اینجا جمع می‌شوند (all_routers)
    ├── _shared.py           # کمکی مشترک: require_linked()
    ├── common.py            # /start /help /menu /cancel /settings + پیام نامشخص
    ├── linking.py           # اتصال/قطع اتصال حساب با کد یکبار مصرف
    ├── habits.py            # لیست/ثبت/آمار/فعال‌سازی/حذف عادت + ویزارد افزودن
    ├── todos.py             # لیست/تکمیل/حذف کار + ویزارد افزودن (عنوان→اولویت→سررسید)
    ├── finance.py           # خلاصه مالی/تراکنش‌های اخیر/حذف + ویزارد افزودن تراکنش
    └── reminders.py          # لیست/فعال‌سازی/حذف یادآور + ویزارد افزودن
```

## دستورات ربات

| دستور | کاربرد |
|---|---|
| `/start` | شروع + وضعیت اتصال حساب |
| `/menu` | نمایش منوی اصلی (دکمه‌های پایین صفحه) |
| `/habits` | لیست و مدیریت عادت‌ها |
| `/todos` | لیست و مدیریت کارها |
| `/balance` | خلاصه مالی و ثبت تراکنش |
| `/reminders` | لیست و مدیریت یادآورها |
| `/settings` | تنظیمات و قطع اتصال حساب |
| `/link` | دریافت کد اتصال حساب |
| `/cancel` | لغو فرم چند مرحله‌ای جاری |
| `/help` | راهنما |

همه این دستورات از طریق منوی پایین صفحه (دکمه‌های 📋 ✅ 💰 🔔 ⚙️ ❓) هم در دسترس‌اند.

## اتصال حساب (بدون فرانت هنوز، ولی API آماده است)

1. کاربر در ربات `/start` یا `/link` می‌زند → یک کد ۶ رقمی با اعتبار ۱۰ دقیقه می‌گیرد.
2. کاربر در سایت/اپ (بعد از لاگین) کد را وارد می‌کند.
3. سایت/اپ درخواست زیر را می‌زند:

```
POST /api/telegram/webhook/verify-link/
Authorization: Bearer <JWT>
{"code": "123456"}
```

این خودش `Profile.telegram_chat_id` کاربر را ست می‌کند. برای قطع اتصال هم:

```
POST /api/telegram/webhook/unlink/
Authorization: Bearer <JWT>
```

> نکته: چون این دو مسیر داخل `telegram_bot/urls.py` تعریف شده‌اند و آن اپ در
> `personal_hub/urls.py` روی `api/telegram/webhook/` مونت شده، آدرس نهایی
> کمی عجیب می‌شود (`.../webhook/verify-link/`). اگر می‌خواهید تمیزتر باشد
> (`/api/telegram/verify-link/`)، کافیست در `personal_hub/urls.py` مقدار
> prefix همان include را به `api/telegram/` تغییر دهید -- چیزی داخل این اپ
> نیاز به تغییر ندارد.

## افزودن یک قابلیت جدید (مثلاً «یادداشت‌ها»)

1. اگر مدل جدید لازم است، در اپ جنگوی مربوطه (یا اپ جدید) بسازید.
2. توابع دسترسی به دیتابیس (async) را در `utils.py` اضافه کنید.
3. کیبوردهای لازم را در `keyboards/inline.py` اضافه کنید.
4. یک فایل `handlers/notes.py` با یک `Router` جدید بسازید (از روی `habits.py` کپی بگیرید، ساختار مشابه است).
5. روتر جدید را در `handlers/__init__.py` به `all_routers` اضافه کنید.

همین! نیازی به تغییر `bot.py` یا هیچ فایل دیگری نیست.
