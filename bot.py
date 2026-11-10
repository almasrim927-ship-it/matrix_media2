import logging
import requests
import asyncio
import json
import os
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "9204783274:AAFZt3-UmOFxDwzKIUmAnEZ3M8vbn3Eiulk"
ALERT_GROUP_ID = -1001234567890 

# تم تحديث مفتاح الـ API الجديد بالكامل هنا
ALKABOS_API_KEY = "ee8c91eeae41cb967e8e9434197afd8b"
ALKABOS_API_URL = "https://alkabos.com/api/v2"

NEW_API_KEY = "ee8c91eeae41cb967e8e9434197afd8b"
NEW_API_URL = "https://alkabos.com/api/v2" 

ADMIN_ID = 6764960829
CURRENCY = "JOD"
ORANGE_WALLET = "@ALMASRIM299"
PROVIDER_NAME = "Momen Almasri"
SUPPORT_CONTACT = "@Momen_Almasri"

DATA_FILE = "users_data.json"
PROMO_FILE = "promo_codes.json"
TICKETS_FILE = "support_tickets.json"
MAINTENANCE_FILE = "maintenance_settings.json"
SPAM_LOG_FILE = "spam_attacks.json"

def load_json(filename, default_val):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return {int(k) if str(k).isdigit() else k: v for k, v in data.items()} if isinstance(data, dict) else data
            except json.JSONDecodeError:
                return default_val
    return default_val

def save_json(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Error saving {filename}: {e}")

users_db = load_json(DATA_FILE, {})
promo_codes = load_json(PROMO_FILE, {"MATRIX2026": 1.00})
support_tickets = load_json(TICKETS_FILE, {})
maintenance_settings = load_json(MAINTENANCE_FILE, {"bot": False, "categories": {}, "services": {}})
spam_attacks = load_json(SPAM_LOG_FILE, {})

pending_deposits = {}
deposit_counter = 1
ticket_counter = 1
user_last_msg_time = {}

def save_users_to_file():
    save_data = {str(k): v for k, v in users_db.items()}
    save_json(DATA_FILE, save_data)

def save_spam_logs():
    save_json(SPAM_LOG_FILE, {str(k): v for k, v in spam_attacks.items()})

def log_user_transaction(user_id, amount, description):
    if user_id in users_db:
        if "transactions" not in users_db[user_id]:
            users_db[user_id]["transactions"] = []
        users_db[user_id]["transactions"].append({
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "amount": amount,
            "description": description
        })
        save_users_to_file()

SERVICES = {
    "facebook": {
        "name": "📘 خدمات فيسبوك",
        "items": [
            {"id": 3884, "title": "متابعين فيسبوك | سرعة عالية (بدون تعبئة)", "price": 0.22, "min": 10},
            {"id": 4823, "title": "متابعين فيسبوك | حسابات قديمة + تعويض 30 يوم", "price": 0.29, "min": 10},
            {"id": 4914, "title": "متابعين فيسبوك فيتنامي | تعويض 30 يوم", "price": 0.26, "min": 500},
            {"id": 4564, "title": "متابعين فيسبوك | تعويض مدى الحياة", "price": 0.26, "min": 100},
            {"id": 2129, "title": "متابعين فيسبوك سوريين + عرب 🇸🇦🇸🇾 (ضمان 365 يوم)", "price": 1.00, "min": 1000},
            {"id": 2529, "title": "متابعين صفحة فيسبوك مصريين 100% (ضمان 30 يوم)", "price": 1.00, "min": 1000},
            {"id": 4870, "title": "مشاهدات فيسبوك فيديو / ريلز فوري", "price": 0.13, "min": 100},
            {"id": 3400, "title": "إعجابات منشور فيسبوك ميكس (صفحات مصرية)", "price": 0.70, "min": 250},
            {"id": 2623, "title": "تعليقات مخصصة فيسبوك مصريين ضمان مدى الحياة", "price": 1.70, "min": 100},
        ]
    },
    "instagram": {
        "name": "📸 خدمات إنستغرام",
        "items": [
            {"id": 1083870, "title": "مشاركات انستا مجانا (1000 مشاركة) [مؤقت 24س]", "price": 0.00, "min": 1000, "provider": "new", "free_cooldown": True},
            {"id": 4790, "title": "إعجابات انستقرام (لايكات ريلز) ❤️", "price": 0.45, "min": 10, "desc": "❤️ إعجابات انستقرام (لايكات ريلز)\n📊 حد اقصى 1 مليون | جودة حقيقية | 🚀 سرعة 100 ألف يومياً | ⚡ بدء فوري | 🔘 يدعم الإلغاء | ⚠️ بدون تعويض"},
            {"id": 4882, "title": "متابعين انستقرام [حسابات قديمة داتا 2014-2025] 👥", "price": 2.00, "min": 10, "desc": "👥 متابعين انستقرام [ حسابات قديمة داتا 2014 - 2025 ]\n📊 حد اقصى 150 ألف | 🚀 سرعة 100 ألف يومياً | ⚡ بدء فوري | ⚠️ ملاحظة هامة: هذه الخدمة يوجد بها نقص."},
            {"id": 1550, "title": "مشاهدات إنستغرام (فيديو ريلز) 🎥", "price": 0.03, "min": 100, "desc": "🎥 مشاهدات إنستغرام (فيديو ريلز)\n🔗 جميع الروابط | ⚡ سرعة فائقة وتنفيذ فوري [100 مليون في اليوم]"},
            {"id": 354, "title": "حفظ انستقرام (فيديو ريلز) 📥", "price": 0.75, "min": 10, "desc": "📥 حفظ انستقرام (فيديو ريلز)\n👥 جودة عالية | 🎯 الحد الأقصى 100 ألف | ⚡ سرعة 100 ألف يوميًا | 🚀 بدء فوري | ❌ بدون إعادة تعبئة"},
            {"id": 338, "title": "مشاركات إنستجرام (فيديو ريلز) ↗️", "price": 0.20, "min": 10, "desc": "↗️ مشاركات إنستجرام (فيديو ريلز)\n💯 مستقر ويعمل بنسبة 100% | ♻️ إعادة تعبئة 365 يوم"},
            {"id": 3805, "title": "إعادة نشر علي انستقرام (فيديو ريلز) 📲", "price": 0.50, "min": 10, "desc": "📲 إعادة نشر علي انستقرام (فيديو ريلز)\n👥 حسابات متنوعة | 🎯 حد أقصى 100 ألف | ⚡ سرعة 100 ألف يوميًا | 🚀 فوري | 🛡️ ضمان 30 يوم"},
            {"id": 3448, "title": "مشاهدات ستوري إنستجرام 📱", "price": 0.20, "min": 100, "desc": "📱 مشاهدات ستوري إنستجرام\n📈 حتى 200 ألف مشاهدة | 🎯 لجميع الستوريات | ⚡ سرعة تنفيذ تصل إلى 200 ألف يوميًا | 🔥 إنجاز فائق السرعة | 🔄 بدون تعويض"},
        ]
    },
    "tiktok": {
        "name": "🎵 خدمات تيك توك",
        "items": [
            {"id": 1340, "title": "متابعين تيك توك مصريين 100% حقيقي نشط", "price": 4.00, "min": 1000},
            {"id": 3570, "title": "مشاهدات تيك توك من السعودية", "price": 0.28, "min": 100},
            {"id": 4888, "title": "متابعين تيك توك | السرعة 10 آلاف يومياً", "price": 0.85, "min": 100},
            {"id": 4786, "title": "متابعين تيك توك | الأرخص (ضمان 7 أيام)", "price": 1.10, "min": 10},
            {"id": 4912, "title": "إعجابات تيك توك | ضمان مدى الحياة", "price": 0.68, "min": 10},
            {"id": 4278, "title": "مشاهدات تيك توك | ضمان 30 يوم", "price": 0.15, "min": 100},
            {"id": 4654, "title": "لايكات على تعليق تيك توك | ضمان 30 يوم", "price": 0.16, "min": 10},
            {"id": 3561, "title": "شحن عملات تيك توك (عدد غير محدود)", "price": 9.60, "min": 500},
        ]
    },
    "telegram": {
        "name": "✈️ خدمات تيليجرام",
        "items": [
            {"id": 4579, "title": "أعضاء تيليجرام عرب 🇦🇪 | ضمان 30 يوماً", "price": 0.40, "min": 50},
            {"id": 1873, "title": "أعضاء تيليجرام 100% عرب 🇸🇦 | تعويض 30 يوم", "price": 1.20, "min": 10},
            {"id": 4720, "title": "أعضاء تيليجرام جودة عالية | تعويض 30 يوم", "price": 0.45, "min": 1000},
            {"id": 4190, "title": "بدء بوت تيليجرام | الأرخص", "price": 0.22, "min": 100},
            {"id": 4166, "title": "تفاعلات تيليجرام إيجابية متنوعة + مشاهدات", "price": 0.112, "min": 10},
            {"id": 4173, "title": "مشاهدات منشورات تيليجرام (آخر منشور)", "price": 0.105, "min": 500},
            {"id": 681, "title": "توثيق تليجرام بريميوم [شهري]", "price": 4.60, "min": 1},
        ]
    },
    "youtube": {
        "name": "▶️ خدمات يوتيوب",
        "items": [
            {"id": 4663, "title": "ساعات مشاهدة يوتيوب | ضمان 30 يوم", "price": 15.10, "min": 100},
            {"id": 2962, "title": "مشتركين يوتيوب | جودة عالية بدون ضمان", "price": 0.11, "min": 10},
            {"id": 1886, "title": "مشتركين يوتيوب | ضمان 30 يوم مستقرة", "price": 14.10, "min": 10},
            {"id": 4738, "title": "إعجابات يوتيوب | ضمان 30 يوم", "price": 0.32, "min": 50},
            {"id": 3580, "title": "مشاهدات يوتيوب عرب 100% (إعلانات ممولة)", "price": 0.60, "min": 100},
            {"id": 3741, "title": "تعليقات يوتيوب مخصصة | ضمان 30 يوم", "price": 1.20, "min": 10},
            {"id": 3649, "title": "يوتيوب بريميوم | تفعيل 3 شهور لحسابك الشخصي", "price": 4.10, "min": 1},
        ]
    }
}
def place_provider_order(link: str, quantity: int, service_id: int, provider_type="alkabos"):
    url = NEW_API_URL if provider_type == "new" else ALKABOS_API_URL
    api_key = NEW_API_KEY if provider_type == "new" else ALKABOS_API_KEY
    data = {"key": api_key, "action": "add", "service": service_id, "link": link, "quantity": quantity}
    try:
        response = requests.post(url, data=data, timeout=15)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def manage_provider_order(action_type: str, order_id: int):
    data = {"key": ALKABOS_API_KEY, "action": action_type, "order": order_id}
    try:
        response = requests.post(ALKABOS_API_URL, data=data, timeout=15)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def check_order_status_api(order_id: int):
    data = {"key": ALKABOS_API_KEY, "action": "status", "order": order_id}
    try:
        response = requests.post(ALKABOS_API_URL, data=data, timeout=15)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def get_provider_balance():
    data = {"key": ALKABOS_API_KEY, "action": "balance"}
    try:
        response = requests.post(ALKABOS_API_URL, data=data, timeout=10)
        res = response.json()
        if "balance" in res:
            return f"{res['balance']} {res.get('currency', 'USD')}"
        return f"غير متوفر: {res}"
    except Exception as e:
        return f"خطأ اتصال: {str(e)}"

def main_menu_keyboard(is_admin=False):
    keyboard = [
        [InlineKeyboardButton("🛒 قسائم ومنصات الخدمات", callback_data="categories_menu"), InlineKeyboardButton("🔍 بحث عن خدمة", callback_data="search_service")],
        [InlineKeyboardButton("💰 رصيدي", callback_data="check_balance"), InlineKeyboardButton("💳 اضافه رصيد", callback_data="add_balance_menu")],
        [InlineKeyboardButton("🎟️ كود ترويجي", callback_data="promo_menu"), InlineKeyboardButton("📜 طلباتي السابقة", callback_data="my_orders")],
        [InlineKeyboardButton("🔍 استعلام عن طلب", callback_data="check_order_status"), InlineKeyboardButton("🎫 تذاكر الدعم الفني", callback_data="support_tickets_menu")],
        [InlineKeyboardButton("📞 التواصل المباشر", callback_data="support_menu")],
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton("👑 لوحة تحكم الإدارة", callback_data="admin_panel")])
    return InlineKeyboardMarkup(keyboard)

async def anti_spam_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    if not user:
        return False
    user_id = user.id
    if user_id == ADMIN_ID:
        return False

    current_time = time.time()
    last_time = user_last_msg_time.get(user_id, 0.0)

    if current_time - last_time < 0.7:
        user_last_msg_time[user_id] = current_time
        u_str = str(user_id)
        
        if u_str not in spam_attacks:
            spam_attacks[u_str] = {
                "username": user.username or user.first_name,
                "count": 1,
                "last_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            spam_attacks[u_str]["count"] += 1
            spam_attacks[u_str]["last_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        save_spam_logs()

        try:
            alert_text = (
                f"🚨 **رصد هجوم / سبام (Anti-Spam)!**\n\n"
                f"👤 المستخدم: @{user.username or user.first_name}\n"
                f"🆔 الأيدي: `{user_id}`\n"
                f"🔢 عدد محاولات التكرار: `{spam_attacks[u_str]['count']}`\n"
                f"🕒 الوقت: `{spam_attacks[u_str]['last_time']}`"
            )
            kb = [
                [
                    InlineKeyboardButton("🚫 حظر المستخدم", callback_data=f"admin_ban_spam_{user_id}"),
                    InlineKeyboardButton("⚠️ إرسال تحذير", callback_data=f"admin_warn_spam_{user_id}")
                ]
            ]
            await context.bot.send_message(chat_id=ADMIN_ID, text=alert_text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        except Exception:
            pass

        if update.message:
            await update.message.reply_text("⚠️ **تنبيه:** يرجى عدم إرسال الرسائل بهذه السرعة لتجنب تقييد حسابك.")
        return True

    user_last_msg_time[user_id] = current_time
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    user_id = user.id
    is_admin = (user_id == ADMIN_ID)

    if user_id in users_db and users_db[user_id].get("banned", False) and not is_admin:
        if update.message:
            await update.message.reply_text("🚫 **عذراً، لقد تم حظرك من استخدام البوت بواسطة الإدارة.**", parse_mode="Markdown")
        return

    if maintenance_settings.get("bot", False) and not is_admin:
        maintenance_msg = "🛠️ **المتجر في وضع الصيانة حالياً!** عودوا قريباً!"
        if update.message:
            await update.message.reply_text(maintenance_msg, parse_mode="Markdown")
        elif update.callback_query:
            await update.callback_query.message.edit_text(maintenance_msg, parse_mode="Markdown")
        return

    if user_id not in users_db:
        users_db[user_id] = {
            "balance": 0.0, "username": user.username or user.first_name,
            "discount": 0.0, "orders": [], "transactions": [], "banned": False, "last_free_order": 0
        }
        save_users_to_file()
    else:
        users_db[user_id].setdefault("orders", [])
        users_db[user_id].setdefault("transactions", [])
        users_db[user_id].setdefault("banned", False)

    balance = users_db[user_id]["balance"]
    discount = users_db[user_id]["discount"]
    
    # تحديد حالة الحساب الأمنية حسب سجلات السبام
    u_str = str(user_id)
    if u_str in spam_attacks and spam_attacks[u_str].get("count", 0) > 0:
        security_status = f"⚠️ تنبيه ({spam_attacks[u_str].get('count')} محاولات تكرار)"
    else:
        security_status = "🟢 سليم وآمن تماماً"

    # الواجهة المطورة والمطلوبة بالخط الجميل مع JOD وحالة الحساب
    welcome_text = (
        f"🌟 **أهلاً بك يا {user.first_name} في متجر الخدمات الرقمية!**\n\n"
        f"👤 **معلومات الحساب:**\n"
        f"• الايدي الخاص بك (`ID`): `{user_id}`\n"
        f"• الرصيد الحالي: `{balance:.3f}` **{CURRENCY}**\n"
        f"• نسبة الخصم الفعالة: `{discount}%`\n"
        f"• حالة الحساب: **{security_status}**\n\n"
        f"💡 **نصائح ومعلومات مقترحة:**\n"
        f"1️⃣ تأكد أن الحسابات والروابط عامة وليست خاصة قبل إرسال الطلب لضمان التنفيذ الفوري.\n"
        f"2️⃣ يمكنك شحن رصيدك بكل سهولة عبر خيار (إضافة رصيد) وإرسال إيصال التحويل.\n"
        f"3️⃣ لخدمتك بشكل أفضل، احتفظ برقم الطلب (`Order ID`) الذي يظهر لك بعد كل عملية.\n\n"
        f"🚀 **المزود الرسمي:** `{PROVIDER_NAME}`\n"
        f"اختر ما يناسبك من الأزرار أدناه:"
    )

    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=main_menu_keyboard(is_admin), parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.message.edit_text(welcome_text, reply_markup=main_menu_keyboard(is_admin), parse_mode="Markdown")
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    user_id = query.from_user.id
    is_admin = (user_id == ADMIN_ID)

    if user_id in users_db and users_db[user_id].get("banned", False) and not is_admin:
        await query.message.edit_text("🚫 **عذراً، لقد تم حظرك من استخدام البوت.**", parse_mode="Markdown")
        return

    if maintenance_settings.get("bot", False) and not is_admin:
        await query.message.edit_text("🛠️ **المتجر في وضع الصيانة حالياً!**", parse_mode="Markdown")
        return

    if user_id not in users_db:
        users_db[user_id] = {"balance": 0.0, "username": query.from_user.username, "discount": 0.0, "orders": [], "transactions": [], "banned": False}
        save_users_to_file()

    data = query.data

    if data.startswith("admin_ban_spam_"):
        if not is_admin:
            return
        t_id = int(data.split("_")[3])
        users_db.setdefault(t_id, {"balance": 0.0, "username": "مخالف", "discount": 0.0, "orders": [], "transactions": [], "banned": False})
        users_db[t_id]["banned"] = True
        save_users_to_file()
        await query.answer(f"✅ تم حظر المخالف {t_id} بنجاح!", show_alert=True)
        return

    if data.startswith("admin_warn_spam_"):
        if not is_admin:
            return
        t_id = int(data.split("_")[3])
        try:
            await context.bot.send_message(chat_id=t_id, text="⚠️ **تنبيه هام من الإدارة:**\nتم رصد إرسال طلبات متكررة بشكل مخالف. يرجى التوقف لتجنب حظر حسابك.", parse_mode="Markdown")
            await query.answer("✅ تم إرسال التحذير بنجاح!", show_alert=True)
        except Exception as e:
            await query.answer(f"❌ فشل الإرسال: {e}", show_alert=True)
        return

    if data == "main_menu":
        balance = users_db[user_id]["balance"]
        discount = users_db[user_id]["discount"]
        
        u_str = str(user_id)
        if u_str in spam_attacks and spam_attacks[u_str].get("count", 0) > 0:
            security_status = f"⚠️ تنبيه ({spam_attacks[u_str].get('count')} محاولات)"
        else:
            security_status = "🟢 سليم وآمن تماماً"

        text = (
            f"📋 **القائمة الرئيسية:**\n\n"
            f"🆔 الايدي الخاص بك: `{user_id}`\n"
            f"💰 رصيدك الحالي: `{balance:.3f}` **{CURRENCY}**\n"
            f"🛡️ حالة الحساب: **{security_status}**\n\n"
            f"اختر القسم المطلوب من الأزرار بالأسفل:"
        )
        await query.message.edit_text(text, reply_markup=main_menu_keyboard(is_admin), parse_mode="Markdown")

    elif data == "check_balance":
        balance = users_db[user_id]["balance"]
        await query.message.edit_text(
            f"💰 **حساب الرصيد المالي:**\n\n• الرصيد الحالي: `{balance:.3f}` **{CURRENCY}**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]]),
            parse_mode="Markdown"
        )

    elif data == "my_orders":
        user_orders = users_db[user_id].get("orders", [])
        if not user_orders:
            text = "📜 **سجل طلباتك السابقة:**\n\nلم تقم بأي طلبات حتى الآن."
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]]
        else:
            text = "📜 **آخر طلباتك السابقة:**\n\n"
            keyboard = []
            for ord in user_orders[-5:]:
                o_id = ord['order_id']
                text += f"🆔 رقم الطلب: `{o_id}` | الكمية: `{ord['quantity']}`\n"
                keyboard.append([
                    InlineKeyboardButton(f"⚡ تسريع #{o_id}", callback_data=f"refill_ord_{o_id}"),
                    InlineKeyboardButton(f"🔄 تعويض #{o_id}", callback_data=f"status_ord_{o_id}")
                ])
            keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")])
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("refill_ord_"):
        o_id = int(data.split("_")[2])
        res = manage_provider_order("refill", o_id)
        await query.message.reply_text(f"⚡ **نتيجة تسريع الطلب #{o_id}:**\n`{res}`", parse_mode="Markdown")

    elif data.startswith("status_ord_"):
        o_id = int(data.split("_")[2])
        status_res = check_order_status_api(o_id)
        if "error" in status_res:
            await query.message.reply_text(f"❌ خطأ: {status_res['error']}")
        else:
            await query.message.reply_text(f"🔍 حالة الطلب #{o_id}:\nالحالة: `{status_res.get('status')}`\nالمتبقي: `{status_res.get('remains')}`", parse_mode="Markdown")

    elif data == "search_service":
        context.user_data["waiting_for_search_query"] = True
        await query.message.edit_text("🔍 **البحث السريع:**\n\nأرسل كلمة مفتاحية للخدمة:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]]), parse_mode="Markdown")

    elif data == "check_order_status":
        context.user_data["waiting_for_status_id"] = True
        await query.message.edit_text("🔍 **الاستعلام عن حالة الطلب:**\n\nأرسل رقم الطلب (`Order ID`) الآن:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]]), parse_mode="Markdown")

    elif data == "promo_menu":
        context.user_data["waiting_for_promo_code"] = True
        await query.message.edit_text("🎟️ **كود ترويجي:**\n\nأرسل الكود الآن:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]]), parse_mode="Markdown")

    elif data == "support_menu":
        await query.message.edit_text(f"📞 **الدعم الفني:**\n\nللتواصل: {SUPPORT_CONTACT}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]]), parse_mode="Markdown")

    elif data == "support_tickets_menu":
        user_ticks = support_tickets.get(str(user_id), [])
        ticks_text = "🎫 **نظام تذاكر الدعم الفني:**\n\n"
        if not user_ticks:
            ticks_text += "ليس لديك أي تذاكر مفتوحة."
        else:
            for t in user_ticks:
                ticks_text += f"📌 تذكرة #{t['id']} | الحالة: `{t['status']}`\n💬 الرسالة: {t['msg']}\n📬 الرد: {t['reply']}\n---\n"
        await query.message.edit_text(ticks_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➕ فتح تذكرة", callback_data="create_new_ticket")], [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]]), parse_mode="Markdown")

    elif data == "create_new_ticket":
        context.user_data["waiting_for_ticket_msg"] = True
        await query.message.edit_text("🎫 **فتح تذكرة جديدة**\n\nاكتب شكواك أو استفسارك في رسالة:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء", callback_data="support_tickets_menu")]]), parse_mode="Markdown")

    elif data == "categories_menu":
        keyboard = []
        for cat_key, cat_info in SERVICES.items():
            if maintenance_settings.get("categories", {}).get(cat_key, False):
                keyboard.append([InlineKeyboardButton(f"{cat_info['name']} (صيانة 🛠️)", callback_data="cat_maint_alert")])
            else:
                keyboard.append([InlineKeyboardButton(cat_info["name"], callback_data=f"cat_{cat_key}")])
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")])
        await query.message.edit_text("📂 **اختر المنصة المطلوبة:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "cat_maint_alert":
        await query.answer("عذراً، هذا القسم مغلق للصيانة مؤقتاً.", show_alert=True)

    elif data.startswith("cat_"):
        cat_key = data.split("_")[1]
        cat_info = SERVICES.get(cat_key)
        keyboard = []
        for item in cat_info["items"]:
            s_id_str = str(item["id"])
            if maintenance_settings.get("services", {}).get(s_id_str, False):
                keyboard.append([InlineKeyboardButton(f"{item['title']} (صيانة 🛠️)", callback_data="srv_maint_alert")])
            else:
                keyboard.append([InlineKeyboardButton(f"{item['title']} | سعر 1000: {item['price']} {CURRENCY}", callback_data=f"srv_{cat_key}_{item['id']}")])
        keyboard.append([InlineKeyboardButton("🔙 رجوع للأقسام", callback_data="categories_menu")])
        await query.message.edit_text(f"✨ **قائمة خدمات {cat_info['name']}**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "srv_maint_alert":
        await query.answer("عذراً، هذه الخدمة مغلقة للصيانة مؤقتاً.", show_alert=True)

    elif data.startswith("srv_"):
        parts = data.split("_")
        service_id = int(parts[2])
        cat_key = parts[1]
        selected_service = next((i for i in SERVICES[cat_key]["items"] if i["id"] == service_id), None)
        if not selected_service:
            await query.message.edit_text("❌ الخدمة غير موجودة.", reply_markup=main_menu_keyboard(is_admin))
            return

        context.user_data.update({
            "active_service_id": service_id, "active_service_title": selected_service["title"],
            "active_service_price": selected_service["price"], "active_service_min": selected_service["min"],
            "active_service_provider": selected_service.get("provider", "alkabos"),
            "waiting_for_calc_quantity": True
        })
        
        await query.message.edit_text(
            f"🎯 **الخدمة المختارة:**\n`{selected_service['title']}`\n\n• السعر لكل 1000: `{selected_service['price']}` **{CURRENCY}**\n• الحد الأدنى: `{selected_service['min']}`\n\n🧮 **أرسل الآن الكمية المطلوبة (أرقام فقط):**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء", callback_data=f"cat_{cat_key}")]]), parse_mode="Markdown"
        )

    elif data == "confirm_order":
        service_id = context.user_data.get("active_service_id")
        link = context.user_data.get("order_link")
        quantity = context.user_data.get("order_quantity")
        total_cost = context.user_data.get("order_total_cost")
        provider_type = context.user_data.get("active_service_provider", "alkabos")

        if users_db[user_id]["balance"] < total_cost:
            await query.message.edit_text("❌ رصيدك غير كافٍ.", reply_markup=main_menu_keyboard(is_admin))
            return

        users_db[user_id]["balance"] -= total_cost
        api_result = place_provider_order(link, quantity, service_id, provider_type)

        if "order" in api_result:
            order_id = api_result["order"]
            users_db[user_id]["orders"].append({"order_id": order_id, "quantity": quantity, "cost": round(total_cost, 3)})
            save_users_to_file()
            await query.message.edit_text(f"✅ **تم تنفيذ الطلب بنجاح!**\n🆔 رقم الطلب: `{order_id}`\n💸 التكلفة: `{total_cost:.3f}` **{CURRENCY}**", reply_markup=main_menu_keyboard(is_admin), parse_mode="Markdown")
        else:
            users_db[user_id]["balance"] += total_cost
            save_users_to_file()
            err_desc = api_result.get("error", api_result)
            await query.message.edit_text(f"❌ **خطأ تقني:**\n`{err_desc}`\nتم إرجاع المبلغ لرصيدك.", reply_markup=main_menu_keyboard(is_admin), parse_mode="Markdown")

    elif data == "cancel_order":
        await query.message.edit_text("❌ تم إلغاء الطلب.", reply_markup=main_menu_keyboard(is_admin), parse_mode="Markdown")

    elif data == "add_balance_menu":
        await query.message.edit_text("💳 **اختر وسيلة الشحن:**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔶 Orange Money", callback_data="deposit_orange")], [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]]), parse_mode="Markdown")

    elif data == "deposit_orange":
        context.user_data["waiting_for_deposit_amount"] = True
        await query.message.edit_text(f"💳 **شحن Orange Money**\nالتحويل للمحفظة: `{ORANGE_WALLET}`\n(تخصم 10 قروش عمولة عن كل دينار).\n\n💬 **أرسل المبلغ المحول (أرقام فقط):**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="add_balance_menu")]]), parse_mode="Markdown")

    # ================= لوحة تحكم الإدارة =================
    elif data == "admin_panel" and is_admin:
        m_status = "مفعل 🟢" if maintenance_settings.get("bot", False) else "معطل 🔴"
        kb = [
            [InlineKeyboardButton("👥 المستخدمين مع الأيدي", callback_data="admin_list_users"), InlineKeyboardButton("📊 كشف العملاء الشامل", callback_data="admin_clients_report")],
            [InlineKeyboardButton("📥 الإيصالات المعلقة والشحن", callback_data="admin_deposits_menu"), InlineKeyboardButton("📨 إشعار لمستخدم", callback_data="admin_send_notification")],
            [InlineKeyboardButton("🛠️ صيانة قسم أو خدمة", callback_data="admin_maintenance_menu"), InlineKeyboardButton("🛠️ صيانة البوت العامة", callback_data="toggle_maintenance")],
            [InlineKeyboardButton("🚨 هجمات ومخالفين السبام", callback_data="admin_spam_logs"), InlineKeyboardButton("🎟️ الأكواد", callback_data="admin_promo_menu")],
            [InlineKeyboardButton("➕ إضافة رصيد", callback_data="admin_add_bal"), InlineKeyboardButton("➖ خصم رصيد", callback_data="admin_sub_bal")],
            [InlineKeyboardButton("⚡ تسريع طلب", callback_data="admin_speed_order"), InlineKeyboardButton("❌ إلغاء طلب", callback_data="admin_cancel_order")],
            [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")]
        ]
        await query.message.edit_text(f"👑 **لوحة تحكم الإدارة:**\nصيانة البوت العامة: **{m_status}**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data == "admin_spam_logs" and is_admin:
        if not spam_attacks:
            text = "🛡️ **سجل الهجمات (Anti-Spam):**\n\nلم يتم رصد أي هجمات حتى الآن. النظام محمي تماماً! ✅"
            kb = [[InlineKeyboardButton("🔙 لوحة التحكم", callback_data="admin_panel")]]
        else:
            text = "🚨 **قائمة المخالفين والسبام المرصودين:**\n\n"
            kb = []
            for u_str, info in list(spam_attacks.items())[-10:]:
                u_id = int(u_str)
                text += f"👤 `@{info.get('username')}` | أيدي: `{u_id}`\n⚠️ المحاولات: `{info.get('count')}`\n🕒 الوقت: `{info.get('last_time')}`\n---\n"
                kb.append([InlineKeyboardButton(f"🚫 حظر {u_id}", callback_data=f"admin_ban_spam_{u_id}"), InlineKeyboardButton(f"🗑️ مسح السجل", callback_data=f"clear_spam_{u_id}")])
            kb.append([InlineKeyboardButton("🧹 مسح كافة السجلات", callback_data="clear_all_spam")])
            kb.append([InlineKeyboardButton("🔙 لوحة التحكم", callback_data="admin_panel")])
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data.startswith("clear_spam_") and is_admin:
        u_id = int(data.split("_")[2])
        if str(u_id) in spam_attacks:
            del spam_attacks[str(u_id)]
            save_spam_logs()
        await query.answer("🗑️ تمت الإزالة بنجاح.", show_alert=True)
        await query.message.edit_text("🗑️ تم مسح سجل هذا المستخدم.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="admin_spam_logs")]]))

    elif data == "clear_all_spam" and is_admin:
        spam_attacks.clear()
        save_spam_logs()
        await query.answer("🧹 تم مسح السجلات بالكامل!", show_alert=True)
        await query.message.edit_text("🧹 سجل الهجمات فارغ الآن.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة التحكم", callback_data="admin_panel")]]))

    elif data == "admin_clients_report" and is_admin:
        if not users_db:
            rep = "📂 لا يوجد عملاء بعد."
        else:
            rep = "📊 **كشف العملاء الشامل (الأرصدة والطلبات):**\n\n"
            for u_id, info in users_db.items():
                uname = info.get("username", "بدون")
                bal = info.get("balance", 0.0)
                disc = info.get("discount", 0.0)
                b_st = "🚫 محظور" if info.get("banned", False) else "✅ نشط"
                ords = info.get("orders", [])
                rep += f"👤 @{uname} | `{u_id}`\n💰 رصيد: `{bal:.3f}` {CURRENCY} | خصم: `{disc}%` | {b_st}\n📦 إجمالي الطلبات: `{len(ords)}` طلب\n-------------------\n"
        if len(rep) > 4000:
            rep = rep[:3950] + "\n...(تم الاقتطاع لطول النص)"
        await query.message.edit_text(rep, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة التحكم", callback_data="admin_panel")]]), parse_mode="Markdown")

    elif data == "admin_list_users" and is_admin:
        if not users_db:
            text = "📂 لا توجد بيانات."
        else:
            text = "👥 **قائمة المستخدمين والأيدي (IDs):**\n\n"
            for u_id, info in users_db.items():
                text += f"👤 @{info.get('username','بدون')} ── ID: `{u_id}`\n"
        if len(text) > 4000:
            text = text[:3950]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة التحكم", callback_data="admin_panel")]]), parse_mode="Markdown")

    elif data == "admin_send_notification" and is_admin:
        context.user_data["admin_action"] = "send_custom_notification_id"
        await query.message.edit_text("📨 **إرسال إشعار خاص لمستخدم:**\n\nأرسل الآن **أيدي المستخدم (ID)** المستهدف:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء", callback_data="admin_panel")]]), parse_mode="Markdown")

    elif data == "admin_maintenance_menu" and is_admin:
        kb = [
            [InlineKeyboardButton("📂 إيقاف/تفعيل منصة بالكامل", callback_data="maint_cat_list")],
            [InlineKeyboardButton("🎯 إيقاف/تفعيل خدمة محددة برقم ID", callback_data="maint_srv_input")],
            [InlineKeyboardButton("🔙 لوحة التحكم", callback_data="admin_panel")]
        ]
        await query.message.edit_text("🛠️ **إدارة الصيانة للأقسام والخدمات:**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data == "maint_cat_list" and is_admin:
        kb = []
        for k, info in SERVICES.items():
            is_m = maintenance_settings.get("categories", {}).get(k, False)
            st = "مفعل 🟢" if not is_m else "في الصيانة 🛠️"
            kb.append([InlineKeyboardButton(f"{info['name']} [{st}]", callback_data=f"toggle_cat_{k}")])
        kb.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_maintenance_menu")])
        await query.message.edit_text("اختر المنصة لتبديل حالة الصيانة:", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data.startswith("toggle_cat_") and is_admin:
        cat_k = data.split("_")[2]
        cur = maintenance_settings.setdefault("categories", {}).get(cat_k, False)
        maintenance_settings["categories"][cat_k] = not cur
        save_json(MAINTENANCE_FILE, maintenance_settings)
        await query.answer("تم تحديث حالة الصيانة بنجاح!", show_alert=True)
        kb = []
        for k, info in SERVICES.items():
            is_m = maintenance_settings.get("categories", {}).get(k, False)
            st = "مفعل 🟢" if not is_m else "في الصيانة 🛠️"
            kb.append([InlineKeyboardButton(f"{info['name']} [{st}]", callback_data=f"toggle_cat_{k}")])
        kb.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_maintenance_menu")])
        await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(kb))

    elif data == "maint_srv_input" and is_admin:
        context.user_data["admin_action"] = "toggle_service_maint_id"
        await query.message.edit_text("🎯 أرسل الآن **رقم معرف الخدمة (Service ID)** لتبديل حالة صيانتها:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء", callback_data="admin_maintenance_menu")]]), parse_mode="Markdown")

    elif data == "toggle_maintenance" and is_admin:
        maintenance_settings["bot"] = not maintenance_settings.get("bot", False)
        save_json(MAINTENANCE_FILE, maintenance_settings)
        s = "مفعل 🟢" if maintenance_settings["bot"] else "معطل 🔴"
        await query.message.edit_text(f"🛠️ تم تغيير صيانة البوت العامة إلى: **{s}**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة التحكم", callback_data="admin_panel")]]), parse_mode="Markdown")

    elif data == "admin_promo_menu" and is_admin:
        plist = "\n".join([f"🔑 `{k}` : `{v} {CURRENCY}`" for k, v in promo_codes.items()]) or "لا توجد أكواد."
        await query.message.edit_text(f"🎟️ **الأكواد الترويجية:**\n\n{plist}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➕ إضافة كود", callback_data="add_promo_step1")], [InlineKeyboardButton("🔙 لوحة التحكم", callback_data="admin_panel")]]), parse_mode="Markdown")

    elif data == "add_promo_step1" and is_admin:
        context.user_data["admin_action"] = "add_promo_code"
        await query.message.edit_text("➕ **أرسل الكود والقيمة هكذا:**\n`MATRIX 1.5`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء", callback_data="admin_panel")]]), parse_mode="Markdown")

    elif data == "admin_add_bal" and is_admin:
        context.user_data["admin_action"] = "add_balance_step1"
        await query.message.edit_text("➕ **أرسل أيدي (ID) المستخدم:**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء", callback_data="admin_panel")]]), parse_mode="Markdown")

    elif data == "admin_sub_bal" and is_admin:
        context.user_data["admin_action"] = "sub_balance_step1"
        await query.message.edit_text("➖ **أرسل أيدي (ID) المستخدم للخصم:**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء", callback_data="admin_panel")]]), parse_mode="Markdown")

    elif data == "admin_speed_order" and is_admin:
        context.user_data["admin_action"] = "speed_order_input"
        await query.message.edit_text("⚡ **أرسل رقم الطلب (Order ID) للتسريع:**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء", callback_data="admin_panel")]]), parse_mode="Markdown")

    elif data == "admin_cancel_order" and is_admin:
        context.user_data["admin_action"] = "cancel_order_input"
        await query.message.edit_text("❌ **أرسل رقم الطلب (Order ID) للإلغاء:**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء", callback_data="admin_panel")]]), parse_mode="Markdown")

    elif data == "admin_deposits_menu" and is_admin:
        if not pending_deposits:
            await query.message.edit_text("✅ لا توجد إيصالات شحن معلقة.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة التحكم", callback_data="admin_panel")]]))
            return
        kb = []
        for dep_id, info in pending_deposits.items():
            kb.append([
                InlineKeyboardButton(f"🟢 قبول #{dep_id} ({info['net_amount']} {CURRENCY})", callback_data=f"approve_{dep_id}"),
                InlineKeyboardButton(f"🔴 رفض #{dep_id}", callback_data=f"reject_{dep_id}")
            ])
        kb.append([InlineKeyboardButton("🔙 لوحة التحكم", callback_data="admin_panel")])
        await query.message.edit_text("📥 **الإيصالات المعلقة:**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data.startswith("approve_") and is_admin:
        dep_id = int(data.split("_")[1])
        if dep_id in pending_deposits:
            info = pending_deposits.pop(dep_id)
            uid, net = info["user_id"], info["net_amount"]
            users_db.setdefault(uid, {"balance": 0.0, "username": "مستخدم", "discount": 0.0, "orders": [], "transactions": [], "banned": False})
            users_db[uid]["balance"] += net
            log_user_transaction(uid, net, f"شحن رصيد بواسطة إيصال Orange Money (رقم الإيصال #{dep_id})")
            save_users_to_file()
            await query.message.edit_text(f"✅ تمت الموافقة وإضافة `{net:.3f}` {CURRENCY} للمستخدم `{uid}`.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 للإيصالات", callback_data="admin_deposits_menu")]]), parse_mode="Markdown")
            try:
                await context.bot.send_message(chat_id=uid, text=f"🎉 **تمت إضافة الرصيد بنجاح!**\n💳 تمت الموافقة على الشحن وإضافة `{net:.3f}` **{CURRENCY}** لرصيدك.", parse_mode="Markdown")
            except Exception:
                pass

    elif data.startswith("reject_") and is_admin:
        dep_id = int(data.split("_")[1])
        if dep_id in pending_deposits:
            info = pending_deposits.pop(dep_id)
            uid = info["user_id"]
            await query.message.edit_text(f"❌ تم رفض إيصال المستخدم `{uid}`.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 للإيصالات", callback_data="admin_deposits_menu")]]))
            try:
                await context.bot.send_message(chat_id=uid, text="❌ نعتذر، تم رفض إيصال الشحن لعدم صحته.", parse_mode="Markdown")
            except Exception:
                pass
async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await anti_spam_middleware(update, context):
        return

    global maintenance_settings, ticket_counter
    if not update.message or not update.message.text:
        return
    user_id = update.effective_user.id
    text = update.message.text.strip()
    is_admin = (user_id == ADMIN_ID)

    if user_id in users_db and users_db[user_id].get("banned", False) and not is_admin:
        return
    if maintenance_settings.get("bot", False) and not is_admin:
        return

    if user_id not in users_db:
        users_db[user_id] = {"balance": 0.0, "username": update.effective_user.username, "discount": 0.0, "orders": [], "banned": False, "last_free_order": 0}
        save_users_to_file()

    if context.user_data.get("waiting_for_ticket_msg"):
        context.user_data["waiting_for_ticket_msg"] = False
        t_id = ticket_counter
        ticket_counter += 1
        user_str = str(user_id)
        if user_str not in support_tickets:
            support_tickets[user_str] = []
        support_tickets[user_str].append({"id": t_id, "msg": text, "status": "مفتوحة", "reply": "لا يوجد رد بعد"})
        save_json(TICKETS_FILE, support_tickets)
        await update.message.reply_text(f"✅ **تم إرسال تذكرتك بنجاح (#{t_id})!**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 تذاكري", callback_data="support_tickets_menu")]]), parse_mode="Markdown")
        return

    if context.user_data.get("waiting_for_search_query"):
        context.user_data["waiting_for_search_query"] = False
        found = []
        for c_key, c_data in SERVICES.items():
            for item in c_data["items"]:
                if text.lower() in item["title"].lower():
                    found.append((c_key, item))
        if not found:
            await update.message.reply_text("❌ لم يتم العثور على نتائج.")
        else:
            res = f"🔎 **نتائج البحث:**\n\n"
            kb = []
            for c_key, item in found[:10]:
                res += f"🔹 {item['title']} | `{item['price']}` {CURRENCY}\n"
                kb.append([InlineKeyboardButton(item['title'][:35], callback_data=f"srv_{c_key}_{item['id']}")])
            kb.append([InlineKeyboardButton("🔙 الرئيسية", callback_data="main_menu")])
            await update.message.reply_text(res, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return

    if context.user_data.get("waiting_for_status_id"):
        context.user_data["waiting_for_status_id"] = False
        try:
            o_id = int(text)
            r = check_order_status_api(o_id)
            if "error" in r:
                await update.message.reply_text(f"❌ خطأ من المزود: `{r['error']}`", parse_mode="Markdown")
            else:
                await update.message.reply_text(
                    f"🔍 **حالة الطلب #{o_id} (من السيرفر مباشرة):**\n\n"
                    f"📌 **الحالة:** `{r.get('status')}`\n"
                    f"📈 **العدد الابتدائي:** `{r.get('start_count')}`\n"
                    f"⏳ **المتبقي:** `{r.get('remains')}`\n"
                    f"💵 **التكلفة:** `{r.get('charge')}`",
                    parse_mode="Markdown"
                )
        except ValueError:
            await update.message.reply_text("❌ أرقام صحيحة فقط مطلوبة.")
        return

    if context.user_data.get("waiting_for_promo_code"):
        context.user_data["waiting_for_promo_code"] = False
        if text in promo_codes:
            bonus = promo_codes.pop(text)
            users_db[user_id]["balance"] += bonus
            save_users_to_file()
            save_json(PROMO_FILE, promo_codes)
            await update.message.reply_text(f"🎉 تم تفعيل الكود وإضافة `{bonus}` **{CURRENCY}** لرصيدك!", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ الكود غير صالح أو تم استخدامه مسبقاً.")
        return

    if is_admin:
        action = context.user_data.get("admin_action")
        if action == "toggle_service_maint_id":
            context.user_data["admin_action"] = None
            try:
                s_id = str(int(text))
                cur = maintenance_settings.setdefault("services", {}).get(s_id, False)
                maintenance_settings["services"][s_id] = not cur
                save_json(MAINTENANCE_FILE, maintenance_settings)
                st = "مفعلة 🟢" if cur else "في الصيانة 🛠️"
                await update.message.reply_text(f"✅ تم تغيير صيانة الخدمة `{s_id}` لتصبح: {st}")
            except ValueError:
                await update.message.reply_text("❌ أيدي خدمة غير صحيح.")
            return

        elif action == "send_custom_notification_id":
            try:
                target_uid = int(text)
                context.user_data["notify_target_uid"] = target_uid
                context.user_data["admin_action"] = "send_custom_notification_msg"
                await update.message.reply_text(f"✅ تم تحديد المستخدم (`{target_uid}`).\n\n💬 **الآن أرسل نص الإشعار المراد إرساله له:**", parse_mode="Markdown")
            except ValueError:
                await update.message.reply_text("❌ أيدي صحيح مطلوب.")
            return

        elif action == "send_custom_notification_msg":
            context.user_data["admin_action"] = None
            target_uid = context.user_data.get("notify_target_uid")
            try:
                await context.bot.send_message(chat_id=target_uid, text=f"📩 **إشعار هام من الإدارة:**\n\n{text}", parse_mode="Markdown")
                await update.message.reply_text(f"✅ تم إرسال الإشعار للمستخدم `{target_uid}` بنجاح!")
            except Exception as e:
                await update.message.reply_text(f"❌ فشل الإرسال:\n`{e}`", parse_mode="Markdown")
            return

        elif action == "add_promo_code":
            try:
                parts = text.split()
                c_name, c_val = parts[0], float(parts[1])
                promo_codes[c_name] = c_val
                save_json(PROMO_FILE, promo_codes)
                context.user_data["admin_action"] = None
                await update.message.reply_text(f"✅ تم إضافة الكود `{c_name}` بقيمة `{c_val}` {CURRENCY}", parse_mode="Markdown")
            except Exception:
                await update.message.reply_text("❌ صيغة خاطئة. أرسل هكذا: `MATRIX 1.0`", parse_mode="Markdown")
            return

        elif action == "add_balance_step1":
            try:
                context.user_data["target_user_id"] = int(text)
                context.user_data["admin_action"] = "add_balance_step2"
                await update.message.reply_text("💬 **أرسل المبلغ المراد إضافته:**", parse_mode="Markdown")
            except ValueError:
                await update.message.reply_text("❌ أيدي خاطئ.")
            return

        elif action == "add_balance_step2":
            try:
                amt = float(text)
                tid = context.user_data.get("target_user_id")
                users_db.setdefault(tid, {"balance": 0.0, "username": "مستخدم", "discount": 0.0, "orders": [], "transactions": [], "banned": False})
                users_db[tid]["balance"] += amt
                save_users_to_file()
                context.user_data["admin_action"] = None
                await update.message.reply_text(f"✅ تمت إضافة `{amt}` {CURRENCY} للمستخدم `{tid}` بنجاح.", parse_mode="Markdown")
            except ValueError:
                await update.message.reply_text("❌ أرسل رقماً صحيحاً.")
            return

        elif action == "sub_balance_step1":
            try:
                context.user_data["target_user_id"] = int(text)
                context.user_data["admin_action"] = "sub_balance_step2"
                await update.message.reply_text("💬 **أرسل المبلغ المراد خصمه:**", parse_mode="Markdown")
            except ValueError:
                await update.message.reply_text("❌ أيدي خاطئ.")
            return

        elif action == "sub_balance_step2":
            try:
                amt = float(text)
                tid = context.user_data.get("target_user_id")
                users_db.setdefault(tid, {"balance": 0.0, "username": "مستخدم", "discount": 0.0, "orders": [], "transactions": [], "banned": False})
                users_db[tid]["balance"] = max(0.0, users_db[tid]["balance"] - amt)
                save_users_to_file()
                context.user_data["admin_action"] = None
                await update.message.reply_text(f"✅ تم خصم `{amt}` {CURRENCY} من المستخدم `{tid}`.", parse_mode="Markdown")
            except ValueError:
                await update.message.reply_text("❌ أرسل رقماً صحيحاً.")
            return

        elif action == "speed_order_input":
            try:
                o_id = int(text)
                res = manage_provider_order("refill", o_id)
                context.user_data["admin_action"] = None
                await update.message.reply_text(f"⚡ نتيجة التسريع:\n`{res}`", parse_mode="Markdown")
            except ValueError:
                await update.message.reply_text("❌ أرقام فقط.")
            return

        elif action == "cancel_order_input":
            try:
                o_id = int(text)
                res = manage_provider_order("cancel", o_id)
                context.user_data["admin_action"] = None
                await update.message.reply_text(f"❌ نتيجة الإلغاء:\n`{res}`", parse_mode="Markdown")
            except ValueError:
                await update.message.reply_text("❌ أرقام فقط.")
            return

    if context.user_data.get("waiting_for_deposit_amount"):
        try:
            amt = float(text)
            if amt <= 0:
                raise ValueError
        except ValueError:
            await update.message.reply_text("❌ أرسل مبلغاً صحيحاً بالأرقام.")
            return
        context.user_data["waiting_for_deposit_amount"] = False
        context.user_data["deposit_entered_amount"] = amt
        context.user_data["waiting_for_deposit_proof"] = True
        await update.message.reply_text("📸 **الآن أرسل صورة إيصال التحويل:**", parse_mode="Markdown")
        return

    if context.user_data.get("waiting_for_calc_quantity"):
        context.user_data["waiting_for_calc_quantity"] = False
        try:
            qty = int(text)
        except ValueError:
            await update.message.reply_text("❌ أرسل أرقاماً صحيحة للكمية:")
            context.user_data["waiting_for_calc_quantity"] = True
            return

        min_val = context.user_data.get("active_service_min", 10)
        if qty < min_val:
            await update.message.reply_text(f"❌ الحد الأدنى هو `{min_val}`. أعد إرسال الكمية:", parse_mode="Markdown")
            context.user_data["waiting_for_calc_quantity"] = True
            return

        price = context.user_data.get("active_service_price", 0.5)
        base = (qty / 1000) * price
        disc = users_db.get(user_id, {}).get("discount", 0.0)
        total = base * (1 - (disc / 100.0))

        context.user_data["order_quantity"] = qty
        context.user_data["order_total_cost"] = total
        context.user_data["waiting_for_service_link"] = True

        await update.message.reply_text(f"🧮 التكلفة الإجمالية: `{total:.3f}` **{CURRENCY}**\n\n🔗 **أرسل الآن الرابط المستهدف:**", parse_mode="Markdown")
        return

    if context.user_data.get("waiting_for_service_link"):
        if not text.startswith("http://") and not text.startswith("https://"):
            await update.message.reply_text("❌ **رابط غير صالح!** يجب أن يبدأ بـ http أو https:")
            return

        context.user_data["waiting_for_service_link"] = False
        context.user_data["order_link"] = text
        qty = context.user_data.get("order_quantity")
        total = context.user_data.get("order_total_cost")
        s_title = context.user_data.get("active_service_title", "خدمة")

        bal = users_db.get(user_id, {}).get("balance", 0.0)
        if bal < total:
            await update.message.reply_text(f"❌ رصيدك غير كافٍ!\nالمطلوب: `{total:.3f}` | رصيدك: `{bal:.3f}` **{CURRENCY}**", parse_mode="Markdown")
            return

        confirm_msg = f"📋 **تأكيد الطلب:**\n\n🔹 الخدمة: {s_title}\n🔗 الرابط: {text}\n📊 الكمية: `{qty}`\n💸 التكلفة: `{total:.3f}` **{CURRENCY}**"
        kb = [[InlineKeyboardButton("✅ تأكيد", callback_data="confirm_order")], [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_order")]]
        await update.message.reply_text(confirm_msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return

async def handle_photo_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await anti_spam_middleware(update, context):
        return
    if not update.message or not update.message.photo:
        return
    user_id = update.effective_user.id
    if context.user_data.get("waiting_for_deposit_proof"):
        context.user_data["waiting_for_deposit_proof"] = False
        photo = update.message.photo[-1]
        entered = context.user_data.get("deposit_entered_amount", 1.0)
        net = entered - (entered * 0.10)

        global deposit_counter
        d_id = deposit_counter
        deposit_counter += 1

        pending_deposits[d_id] = {"user_id": user_id, "amount": entered, "net_amount": net, "proof": photo.file_id}
        await update.message.reply_text("⏳ **تم إرسال الإيصال للإدارة للمراجعة.**", parse_mode="Markdown")

        try:
            uname = update.effective_user.username or update.effective_user.first_name
            await context.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=photo.file_id,
                caption=f"🔔 **إيصال شحن جديد معلق (#{d_id})!**\n\n👤 المستخدم: @{uname} (`{user_id}`)\n💳 المبلغ: `{entered}` **{CURRENCY}**\n💵 الصافي بعد العمولة: `{net:.3f}` **{CURRENCY}**",
                parse_mode="Markdown"
            )
        except Exception:
            pass

def main():
    try:
        app = ApplicationBuilder().token(BOT_TOKEN).build()

        async def post_init(application):
            await application.bot.set_my_commands([BotCommand("start", "تشغيل البوت والقائمة الرئيسية")])

        app.post_init = post_init

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CallbackQueryHandler(button_handler))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
        app.add_handler(MessageHandler(filters.PHOTO, handle_photo_messages))

        print("🤖 البوت يعمل بكفاءة تامة ومع المفتاح الجديد...")
        app.run_polling()
    except Exception as e:
        logger.error(f"Critical Bot Error: {e}")

if __name__ == "__main__":
    main()
