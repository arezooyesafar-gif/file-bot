from pyrogram import Client, filters, idle, errors
from pyrogram.types import *
from pyrogram.raw import functions, base, types
from colorama import Fore
import requests
import pymysql
import json
import sys
import os
import re
import math
from datetime import datetime, timedelta
import asyncio
#================= Config =================#
owner = 8335031839 # ایدی عددی مالک سلف ساز
api_id =  # ایپی ایدی مالک سلف ساز 
api_hash = "" # ایپی هش مالک سلف ساز
bot_token = "" # توکن ربات هلپر 
DBName = "selfsazv_panel" # نام دیتابیس هلپر 
DBUser = "selfsazv_panel" # یوزر دیتابیس هلپر 
DBPass = "selfsazv_panel" # پسورد دیتابیس هلپر 

# دیتابیس اصلی برای گرفتن الماس کاربران
MAIN_DBName = "selfsazv_self" # نام دیتابیس اصلی از سورس اصلی
MAIN_DBUser = "selfsazv_self" # یوزر دیتابیس اصلی
MAIN_DBPass = "selfsazv_self" # پسورد دیتابیس اصلی
#==========================================#

def get_data(query, params=None):
    try:
        connection = pymysql.connect(
            host="localhost",
            database=DBName,
            user=DBUser,
            password=DBPass,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
            connect_timeout=5,
            read_timeout=10,
            write_timeout=10,
        )
        db = connection.cursor()
        if params is None:
            m = re.match(r"^\s*SELECT\s+\*\s+FROM\s+(\w+)\s+WHERE\s+id\s*=\s*'?([0-9]+)'?\s*(LIMIT\s+1)?\s*$", query, re.IGNORECASE)
            if m:
                table, _id, _ = m.groups()
                query = f"SELECT * FROM {table} WHERE id = %s LIMIT 1"
                params = (_id,)
        db.execute(query, params or ())
        return db.fetchone()
    except Exception as e:
        print(f"[DB][get_data] Error: {type(e).__name__}: {e}")
        return None
    finally:
        try:
            connection.close()
        except Exception:
            pass


def get_datas(query):
     with pymysql.connect(host="localhost", database=DBName, user=DBUser, password=DBPass) as connect:
          db = connect.cursor()
          db.execute(query)
          result = db.fetchall()
          return result

def update_data(query):
     with pymysql.connect(host="localhost", database=DBName, user=DBUser, password=DBPass) as connect:
          db = connect.cursor()
          db.execute(query)
          connect.commit()

# تابع برای گرفتن الماس از دیتابیس اصلی
def get_main_data(query, params=None):
    try:
        connection = pymysql.connect(
            host="localhost",
            database=MAIN_DBName,
            user=MAIN_DBUser,
            password=MAIN_DBPass,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
            connect_timeout=5,
            read_timeout=10,
            write_timeout=10,
        )
        db = connection.cursor()
        db.execute(query, params or ())
        return db.fetchone()
    except Exception as e:
        print(f"[MAIN_DB][get_main_data] Error: {type(e).__name__}: {e}")
        return None
    finally:
        try:
            connection.close()
        except Exception:
            pass

# تابع برای گرفتن اطلاعات کاربر از دیتابیس اصلی
def get_user_diamonds(user_id):
    """گرفتن الماس کاربر از دیتابیس اصلی"""
    try:
        user_data = get_main_data(f"SELECT amount FROM user WHERE id = '{user_id}' LIMIT 1")
        if user_data:
            return user_data.get('amount', 0)
        return 0
    except Exception as e:
        print(f"[get_user_diamonds] Error: {e}")
        return 0

# تابع محاسبه زمان باقیمانده بر اساس الماس (هر ساعت 2 الماس)
def calculate_expire_time(diamonds):
    """محاسبه زمان باقیمانده بر اساس تعداد الماس (هر ساعت 2 الماس)"""
    if diamonds <= 0:
        return 0, 0, 0, "0 ساعت (0 روز)"
    
    # هر ساعت 2 الماس
    hours = diamonds // 2
    days = hours // 24
    remaining_hours = hours % 24
    
    # محاسبه دقیق زمان با روز و ساعت
    if days > 0:
        time_text = f"{days} روز و {remaining_hours} ساعت"
    else:
        time_text = f"{hours} ساعت"
    
    return hours, days, remaining_hours, time_text

update_data("""
CREATE TABLE IF NOT EXISTS user(
id bigint PRIMARY KEY,
step varchar(150) DEFAULT 'none'
) default charset=utf8mb4;
""")
update_data("""
CREATE TABLE IF NOT EXISTS ownerlist(
id bigint PRIMARY KEY
) default charset=utf8mb4;
""")
update_data("""
CREATE TABLE IF NOT EXISTS adminlist(
id bigint PRIMARY KEY
) default charset=utf8mb4;
""")

OwnerUser = get_data(f"SELECT * FROM ownerlist WHERE id = '{owner}' LIMIT 1")
if OwnerUser is None:
     update_data(f"INSERT INTO ownerlist(id) VALUES({owner})")

AdminUser = get_data(f"SELECT * FROM adminlist WHERE id = '{owner}' LIMIT 1")
if AdminUser is None:
     update_data(f"INSERT INTO adminlist(id) VALUES({owner})")

app = Client("Helper", api_id, api_hash, bot_token=bot_token)

@app.on_message(filters.private, group=-1)
async def update(c, m):
     OwnerUser = get_data(f"SELECT * FROM ownerlist WHERE id = '{m.chat.id}' LIMIT 1")
     AdminUser = get_data(f"SELECT * FROM adminlist WHERE id = '{m.chat.id}' LIMIT 1")
     if OwnerUser is not None or AdminUser is not None:
          user = get_data(f"SELECT * FROM user WHERE id = '{m.chat.id}' LIMIT 1")
          if user is None:
               update_data(f"INSERT INTO user(id) VALUES({m.chat.id})")
  
# ==================== متن‌های راهنما ==================== #
help_info_user = """
<blockquote>🆔 اطلاعات کاربر

با این دستور اطلاعات کامل کاربر رو پیدا کن.

↲ دستور:
`ایدی` + ریپلای
`ایدی` @یوزرنیم</blockquote>
"""

help_antilogin = """
<blockquote>🔐 ضد لاگین

از ورود غیرمجاز به اکانتت جلوگیری کن!

↲ دستور:
`ضد لاگین روشن`  
`ضد لاگین خاموش`</blockquote>
"""

help_online = """
<blockquote>🟢 انلاینی

با این بخش میتونید همیشه اکانتونو آنلاین نگه دارید

↲ دستور:
`انلاینی روشن`
`انلاینی خاموش`</blockquote>
"""

help_clone = """
<blockquote>🧬 کلون

با این دستور میتونید پروفایل هر شخصی رو کپی کنید!

↲ دستور:
`کلون` + ریپلای</blockquote>
"""

help_delete = """
<blockquote>🗑 حذف پیام انبوه

چندتا پیام آخر چت رو سریع پاک کن!

↲ دستور:
`حذف` [تعداد]  
`حذف` + ریپلای</blockquote>
"""

help_animation = """
<blockquote>🎮 سرگرمی

دستورهای فان و باحال برای چت

↲ دستور:
`جق`</blockquote>
"""

help_riket = """
<blockquote>👍 ریکت خودکار

هر کی بهت پیام بده یا توی گروه چیزی بفرسته،  
خودکار ریکت دلخواهت رو براش بذار!

↲ دستور:
`ریکت روشن`  
`ریکت خاموش`  
`ریکت` [ایموجی] + ریپلای  
`حذف ریکت` + ریپلای  
`لیست ریکت`  
`پاکسازی لیست ریکت`</blockquote>
"""

help_spam = """
<blockquote>🚀 اسپم پیام

پیامتو انقدر تکرار کن که طرف دیوونه بشه

↲ دستور:
`اسپم` [تعداد] [متن]  
`اسپم سریع` [تعداد] [متن]</blockquote>
"""

help_download = """
<blockquote>📥 دانلودر و کپی پست

هر پستی که بخوای از هر کانال یا گروهی دانلود کن یا کپی کن توی سیو مسیجت

↲ دستور:
`دانلود` [لینک پست]</blockquote>
"""

help_logo = """
<blockquote>🎨 ساخت لوگو

با اسم انگلیسی و یه طرح خفن، تو چند ثانیه لوگو بساز!

↲ دستور:
`لوگو` [اسم انگلیسی] [عدد طرح]</blockquote>
"""

help_game = """
<blockquote>🎲 تقلب در بازی‌های تلگرام

هر چی دلت خواست تو تاس، دارت، بولینگ و ... برنده شو!

↲ دستور:
`تاس` [عدد ۱-۶]  
`دارت`  
`بولینگ`  
`بسکتبال`  
`فوتبال` [۱ یا ۴]  
`کازینو`</blockquote>
"""

help_convert = """
<blockquote>🔄 تبدیل های مدیا

استیکر، عکس، گیف رو به هم تبدیل کن!

↲ دستور:
`تبدیل استیکر به عکس` + ریپلای  
`تبدیل عکس به استیکر` + ریپلای  
`فیلم به گیف` + ریپلای</blockquote>
"""

help_management = """
<blockquote>🚫 مدیریت اکانت

کاربرای مزاحم رو کنترل کن!

↲ دستور:
`بلاک` + ریپلای  
`انبلاک` + ریپلای</blockquote>
"""

help_sakot = """
<blockquote>🔇 سکوت کردن کاربر

پیامای طرف رو خودکار حذف کن!

↲ دستور:
`سکوت` + ریپلای  
`حذف سکوت` + ریپلای  
`لیست سکوت`  
`پاکسازی لیست سکوت`</blockquote>
"""

help_enemy_friend = """
<blockquote>😈 دشمن و دوست

دشمناتو اذیت کن، دوستاتو خوشحال!

**دشمن:**
`تنظیم دشمن` + ریپلای  
`حذف دشمن` + ریپلای  
`لیست دشمن`  
`پاکسازی لیست دشمن`

**دوست:**
`تنظیم دوست` + ریپلای  
`حذف دوست` + ریپلای  
`لیست دوست`  
`پاکسازی لیست دوست`</blockquote>
"""

help_pvlock = """
<blockquote>🔒 قفل‌ها

ارسال بعضی نوع پیام‌ها رو کامل ببند!

↲ دستور:
`قفل پیوی` روشن/خاموش
`قفل استیکر` روشن/خاموش
`قفل فوروارد` روشن/خاموش
`قفل گیف` روشن/خاموش
`قفل لینک` روشن/خاموش
`قفل عکس` روشن/خاموش
`قفل ویدیو` روشن/خاموش
`قفل ریپلای` روشن/خاموش</blockquote>
"""

help_secretary = """
<blockquote>👩‍💼 منشی پیشرفته

هر کی بهت پیام داد، خودکار جواب بده!

↲ دستور:
`منشی` روشن/خاموش
`متن منشی` [متن]</blockquote>
"""

help_filter = """
<blockquote>🚫 فیلترکلمات

کلمات ممنوعه رو حذف کن!

↲ دستور:
`فیلتر کلمات` روشن/خاموش
`فیلتر کلمه` [کلمه]  
`حذف فیلتر` [کلمه]  
`لیست فیلتر`  
`پاکسازی کلمات فیلتر`</blockquote>
"""

help_timesave = """
<blockquote>📸 ذخیره تایمی

عکس و ویدیوهای تایم‌دار رو خودکار سیو کن!

↲ دستور:
`ذخیره تایمی` روشن/خاموش</blockquote>
"""

help_texteffect = """
<blockquote>✨ حالت‌متن

پیامات رو با افکت‌های خفن بفرست!

↲ دستور:
`افکت متن` روشن/خاموش
`نوع افکت` [بولد، ایتالیک، زیرخط، اسپویلر، تدریجی، تایپ]</blockquote>
"""

help_autoseen = """
<blockquote>👁️ سین خودکار

هر پیامی که بیاد، خودکار سین بشه!

↲ دستور:
`سین خودکار` روشن/خاموش</blockquote>
"""

help_action = """
<blockquote>🎭 اکشن چت

وقتی تایپ می‌کنی، اکشن خفن نشون بده!

↲ دستور:
`اکشن` روشن/خاموش
`حالت اکشن`
[تایپ، ویس، ویدیو، عکس، سند، استیکر، بازی]</blockquote>
"""

help_tabchi = """
<blockquote>📢 تبچی پیشرفته

بنر هاتو راحت و بدون دردسر تبلغ کن با این قابلیت !

↲ دستور:
`تبچی` روشن/خاموش
`بنر` [ثانیه] [فور|کپی] + ریپلای  
`لیست بنر`  
`پاک کردن بنر` [کد]  
`پاکسازی کل تبچی`</blockquote>
"""

help_tools = """
<blockquote>🛠 ابزارهای جانبی

ابزارهای کاربردی و باحال سلف

↲ دستور:
`پینگ`  
`ایدی` + ریپلای  
`بیو`  
`تگ ادمین`  
`تگ اعضا`
`سیستم` - اطلاعات سیستم
`ماشین حساب` یا `e` [عبارت]</blockquote>
"""

help_info = """
<blockquote>👤 اطلاعات کاربر

این دستور فقط برای ادمین و مالک است

↲ دستور:
`تگ ادمین`  
`تگ اعضا`</blockquote>
"""

help_autoreply = """
<blockquote>🤖 پاسخ خودکار

هر کی بهت پیام بده، خودکار جواب بده!

↲ دستور:
`پاسخ خودکار` روشن/خاموش
`افزودن پاسخ` [سوال]:[پاسخ]  
`لیست پاسخ`  
`پاکسازی پاسخ`</blockquote>
"""

help_profile = """
<blockquote>👤 تنظیمات پروفایل

تغییر نام، بیو و عکس پروفایل اکانتت!

↲ دستور:
`تنظیم نام` [متن]  
`تنظیم نام خانوادگی` [متن]  
`تنظیم بیو` [متن]  
`تنظیم پروفایل` + ریپلای  
`حذف پروفایل`</blockquote>
"""

help_firstcomment = """
<blockquote>💬 کامنت اول

وقتی یک کانال پست گزاشت، کامنت اولش باش!

↲ دستور:
`کامنت اول` روشن/خاموش
`متن کامنت` [ریپلای]</blockquote>
"""

help_welcome = """
<blockquote>👋 خوشامدگویی

وقتی کسی به گروه اضافه میشه، خودکار خوش‌آمد بگو!

↲ دستور:
`خوشامد` روشن/خاموش
`تنظیم خوشامد` [متن]</blockquote>
"""

help_screenshot = """
<blockquote>📸 اسکرین‌شات از متن

هرچیز دلخواهت رو به عکس تبدیل کن!

↲ دستور:
`اسکرین` + ریپلای</blockquote>
"""

help_voice = """
<blockquote>🎤 تبدیل متن به ویس

متن فارسی رو به ویس تبدیل کن!

↲ دستور:
`ملیکا` [متن]  
`فرید` [متن]</blockquote>
"""

help_saat = """
<blockquote>🕒 ساعت پروفایل

ساعت رو با فونت‌های خفن کنار اسمت یا توی بیو نشون بده

↲ دستور:
`ساعت` روشن/خاموش
`ساعت بیو` روشن/خاموش
`فونت ساعت` [عدد]  
`بال` [عدد]  
`بال خاموش`  
`ثبت بیو` [متن]</blockquote>
"""

help_balsaat = """
<blockquote>🪽 بال ساعت

بال‌های خفن و فانتزی رو دور ساعت اسمت بذار

↲ دستور:
`بال` [عدد]  
`بال خاموش`

📜 لیست بال‌ها (نمونه):

1: ❰ ⩇⩇:⩇⩇ ❱
2: ✧ ⩇⩇:⩇⩇ ✧
3: 𓆩 ⩇⩇:⩇⩇ 𓆪
4: ❦ ⩇⩇:⩇⩇ ❦
5: ᥫ᭡ ⩇⩇:⩇⩇ ᥫ᭡
6: ♛ ⩇⩇:⩇⩇ ♛
7: ༒︎ ⩇⩇:⩇⩇ ༒︎
8: ⨺⃝ ⩇⩇:⩇⩇ ⨺⃝
9: ۝ ⩇⩇:⩇⩇ ۝
10: ߷ ⩇⩇:⩇⩇ ߷
11: ཊ ⩇⩇:⩇⩇ ཏ
12: ࿘ ⩇⩇:⩇⩇ ࿘
13: ࿇ ⩇⩇:⩇⩇ ࿇
14: ࿈ ⩇⩇:⩇⩇ ࿈
15: ፠ ⩇⩇:⩇⩇ ፠
16: ☫ ⩇⩇:⩇⩇ ☫
17: ꙮ‌‌‌‌‌‌ ⩇⩇:⩇⩇ ꙮ‌‌‌‌‌‌
18: ▄︻デ ⩇⩇:⩇⩇ ══━一
19: ﷽ ⩇⩇:⩇⩇ ﷽
20: 🝪 ⩇⩇:⩇⩇ 🝪
21: 🜎 ⩇⩇:⩇⩇ 🜎
22: ቿ ⩇⩇:⩇⩇ ቿ
23: ᳇ ⩇⩇:⩇⩇ ᳇
24: ␥ ⩇⩇:⩇⩇
25: ⟬ ⩇⩇:⩇⩇ ⟭
26: ꧁ ⩇⩇:⩇⩇ ꧂
27: ༺ ⩇⩇:⩇⩇ ༻
28: 𓄂 ⩇⩇:⩇⩇ 𓆃
29: ۩ ⩇⩇:⩇⩇ ۩
30: ✞︎ ⩇⩇:⩇⩇ ✞︎
31: ⨭ ⩇⩇:⩇⩇ ⨮
32: 𓆰 ⩇⩇:⩇⩇ 𓆪
33: 𖤍 ⩇⩇:⩇⩇ 𖤍
34: ❖ ⩇⩇:⩇⩇ ❖
35: 『 ⩇⩇:⩇⩇ 』
36: ʚ ⩇⩇:⩇⩇ ɞ
37: ၄ ⩇⩇:⩇⩇ ၃
38: ⚚ ⩇⩇:⩇⩇ ⚚
39: 𝄃𝄂𝄂𝄃 ⩇⩇:⩇⩇ 𝄃𝄂𝄂??
40: ⁂ ⩇⩇:⩇⩇ ⁂
41: ⫷ ⩇⩇:⩇⩇ ⫸
42: ⦓ ⩇⩇:⩇⩇ ⦔
43: ✤ ⩇⩇:⩇⩇ ✤
44: 𒆜 ⩇⩇:⩇⩇ 𒆜
45: 𓂍 ⩇⩇:⩇⩇ 𓂍
46: ⁘ ⩇⩇:⩇⩇ ⁘
47: ⧰ ⩇⩇:⩇⩇ ⧱
48: ⧼ ⩇⩇:⩇⩇ ⧽
49: ⧪ ⩇⩇:⩇⩇ ⧪
50: ☬ ⩇⩇:⩇⩇ ☬
51: 𒉭 ⩇⩇:⩇⩇ 𒉭
52: ᯤ ⩇⩇:⩇⩇ ᯤ
53: 三 ⩇⩇:⩇⩇ 三
54: 🃜 ⩇⩇:⩇⩇ 🃜
55: 🃚 ⩇⩇:⩇⩇ 🃚
56: 🃖 ⩇⩇:⩇⩇ 🃖
57: 🃁 ⩇⩇:⩇⩇ 🃁
58: 🂭 ⩇⩇:⩇⩇ 🂭
59: 🂺 ⩇⩇:⩇⩇ 🂺
60: 𖤓 ⩇⩇:⩇⩇ 𖤓
61: ☾ ⩇⩇:⩇⩇ ☾
62: 𐀪 ⩇⩇:⩇⩇ 𐀪
63: ❅ ⩇⩇:⩇⩇ ❅
64: ♡ ⩇⩇:⩇⩇ ♡
65: (◣ ⩇⩇:⩇⩇ ◢)
66: ✯ ⩇⩇:⩇⩇ ✯
67: ❝ ⩇⩇:⩇⩇ ❞
68: ⊱⋆⊳ ⩇⩇:⩇⩇ ⊲⋆⊰
69: 「 ⩇⩇:⩇⩇ 」
70: 𓊈 ⩇⩇:⩇⩇ 𓊉
71: 𓉘 ⩇⩇:⩇⩇ 𓉝
72: 𓊆 ⩇⩇:⩇⩇ 𓊇
73: [ ⩇⩇:⩇⩇ ]
74: ╽ ⩇⩇:⩇⩇ ╿
75: ┞ ⩇⩇:⩇⩇ ┦
76: ┌ ⩇⩇:⩇⩇ ┐
77: ⌜ ⩇⩇:⩇⩇ ⌝
78: 【 ⩇⩇:⩇⩇ 】
79: 〖 ⩇⩇:⩇⩇ 〗
80: ⎰ ⩇⩇:⩇⩇ ⎱
81: ⚟ ⩇⩇:⩇⩇ ⚞
82: ⸦ ⩇⩇:⩇⩇ ⸧
83: ╰ ⩇⩇:⩇⩇ ╯
84: ⦑ ⩇⩇:⩇⩇ ⦒
85: ☾ ⩇⩇:⩇⩇ ☽
86: ⌠ ⩇⩇:⩇⩇ ⌡
87: ⧼ ⩇⩇:⩇⩇ ⧽
88: ⊰ ⩇⩇:⩇⩇ ⊱
89: ཋྀ ⩇⩇:⩇⩇ ཐི
90: ╬ ⩇⩇:⩇⩇ ╬
91: 《 ⩇⩇:⩇⩇ 》
92: ★ ⩇⩇:⩇⩇ ★
93: # ⩇⩇:⩇⩇ #
94: Д ⩇⩇:⩇⩇ Д
95: ⑅ ⩇⩇:⩇⩇ ⑅
96: ♪ ⩇⩇:⩇⩇ ♪
97: ♬ ⩇⩇:⩇⩇ ♬
98: ⚕ ⩇⩇:⩇⩇ ⚕
99: ♀ ⩇⩇:⩇⩇ ♀
100: ⋆ ⩇⩇:⩇⩇ ⋆
101: ₊ ⩇⩇:⩇⩇ ₊
102: ꙳ ⩇⩇:⩇⩇ ꙳
103: ࿔ ⩇⩇:⩇⩇ ࿔
104: ❆ ⩇⩇:⩇⩇ ❆
105: ꨄ ⩇⩇:⩇⩇ ꨄ
106: ✚ ⩇⩇:⩇⩇ ✚
107: ✖ ⩇⩇:⩇⩇ ✖
108: ᡣ𐭩 ⩇⩇:⩇⩇ ᡣ𐭩
109: ❰❰ ⩇⩇:⩇⩇ ❱❱
110: ❀ ⩇⩇:⩇⩇ ❀
111: ထ ⩇⩇:⩇⩇ ထ
112: ╭⊰ ⩇⩇:⩇⩇ ⊱╮
113: ࿐| ⩇⩇:⩇⩇ |࿐
114: 𓆩♡𓆪 ⩇⩇:⩇⩇ 𓆩♡𓆪
115: ✦◈ ⩇⩇:⩇⩇ ◈✦
116: ◉⦿◉ ⩇⩇:⩇⩇ ◉⦿◉
117: ✨✨ ⩇⩇:⩇⩇ ✨✨
118: ꧁♢✸ ⩇⩇:⩇⩇ ✸♢꧂
119: ⋆═✩═⋆ ⩇⩇:⩇⩇ ⋆═✩═⋆
120: 一═⌊✦⌋ ⩇⩇:⩇⩇ ⌊✦⌋═一
121: ⋆˚｡⋆୨✧୧˚ ⩇⩇:⩇⩇ ˚୨✧୧⋆｡˚⋆
122: ▂▃▅▇█▓▒ ⩇⩇:⩇⩇ ▒▓█▇▅▃▂
123: ▁ ▂ ▃ ▅ ▆ ▇ ▌ ⩇⩇:⩇⩇ ▐ ▇ ▆ ▅ ▃ ▂ ▁
124: ★.¸¸.•´¯•.¸¸.★ ⩇⩇:⩇⩇ ★.¸¸.•´¯•.¸¸.★
125: ┗━━━━━━⊱ ⩇⩇:⩇⩇ ⊰━━━━━━┛
126: ˜”°•.¸☆¸.•°”˜ ⩇⩇:⩇⩇ ˜”°•.¸☆¸.•°”˜
127: ✧˚·‌‌‌‌˚‌‌‌‌·‌‌‌‌✧·‌‌‌‌˚‌‌‌‌˚·‌‌‌‌✧ ⩇⩇:⩇⩇ ✧˚·‌‌‌‌˚‌‌‌‌‌‌
128: ˜”°•.¸✦¸.•°”˜ ⩇⩇:⩇⩇ ˜”°•.¸✦¸.•°”˜
129: ꧁✬◦°⋆⋆°◦. ⩇⩇:⩇⩇ ◦°⋆⋆°◦✬꧂
130: ✦▄✦▀✦▄ ⩇⩇:⩇⩇ ▄✦▀✦▄✦
131: ─═✩✧═─ ⩇⩇:⩇⩇ ─═✧✩═─
132: ˜”°•✿•°”˜ ⩇⩇:⩇⩇ ˜”°•✿•°”˜
133: ✦•·.·¯˚·.·• ⩇⩇:⩇⩇ •·.·˚¯·.·•✦
134: ✦⁺₊✩☽⋆ ⩇⩇:⩇⩇ ⋆☾✩⁺₊✦
135: ⌠═❖═⌡ ⩇⩇:⩇⩇ ⌠═❖═⌡
136: ▢▣▢▣ ⩇⩇:⩇⩇ ▣▢▣▢
137: ❚█══ ⩇⩇:⩇⩇ ══█❚
138: ⋆·˚˚°✦ ⩇⩇:⩇⩇ ✦°˚˚·⋆
139: ﮩ٨ـﮩﮩ٨ـ ⩇⩇:⩇⩇ ﮩ٨ـﮩﮩ٨ـ
140: ╭─❖ ⩇⩇:⩇⩇ ❖─╮
141: ╰┈☆ ⩇⩇:⩇⩇ ☆┈╯
142: ▞▞▞ ⩇⩇:⩇⩇ ▞▞▞
143: ⊱❀⊰ ⩇⩇:⩇⩇ ⊱❀⊰
144: -♡´- ⩇⩇:⩇⩇ -♡´-
145: ✧【 ⩇⩇:⩇⩇ 】✧
146: ⌜✺⌟ ⩇⩇:⩇⩇ ⌜✺⌟
147: 𓆏 ⩇⩇:⩇⩇ 𓆏
148: 𓆈 ⩇⩇:⩇⩇ 𓆈
149: 𓄘 ⩇⩇:⩇⩇ 𓄘
150: 𓄻 ⩇⩇:⩇⩇ 𓄻
151: 𓂀 ⩇⩇:⩇⩇ 𓂀
152: 𓀀 ⩇⩇:⩇⩇ 𓀀
153: 𓆉 ⩇⩇:⩇⩇ 𓆉
154: 𓅃 ⩇⩇:⩇⩇ 𓅃
155: 𓆠 ⩇⩇:⩇⩇ 𓆠
156: 𓅀 ⩇⩇:⩇⩇ 𓅀
157: 𓄎 ⩇⩇:⩇⩇ 𓄎
158: 𓄏 ⩇⩇:⩇⩇ 𓄏
159: 𓅨 ⩇⩇:⩇⩇ 𓅨
160: 𓅳 ⩇⩇:⩇⩇ 𓅳
161: 𓅰 ⩇⩇:⩇⩇ 𓅰
162: 𓆭 ⩇⩇:⩇⩇ 𓆭
163: 𓂧 ⩇⩇:⩇⩇ 𓂧
164: 𓃂 ⩇⩇:⩇⩇ 𓃂
165: 𓅋 ⩇⩇:⩇⩇ 𓅋
166: 𓅅 ⩇⩇:⩇⩇ 𓅅
167: 𓀂 ⩇⩇:⩇⩇ 𓀂
168: 𓀌 ⩇⩇:⩇⩇ 𓀌
169: 𓅀 ⩇⩇:⩇⩇ 𓅀
170: 𓃷 ⩇⩇:⩇⩇ 𓃷
171: 𓅂 ⩇⩇:⩇⩇ 𓅂
172: 𓂝 ⩇⩇:⩇⩇ 𓂝
173: 𓃀 ⩇⩇:⩇⩇ 𓃀
174: 𓆆 ⩇⩇:⩇⩇ 𓆆
175: 𓆁 ⩇⩇:⩇⩇ 𓆁
176: 𓃗 ⩇⩇:⩇⩇ 𓃗
177: 𓄅 ⩇⩇:⩇⩇ 𓄅
178: 𓆢 ⩇⩇:⩇⩇ 𓆢
179: 𓃀 ⩇⩇:⩇⩇ 𓃀
180: 𓃤 ⩇⩇:⩇⩇ 𓃤
181: 𓂘 ⩇⩇:⩇⩇ 𓂘
182: 𓅌 ⩇⩇:⩇⩇ 𓅌
183: 𓂪 ⩇⩇:⩇⩇ 𓂪
184: 𓃪 ⩇⩇:⩇⩇ 𓃪
185: 𓆀 ⩇⩇:⩇⩇ 𓆀
186: 𓈖 ⩇⩇:⩇⩇ 𓈖
187: 𓄸 ⩇⩇:⩇⩇ 𓄸
188: 𓇎 ⩇⩇:⩇⩇ 𓇎
189: 𓅭 ⩇⩇:⩇⩇ 𓅭
190: 𓆜 ⩇⩇:⩇⩇ 𓆜
191: 𓇰 ⩇⩇:⩇⩇ 𓇰
192: 𓈓 ⩇⩇:⩇⩇ 𓈓
193: 𓉀 ⩇⩇:⩇⩇ 𓉀
194: 𓇑 ⩇⩇:⩇⩇ 𓇑</blockquote>
"""

help_font_saat = """
<blockquote>😎 فونت ساعت

ساعتت رو با فونت خفن کن

↲ دستور:
`فونت ساعت` [عدد]

📜 لیست فونت‌ها (نمونه ۰۱:۲۳):

1: 𝟶𝟷:𝟸𝟹
2: ⓪①:②③
3: 𝟬𝟭:𝟮𝟯
4: ٠١:٢٣
5: ０１:２３
6: ₀₁:₂₃
7: ⁰¹:²³
8: 𝟎𝟏:𝟐𝟑
9: 𝟘𝟙:𝟚𝟛
10: ʘ❶:❷❸
11: θ˦:˧˨
12: ○⥑:⥒⥓
13: ᦲ᧒:᧓᧔
14: ⦅0⦆⦅1⦆:⦅2⦆⦅3⦆
15: 0‌1‌:2‌3‌
16: 『0』『1』:『2』『3』
17: 【0】【1】:【2】【3】
18: Ѳ❶:❷❸
19: 𝟶𝟷:𝟸𝟹
20: 01:23
21: 0⃠1⃠:2⃠3⃠
22: 0⇂:ᘔƐ
23: ⊰0⊱⊰1⊱:⊰2⊱⊰3⊱
24: ⧼0⧽⧼1⧽:⧼2⧽⧼3⧽
25: ⌠0⌡⌠1⌡:⌠2⌡⌠3⌡
26: ☾0☽☾1☽:☾2☽☾3☽
27: ⦑0⦒⦑1⦒:⦑2⦒⦑3⦒
28: ╰0╯╰1╯:╰2╯╰3╯
29: 0ｯ1ｯ:2ｯ3ｯ
30: ⧼0‌⧽⧼1‌⧽:⧼2‌⧽⦑3‌⦎
31: ⦏0‌⦎⦏1‌⦎:⦏2‌⦎⦏3‌⦎
32: ⸦0⸧⸦1⸧:⸦2⸧⸦3⸧
33: ⚞0⚟⚞1⚟:⚞2⚟⚞3⚟
34: ⫷0⫸⫷1⫸:⫷2⫸⫷3⫸
35: ⎰0⎱⎰1⎱:⎰2⎱⎰3⎱
36: ⦓0⦔⦓1⦔:⦓2⦔⦓3⦔
37: 〖0〗〖1〗:〖2〗〖3〗
38: ₀1:₂3
39: ┌0┐┌1┐:┌2┐┌3┐
40: ┞0┦┞1┦:┞2┦┞3┦
41: ╽0╿╽1╿:╽2╿╽3╿
42: ⌜0⌝⌜1⌝:⌜2⌝⌜3⌝
43: ❰0❱❰1❱:❰2❱❰3❱
44: ⓿❶:❷❸
45: ⊘𝟙:ϩӠ
46: 0‌‌‌‌‌1‌‌‌‌‌:2‌‌‌‌‌3‌‌‌‌‌
47: ⓪⓵:⓶⓷
48: ⓪⓵:⓶𝟥
49: 𝟢𝟣:𝟤𝟥</blockquote>
"""

help_expire = """
<blockquote>⏰ دستور انقضا

شما با استفاده از این دستور میتونی انقضای باقی مانده سلفتون رو مشاهده کنی.
زمان بر اساس الماس شما محاسبه میشود (هر ساعت 2 الماس).

↲ دستور:
`انقضا`</blockquote>
"""

help_self = """
<blockquote>📊 دستور سلف

با استفاده از این دستور میتونی پینگ سلفت رو بررسی کنی.

↲ دستور:
`پینگ`</blockquote>
"""

help_restart_self = """
<blockquote>🔄 دستور ریست سلف

شما با این دستور سلف خودتون رو یک دور ریست (خاموش و روشن) میکنید.

↲ دستور:
`ریست`</blockquote>
"""

help_card = """
<blockquote>💳 دستور تنظیم کارت

شما با استفاده از این دستور میتونی کارت بانکی خودت رو تنظیم کنی.

↲ دستور:
`کارت` [ریپلای]
`تنظیم کارت` [شماره 16 رقمی] [نام]</blockquote>
"""

help_tag = """
<blockquote>🏷️ دستور تگ

شما با استفاده از این دستور میتونی تمامی ممبر هارو با یه متن تگ بکنی.

↲ دستور:
`تگ اعضا` [ریپلای]
`تگ ادمین` [ریپلای]</blockquote>
"""

help_proxy = """
<blockquote>🔗 دستور پروکسی

شما با استفاده از این دستور میتونی پروکسی رایگان دریافت کنی.

↲ دستور:
`پروکسی`</blockquote>
"""

help_filter_words = """
<blockquote>🚫 دستور فیلتر کردن متن

با این دستور ها میتونید کلمه هارو برای پیویتون فیلتر کنید و در صورتی که ارسال بکنند حذف میکنه.

↲ دستور:
`فیلتر کلمه` [کلمه]
`حذف فیلتر` [کلمه]
`لیست فیلتر`
`پاکسازی کلمات فیلتر`</blockquote>
"""

help_auto_response = """
<blockquote>🤖 دستور کنترل پاسخ خودکار

در این دستور میتونید کلمه/جمله تنظیم کنید که اگر پیوی اون رو ارسال کنن پاسخ میده و برای گروه اگر روی شما ریپلای بزنن پاسخ میده.

↲ دستور:
`افزودن پاسخ` [کلمه]:[پاسخ]
`لیست پاسخ`
`پاکسازی پاسخ`</blockquote>
"""

help_name = """
<blockquote>📛 دستور تنظیم نام

شما با استفاده از این دستور میتونی نام اول اکانت تلگرامت رو تغییر بدی.

↲ دستور:
`تنظیم نام` [متن]</blockquote>
"""

help_lastname = """
<blockquote>👤 دستور تنظیم نام خانوادگی

شما با استفاده از این دستور میتونی نام خانوادگی اکانت تلگرامت رو تغییر بدی.

↲ دستور:
`تنظیم نام خانوادگی` [متن]</blockquote>
"""

help_bio = """
<blockquote>📝 دستور تنظیم بیو

شما با استفاده از این دستور میتونی بیوگرافی اکانت تلگرامت رو تغییر بدی.

↲ دستور:
`ثبت بیو` [متن]</blockquote>
"""

help_profile_pic = """
<blockquote>🖼️ دستور عکس پروفایل

شما با استفاده از این دستور میتونی عکس پروفایل اکانتت رو تنظیم کنی.

↲ دستور:
`تنظیم پروفایل` [ریپلای]</blockquote>
"""

help_delete_profile = """
<blockquote>🗑️ دستور حذف پروفایل

شما با استفاده از این دستور میتونی عکس پروفایل اکانتت رو حذف کنی.

↲ دستور:
`حذف پروفایل`</blockquote>
"""

help_time_bio = """
<blockquote>🕒 دستور تایم بیو

در دست آپدیت هستش.</blockquote>
"""

help_silence = """
<blockquote>🔇 دستور سکوت

شما با استفاده از این دستور میتونی کاربر رو در گروه سکوت کنی.

↲ دستور:
`سکوت` [ریپلای/یوزرنیم]</blockquote>
"""

help_unsilence = """
<blockquote>🔊 دستور حذف سکوت

شما با استفاده از این دستور میتونی سکوت کاربر رو در گروه حذف کنی.

↲ دستور:
`حذف سکوت` [ریپلای/یوزرنیم]</blockquote>
"""

help_clear_silence = """
<blockquote>🧹 دستور پاکسازی سکوت

شما با استفاده از این دستور میتونی لیست کاربران سکوت شده رو پاکسازی کنی و لیست سکوت رو ببینی.

↲ دستور:
`لیست سکوت`
`پاکسازی لیست سکوت`</blockquote>
"""

help_block = """
<blockquote>🚫 دستور بلاک

شما با استفاده از این دستور میتونی کاربر رو بلاک کنی.

↲ دستور:
`بلاک` [ریپلای/یوزرنیم]</blockquote>
"""

help_unblock = """
<blockquote>✅ دستور آنبلاک

شما با استفاده از این دستور میتونی کاربر رو آنبلاک کنی.

↲ دستور:
`انبلاک` [ریپلای/یوزرنیم]</blockquote>
"""

help_enemy = """
<blockquote>👿 دستور دشمن

شما با استفاده از این دستور میتونی کاربر رو به لیست دشمنان اضافه کنی.

↲ دستور:
`تنظیم دشمن` [ریپلای]
`حذف دشمن` [ریپلای]
`لیست دشمن`
`پاکسازی لیست دشمن`</blockquote>
"""

help_friend = """
<blockquote>💖 دستور دوست

شما با استفاده از این دستور میتونی کاربر رو به لیست دوستان اضافه کنی.

↲ دستور:
`تنظیم دوست` [ریپلای]
`حذف دوست` [ریپلای]
`لیست دوست`
`پاکسازی لیست دوست`</blockquote>
"""

help_secretary_main = """
<blockquote>👩‍💼 دستور منشی

شما با استفاده از این دستور میتونی منشی برای پاسخگویی خودکار تنظیم کنی.

↲ دستور:
`منشی` روشن/خاموش
`متن منشی` [متن]
`تایم منشی` [عدد]</blockquote>
"""

help_tag_alert = """
<blockquote>🔔 دستور هشدار تگ

شما با استفاده از این دستور میتونی هشدار تگ شدن رو فعال کنی.

↲ دستور:
`هشدار تگ` روشن/خاموش</blockquote>
"""

help_offline = """
<blockquote>⏸️ دستور آفلاین

شما با استفاده از این دستور میتونی سلفت رو در حالت آفلاین قرار بدی.

↲ دستور:
`آفلاین` روشن/خاموش</blockquote>
"""

help_create_channel = """
<blockquote>📢 دستور ساخت کانال

شما با استفاده از این دستور میتونی کانال جدید بسازی.

↲ دستور:
`ساخت کانال` [نام]</blockquote>
"""

help_create_group = """
<blockquote>👥 دستور ساخت گروه

شما با استفاده از این دستور میتونی گروه جدید بسازی.

↲ دستور:
`ساخت گروه` [نام]</blockquote>
"""

help_create_supergroup = """
<blockquote>🌟 دستور ساخت سوپرگروه

شما با استفاده از این دستور میتونی سوپرگروه جدید بسازی.

↲ دستور:
`ساخت سوپر گروه` [نام]</blockquote>
"""

help_spam_main = """
<blockquote>💥 دستور اسپم

شما با استفاده از این دستور میتونی پیام اسپم ارسال کنی.
مثال: `اسپم 2 سلام`

↲ دستور:
`اسپم` [تعداد] [متن]</blockquote>
"""

help_welcome_main = """
<blockquote>🎉 دستور خوش آمدگویی

شما با استفاده از این دستور میتونی پیام خوش آمدگویی تنظیم کنی.

↲ دستور:
`خوشامد` روشن/خاموش
`متن خوشامد` [متن][ریپلای]</blockquote>
"""

help_first_comment = """
<blockquote>💬 دستور کامنت اول

شما با استفاده از این دستور میتونی کامنت اول رو تنظیم کنی.

↲ دستور:
`کامنت اول` روشن/خاموش
`متن کامنت` [ریپلای]</blockquote>
"""

help_ban = """
<blockquote>🚷 دستور بن

شما با استفاده از این دستور میتونی کاربر رو بن کنی.

↲ دستور:
`بن` [ریپلای/یوزرنیم]</blockquote>
"""

help_unban = """
<blockquote>✅ دستور آنبن

شما با استفاده از این دستور میتونی کاربر رو آنبن کنی.

↲ دستور:
`انبن` [ریپلای/یوزرنیم]</blockquote>
"""

help_set_silence = """
<blockquote>🔇 دستور تنظیم سکوت

شما با استفاده از این دستور میتونی سکوت کاربر رو تنظیم کنی.

↲ دستور:
`سکوت` [ریپلای]
`حذف سکوت` [ریپلای]
`لیست سکوت`
`پاکسازی لیست سکوت`</blockquote>
"""

help_set_group_pic = """
<blockquote>🖼️ دستور تنظیم پروفایل گروه

شما با استفاده از این دستور میتونی پروفایل گروه رو تنظیم کنی.

↲ دستور:
`تنظیم عکس گروه` [ریپلای]</blockquote>
"""

help_set_group_name = """
<blockquote>📛 دستور تنظیم نام گروه

شما با استفاده از این دستور میتونی نام گروه رو تغییر بدی.

↲ دستور:
`تنظیم نام گروه` [متن]</blockquote>
"""

help_set_group_bio = """
<blockquote>📝 دستور تنظیم بیو گروه

شما با استفاده از این دستور میتونی بیو گروه رو تغییر بدی.

↲ دستور:
`تنظیم بیو گروه` [متن]</blockquote>
"""

help_set_group_username = """
<blockquote>🔗 دستور تنظیم یوزرنیم گروه

شما با استفاده از این دستور میتونی یوزرنیم گروه رو تنظیم کنی.

↲ دستور:
`تنظیم یوزرنیم گروه` [یوزرنیم]</blockquote>
"""

help_pin = """
<blockquote>📌 دستور پین

شما با استفاده از این دستور میتونی پیام رو پین کنی.

↲ دستور:
`پین` [ریپلای]</blockquote>
"""

help_unpin_all = """
<blockquote>🧹 دستور حذف همه پین

شما با استفاده از این دستور میتونی همه پیام های پین شده رو حذف کنی.

↲ دستور:
`حذف پین همه`</blockquote>
"""

help_unpin = """
<blockquote>❌ دستور حذف پین

شما با استفاده از این دستور میتونی پیام پین شده رو حذف کنی.

↲ دستور:
`حذف پین` [ریپلای]</blockquote>
"""

help_delete_main = """
<blockquote>🗑️ دستور حذف

شما با استفاده از این دستور میتونی پیام ها رو حذف کنی.

↲ دستور:
`حذف` [تعداد/ریپلای]</blockquote>
"""

help_tag_admin = """
<blockquote>👨‍💼 دستور تگ ادمین

شما با استفاده از این دستور میتونی ادمین ها رو تگ کنی.

↲ دستور:
`تگ ادمین` [ریپلای]</blockquote>
"""

help_tag_members = """
<blockquote>👤 دستور تگ اعضا

شما با استفاده از این دستور میتونی کاربر ها رو تگ کنی.

↲ دستور:
`تگ اعضا` [ریپلای]</blockquote>
"""

help_extract_file = """
<blockquote>📦 دستور استخراج فایل

شما با استفاده از این دستور میتونی فایل رو از حالت فشرده خارج کنی.

↲ دستور:
`استخراج فایل` [ریپلای]</blockquote>
"""

help_car_price = """
<blockquote>🚗 دستور قیمت ماشین

شما با استفاده از این دستور میتونی قیمت ماشین رو چک کنی.

↲ دستور:
`قیمت ماشین` [نام ماشین]</blockquote>
"""

help_rename_file = """
<blockquote>📝 دستور تغییر نام فایل

شما با استفاده از این دستور میتونی نام فایل رو تغییر بدی.

↲ دستور:
`تغییر نام فایل` [اسم جدید] [ریپلای]</blockquote>
"""

help_number_checker = """
<blockquote>📞 دستور چکر شماره

این بخش درحال آپدیت میباشد.</blockquote>
"""

help_text_screenshot = """
<blockquote>📸 دستور اسکرین شات متن

شما با استفاده از این دستور میتونی از متن اسکرین شات بگیری.

↲ دستور:
`.q` [ریپلای]</blockquote>
"""

help_custom_screenshot = """
<blockquote>🖼️ دستور اسکرین شات دلخواه

شما با استفاده از این دستور میتونی از متن دلخواه اسکرین شات بگیری.

↲ دستور:
`.qq` [متن]</blockquote>
"""

help_cricket = """
<blockquote>🏏 دستور نتایج کریکت

شما با استفاده از این دستور میتونی نتایج کریکت رو ببینی.

↲ دستور:
`کریکت`</blockquote>
"""

help_weather = """
<blockquote>🌤️ دستور وضعیت هوا

شما با استفاده از این دستور میتونی وضعیت هوا رو چک کنی.

↲ دستور:
`وضعیت هوا` [نام شهر]</blockquote>
"""

help_azan = """
<blockquote>🕌 دستور اذان

شما با استفاده از این دستور میتونی زمان اذان رو ببینی.

↲ دستور:
`اذان` [نام شهر]</blockquote>
"""

help_currency = """
<blockquote>💰 دستور قیمت ارز

شما با استفاده از این دستور میتونی قیمت ارز رو ببینی.

↲ دستور:
`نرخ ارز`</blockquote>
"""

help_calculator = """
<blockquote>🧮 دستور ماشین حساب

شما با استفاده از این دستور میتونی محاسبات ریاضی انجام بدی.

↲ دستور:
`e` [عبارت ریاضی]
`محاسبه` [عبارت ریاضی]</blockquote>
"""

help_get_ip = """
<blockquote>🌐 دستور دریافت آیپی

شما با استفاده از این دستور میتونی آیپی سایت رو دریافت کنی.

↲ دستور:
`آیپی` [دامنه]</blockquote>
"""

help_ip_info = """
<blockquote>🔍 دستور اطلاعات آیپی

شما با استفاده از این دستور میتونی اطلاعات آیپی رو ببینی.

↲ دستور:
`اطلاعات آیپی` [آی‌پی]</blockquote>
"""

help_site_ping = """
<blockquote>📡 دستور پینگ سایت

شما با استفاده از این دستور میتونی پینگ سایت رو چک کنی.

↲ دستور:
`پینگ` [دامنه]</blockquote>
"""

help_site_screenshot = """
<blockquote>🖥️ دستور اسکرین شات سایت

شما با استفاده از این دستور میتونی از سایت اسکرین شات بگیری.

↲ دستور:
`اسکرین شات سایت` [دامنه]</blockquote>
"""

help_account_date = """
<blockquote>📅 دستور تاریخ ساخت اکانت

شما با استفاده از این دستور میتونی تاریخ ساخت اکانت رو ببینی.

↲ دستور:
`تاریخ ساخت` [ریپلای]</blockquote>
"""

help_copy_profile = """
<blockquote>👤 دستور کپی پروفایل

شما با استفاده از این دستور میتونی پروفایل کاربر رو کپی کنی.

↲ دستور:
`کلون` [آی‌دی] [ریپلای]</blockquote>
"""

help_limit_status = """
<blockquote>🚫 دستور وضعیت محدودیت

شما با استفاده از این دستور میتونی وضعیت محدودیت اکانت رو ببینی.

↲ دستور:
`وضعیت محدودیت`</blockquote>
"""

help_country_info = """
<blockquote>🌍 دستور اطلاعات کشور

شما با استفاده از این دستور میتونی اطلاعات کشور رو ببینی.

↲ دستور:
`اطلاعات کشور` [نام]</blockquote>
"""

help_translate_fa = """
<blockquote>🇮🇷 دستور ترجمه به فارسی

شما با استفاده از این دستور میتونی متن رو به فارسی ترجمه کنی.

↲ دستور:
`ترجمه به فارسی` [متن]</blockquote>
"""

help_translate_en = """
<blockquote>🇺🇸 دستور ترجمه به انگلیسی

شما با استفاده از این دستور میتونی متن رو به انگلیسی ترجمه کنی.

↲ دستور:
`ترجمه انگلیسی` [متن]</blockquote>
"""

help_download_movie = """
<blockquote>🎬 دستور دانلود فیلم

شما با استفاده از این دستور میتونی فیلم دانلود کنی.

↲ دستور:
`دانلود فیلم` [متن]</blockquote>
"""

help_download_anime = """
<blockquote>🎌 دستور دانلود انیمه

شما با استفاده از این دستور میتونی انیمه دانلود کنی.

↲ دستور:
`دانلود انیمه` [متن]</blockquote>
"""

help_create_password = """
<blockquote>🔐 دستور ساخت پسورد

شما با استفاده از این دستور میتونی پسورد بسازی.

↲ دستور:
`ساخت پسورد` [تعداد]</blockquote>
"""

help_morse_to_text = """
<blockquote>🔤 دستور تبدیل مورس به متن

شما با استفاده از این دستور میتونی مورس رو به متن تبدیل کنی.

↲ دستور:
`مورس به متن` [کد]</blockquote>
"""

help_text_to_morse = """
<blockquote>🔡 دستور تبدیل متن به مورس

شما با استفاده از این دستور میتونی متن رو به مورس تبدیل کنی.

↲ دستور:
`متن به مورس` [متن]</blockquote>
"""

help_get_date = """
<blockquote>📅 دستور دریافت تاریخ

شما با استفاده از این دستور میتونی تاریخ رو ببینی.

↲ دستور:
`تاریخ`</blockquote>
"""

help_account_info = """
<blockquote>👤 دستور دریافت اطلاعات اکانت

شما با استفاده از این دستور میتونی اطلاعات اکانت رو ببینی.

↲ دستور:
`ایدی` [ریپلای]</blockquote>
"""

help_message_info = """
<blockquote>💬 دستور دریافت اطلاعات پیام

شما با استفاده از این دستور میتونی اطلاعات پیام رو ببینی.

↲ دستور:
`اطلاعات پیام` [ریپلای]</blockquote>
"""

help_mention_user = """
<blockquote>👥 دستور منشن کاربر

شما با استفاده از این دستور میتونی کاربر رو منشن کنی.

↲ دستور:
`منشن` [آی‌دی] [ریپلای]</blockquote>
"""

help_national_code = """
<blockquote>🆔 دستور بررسی کد ملی

شما با استفاده از این دستور میتونی کد ملی رو بررسی کنی.

↲ دستور:
`بررسی کد ملی` [شماره]</blockquote>
"""

help_card_inquiry = """
<blockquote>💳 دستور استعلام کارت بانکی

شما با استفاده از این دستور میتونی کارت بانکی رو استعلام کنی.

↲ دستور:
`استعلام کارت` [شماره]</blockquote>
"""

help_instagram_download = """
<blockquote>📸 دستور دانلود اینستا 

شما با استفاده از این دستور میتونی پست اینستاگرامی را دانلود کنی.

↲ دستور:
`دانلود اینستا` [لینک]</blockquote>
"""

help_extract_text = """
<blockquote>📖 دستور استخراج متن از عکس

شما با استفاده از این دستور میتونی متن رو از عکس استخراج کنی.

↲ دستور:
`استخراج متن` [ریپلای]</blockquote>
"""

help_dice = """
<blockquote>🎲 دستور تاس

شما با استفاده از این دستور میتونی تاس بازی کنی.

↲ دستور:
`تاس` [عدد]</blockquote>
"""

help_basketball = """
<blockquote>🏀 دستور بسکتبال

شما با استفاده از این دستور میتونی بسکتبال بازی کنی.

↲ دستور:
`بسکتبال`</blockquote>
"""

help_bowling = """
<blockquote>🎳 دستور بولینگ

شما با استفاده از این دستور میتونی بولینگ بازی کنی.

↲ دستور:
`بولینگ`</blockquote>
"""

help_dart = """
<blockquote>🎯 دستور دارت

شما با استفاده از این دستور میتونی دارت بازی کنی.

↲ دستور:
`دارت`</blockquote>
"""

help_football = """
<blockquote>⚽ دستور فوتبال

شما با استفاده از این دستور میتونی فوتبال بازی کنی.

↲ دستور:
`فوتبال 1`</blockquote>
"""

help_faal = """
<blockquote>📜 دستور فال حافظ

شما با استفاده از این دستور میتونی فال حافظ بگیری.

↲ دستور:
`فال`</blockquote>
"""

help_random_game1 = """
<blockquote>🎲 دستور بازی رندوم 1

شما با استفاده از این دستور میتونی بازی رندوم انجام بدی.

↲ دستور:
`بازی رندوم 1`</blockquote>
"""

help_random_game2 = """
<blockquote>🎲 دستور بازی رندوم 2

شما با استفاده از این دستور میتونی بازی رندوم انجام بدی.

↲ دستور:
`بازی رندوم 2`</blockquote>
"""

help_random_game3 = """
<blockquote>🎲 دستور بازی رندوم 3

شما با استفاده از این دستور میتونی بازی رندوم انجام بدی.

↲ دستور:
`بازی رندوم 3`</blockquote>
"""

help_other_fun = """
<blockquote>🎪 دستور سایر سرگرمی

شما با استفاده از این دستور میتونی از سرگرمی های مختلف استفاده کنی.

↲ دستور:
`جق`</blockquote>
"""

help_photo = """
<blockquote>🔄 دستور عکس

شما با استفاده از این دستور میتونی عکس رو به استیکر تبدیل کنی.

↲ دستور:
`تبدیل عکس به استیکر` [ریپلای روی عکس]</blockquote>
"""

help_sticker = """
<blockquote>🔄 دستور استیکر

شما با استفاده از این دستور میتونی استیکر رو به عکس تبدیل کنی.

↲ دستور:
`تبدیل استیکر به عکس` [ریپلای روی استیکر]</blockquote>
"""

help_gif = """
<blockquote>🎞️ دستور گیف

شما با استفاده از این دستور میتونی ویدئو رو به گیف تبدیل کنی.

↲ دستور:
`فیلم به گیف` [ریپلای روی ویدئو]</blockquote>
"""

help_create_gif = """
<blockquote>🎞️ دستور ساخت گیف

شما با استفاده از این دستور میتونی گیف بسازی.

↲ دستور:
`ساخت گیف` [متن]</blockquote>
"""

help_create_sticker = """
<blockquote>🎞️ دستور ساخت استیکر

شما با استفاده از این دستور میتونی استیکر بسازی.

↲ دستور:
`ساخت استیکر` [متن]</blockquote>
"""

help_tabchi_main = """
<blockquote>🖼️ دستور تنظیم بنر

شما با استفاده از این دستور میتونی تبچی روشن کنید و تبلیغات کنید.

↲ دستور:
`تبچی` روشن/خاموش
`بنر` [ثانیه] [فور | کپی] + ریپلای 
`لیست بنر`
`پاک کردن بنر`
`پاکسازی کل تبچی`</blockquote>
"""

help_ai = """
<blockquote>🧠 دستور هوش مصنوعی

شما با استفاده از این دستور میتونی با هوش مصنوعی چت کنی.

↲ دستور:
`هوش مصنوعی` [متن]</blockquote>
"""

help_private_download = """
<blockquote>🔗 دستور دانلود پرایوت 

شما با استفاده از این دستور میتونی پست هایی که غیرقابل کپی هستند را ذخیره کنی.

↲ دستور:
`دانلود` [لینک]</blockquote>
"""

help_instagram_dl = """
<blockquote>📸 دستور دانلود اینستا 

شما با استفاده از این دستور میتونی پست اینستاگرامی را دانلود کنی.

↲ دستور:
`دانلود اینستا` [لینک]</blockquote>
"""

help_secretary_text = """
<blockquote>📝 دستور متن منشی

با این دستور اون متنی که میخوای منشی هر ۴۵ ثانیه برای هر شخص بفرسته رو میتونی تنظیم بکنی.

↲ دستور:
`متن منشی`</blockquote>
"""

help_secretary_self = """
<blockquote>🤖 دستور فعالسازی منشی

با این دستور میتونی منشی رو روشن بکنی.

↲ دستور:
`منشی` روشن/خاموش</blockquote>
"""

help_secretary_time = """
<blockquote>⏱️ دستور تنظیم تایم منشی

با این دستور میتونی تایم منشی رو تنظیم بکنی.

↲ دستور:
`تایم منشی` (عدد به ثانیه)</blockquote>
"""

help_text_mode = """
<blockquote>📝 دستور حالت متن

شما با استفاده از این دستور میتونی حالت متن رو تنظیم کنی.

↲ دستور:
`افکت متن` روشن/خاموش
`نوع افکت` [نام حالت]
(بولد، ایتالیک، زیرخط، اسپویلر، تدریجی، تایپ)</blockquote>
"""

help_action_mode = """
<blockquote>🎭 دستور حالت اکشن

شما با استفاده از این دستور میتونی حالت اکشن رو تنظیم کنی.

↲ دستور:
`حالت اکشن` روشن/خاموش
`نوع اکشن` [نام حالت]
(تایپ، ویس، ویدیو، عکس، سند، استیکر، بازی)</blockquote>
"""

help_reaction = """
<blockquote>👍 دستور ری‌اکشن

شما با استفاده از این دستور میتونی ری‌اکشن تنظیم کنی.

↲ دستور:
`ریکت` روشن/خاموش
`ریکت` [ایموجی] + ریپلای
`حذف ریکت` [ریپلای]
`لیست ریکت`
`پاکسازی لیست ریکت`</blockquote>
"""

help_time_save = """
<blockquote>💾 دستور ذخیره مدیا تایمدار

شما با استفاده از این دستور میتونی ذخیره تایمدار رو فعال کنی.

↲ دستور:
`ذخیره تایمی` روشن/خاموش</blockquote>
"""

help_anti_login = """
<blockquote>🔐 دستور فعال‌سازی ضدلاگین

شما با استفاده از این دستور میتونی از ورودهای ناشناس جلوگیری کنی.

↲ دستور:
`ضد لاگین` روشن/خاموش</blockquote>
"""

help_auto_seen = """
<blockquote>👁️ دستور فعال‌سازی سین‌خودکار

شما با استفاده از این دستور میتونی هرکی پیام داد بهت سریع ربات سین بزنه.

↲ دستور:
`سین خودکار` روشن/خاموش</blockquote>
"""

help_clear_enemy = """
<blockquote>🗑️ دستور پاکسازی کل دشمن

با استفاده از این دستور شما میتونی کل دشمن های تنظیم شده رو پاکسازی کنی.

↲ دستور:
`پاکسازی لیست دشمن`</blockquote>
"""

help_list_enemy = """
<blockquote>📋 دستور لیست دشمن

با استفاده از این دستور شما میتونی لیست کل دشمن های تنظیم شده رو نگاه کنی.

↲ دستور:
`لیست دشمن`</blockquote>
"""

help_list_friend = """
<blockquote>📋 دستور لیست دوست

با استفاده از این دستور شما میتونی لیست کل دوست های تنظیم شده رو نگاه کنی.

↲ دستور:
`لیست دوست`</blockquote>
"""

help_add_friend = """
<blockquote>❤️ دستور دوست

شما با استفاده از این دستور میتونی کاربر رو به لیست دوستان اضافه کنی.

↲ دستور:
`تنظیم دوست` [ریپلای]
`حذف دوست` [ریپلای]</blockquote>
"""

help_clear_friend = """
<blockquote>🧹 دستور پاکسازی کل دوست

با استفاده از این دستور شما میتونی کل دوست های تنظیم شده رو پاکسازی کنی.

↲ دستور:
`پاکسازی لیست دوست`</blockquote>
"""

help_system = """
<blockquote>💻 اطلاعات سیستم

اطلاعات کامل سیستم و وضعیت سرور رو نمایش میده.

↲ دستور:
`سیستم`</blockquote>
"""

help_gold = """
<blockquote>🪙 قیمت طلا و سکه

قیمت لحظه‌ای طلا و سکه رو نمایش میده.

↲ دستور:
`قیمت طلا`</blockquote>
"""

# ==================== پنل‌های اصلی ==================== #

openpanelbot = InlineKeyboardMarkup(
     [
         [
             InlineKeyboardButton("پنل 📱", switch_inline_query_current_chat='panel', style="danger")
         ]
     ]
)

keyboard_idk = ReplyKeyboardMarkup(
     [
         [
             ("Add Admin"),
             ("Delete Admin"),
             ("Admin List")
         ],
         [
             ("Add Owner"),
             ("Delete Owner"),
             ("Owner List")
         ]
     ],
one_time_keyboard=True,resize_keyboard=True)

# ==================== دکمه‌های منوی 1 ==================== #
def get_menu1_buttons(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❲ مدیریت ❳", callback_data=f'modiriat-{user_id}', style="primary"),
         InlineKeyboardButton("❲ تنظیمات ❳", callback_data=f'tanzimat-{user_id}', style="danger")],
        [InlineKeyboardButton("❲ پروفایل ❳", callback_data=f'profile_main-{user_id}', style="primary")],
        [InlineKeyboardButton("❲ سراسری ❳", callback_data=f'sarasari-{user_id}', style="danger"),
         InlineKeyboardButton("❲ ابزار ❳", callback_data=f'tools_main-{user_id}', style="primary")],
        [InlineKeyboardButton("❲ سرگرمی ❳", callback_data=f'entertainment-{user_id}', style="primary")],
        [InlineKeyboardButton("❲ تغییر ❳", callback_data=f'taghvir-{user_id}', style="success"),
         InlineKeyboardButton("❲ تبچی ❳", callback_data=f'tabchi_main-{user_id}', style="primary")],
        [InlineKeyboardButton("→", callback_data=f'menu2-{user_id}', style="success"),
         InlineKeyboardButton("1/3", callback_data=f'pageinfo-{user_id}', style="primary"),
         InlineKeyboardButton("←", callback_data=f'menu3-{user_id}', style="danger")],
        [InlineKeyboardButton("✖️ بستن پنل", callback_data=f'closepanel-{user_id}', style="success")]
    ])

# ==================== دکمه‌های منوی 2 ==================== #
def get_menu2_buttons(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❲ دانلودر ❳", callback_data=f'downloader-{user_id}', style="success")],
        [InlineKeyboardButton("❲ ساعت پروفایل ❳", callback_data=f'saat-{user_id}', style="success")],
        [InlineKeyboardButton("❲ حالت متن ❳", callback_data=f'text_mode-{user_id}', style="success"),
         InlineKeyboardButton("❲ منشی ❳", callback_data=f'secretary_main-{user_id}', style="primary")],
        [InlineKeyboardButton("❲ اطلاعات ❳", callback_data=f'info_main-{user_id}', style="success")],
        [InlineKeyboardButton("❲ دشمن ❳", callback_data=f'enemy_main-{user_id}', style="danger"),
         InlineKeyboardButton("❲ دوست ❳", callback_data=f'friend_main-{user_id}', style="success")],
        [InlineKeyboardButton("❲ حالت اکشن ❳", callback_data=f'action_mode-{user_id}', style="success")],
        [InlineKeyboardButton("→", callback_data=f'menu3-{user_id}', style="success"),
         InlineKeyboardButton("2/3", callback_data=f'pageinfo-{user_id}', style="success"),
         InlineKeyboardButton("←", callback_data=f'menu1-{user_id}', style="primary")],
        [InlineKeyboardButton("✖️ بستن پنل", callback_data=f'closepanel-{user_id}', style="primary")]
    ])

# ==================== دکمه‌های منوی 3 ==================== #
def get_menu3_buttons(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❲ ذخیره تایمدار ❳", callback_data=f'time_save-{user_id}', style="success"),
         InlineKeyboardButton("❲ سین خودکار ❳", callback_data=f'auto_seen-{user_id}', style="danger")],
        [InlineKeyboardButton("❲ ضدلاگین ❳", callback_data=f'anti_login-{user_id}', style="primary")],
        [InlineKeyboardButton("❲ تقلب ❳", callback_data=f'game-{user_id}', style="success"),
         InlineKeyboardButton("❲ ذخیره تایمدار ❳", callback_data=f'time_save2-{user_id}', style="primary")],
        [InlineKeyboardButton("❲ ری‌اکشن ❳", callback_data=f'reaction-{user_id}', style="danger")],
        [InlineKeyboardButton("→", callback_data=f'menu1-{user_id}', style="success"),
         InlineKeyboardButton("3/3", callback_data=f'pageinfo-{user_id}', style="danger"),
         InlineKeyboardButton("←", callback_data=f'menu2-{user_id}', style="success")],
        [InlineKeyboardButton("✖️ بستن پنل", callback_data=f'closepanel-{user_id}', style="primary")]
    ])

# ==================== دکمه‌های زیرمنوها ==================== #

# دکمه‌های تنظیمات
def get_tanzimat_buttons(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("سلف", callback_data=f'self-{user_id}', style="success"),
         InlineKeyboardButton("تگ", callback_data=f'tag-{user_id}', style="primary")],
        [InlineKeyboardButton("فیلتر کلمات", callback_data=f'filter_words-{user_id}', style="danger"),
         InlineKeyboardButton("پاسخ خودکار", callback_data=f'auto_response-{user_id}', style="danger")],
        [InlineKeyboardButton("‹ برگشت ›", callback_data=f'menu1-{user_id}', style="danger")]
    ])

# دکمه‌های مدیریت
def get_modiriat_buttons(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("انقضا", callback_data=f'expire-{user_id}', style="danger"),
         InlineKeyboardButton("سلف", callback_data=f'self-{user_id}', style="primary")],
        [InlineKeyboardButton("ریست سلف", callback_data=f'restart_self-{user_id}', style="success")],
        [InlineKeyboardButton("تنظیم کارت", callback_data=f'card-{user_id}', style="danger"),
         InlineKeyboardButton("تگ", callback_data=f'tag-{user_id}', style="danger")],
        [InlineKeyboardButton("‹ برگشت ›", callback_data=f'menu1-{user_id}', style="success")]
    ])

# دکمه‌های پروفایل
def get_profile_buttons(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("تنظیم نام", callback_data=f'name-{user_id}', style="danger"),
         InlineKeyboardButton("تنظیم نام خانوادگی", callback_data=f'lastname-{user_id}', style="primary")],
        [InlineKeyboardButton("تنظیم بیو", callback_data=f'bios-{user_id}', style="primary")],
        [InlineKeyboardButton("تایم بیو", callback_data=f'time_bio-{user_id}', style="success"),
         InlineKeyboardButton("عکس پروفایل", callback_data=f'profile_pic-{user_id}', style="danger")],
        [InlineKeyboardButton("حذف پروفایل", callback_data=f'delete_profile-{user_id}', style="danger")],
        [InlineKeyboardButton("‹ برگشت ›", callback_data=f'menu1-{user_id}', style="danger")]
    ])

# دکمه‌های سراسری - صفحه 1
def get_sarasari_page1_buttons(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("سکوت", callback_data=f'silence-{user_id}', style="danger"),
         InlineKeyboardButton("حذف سکوت", callback_data=f'unsilence-{user_id}', style="danger")],
        [InlineKeyboardButton("پاکسازی سکوت", callback_data=f'clear_silence-{user_id}', style="primary")],
        [InlineKeyboardButton("بلاک", callback_data=f'block-{user_id}', style="danger"),
         InlineKeyboardButton("آنبلاک", callback_data=f'unblock-{user_id}', style="danger")],
        [InlineKeyboardButton("دشمن", callback_data=f'enemy-{user_id}', style="success")],
        [InlineKeyboardButton("→", callback_data=f'sarasari2-{user_id}', style="danger"),
         InlineKeyboardButton("1/6", callback_data=f'pageinfo-{user_id}', style="success"),
         InlineKeyboardButton("←", callback_data=f'sarasari6-{user_id}', style="success")],
        [InlineKeyboardButton("‹ برگشت ›", callback_data=f'menu1-{user_id}', style="danger")]
    ])

# دکمه‌های سراسری - صفحه 2
def get_sarasari_page2_buttons(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("آفلاین", callback_data=f'offline-{user_id}', style="danger"),
         InlineKeyboardButton("دوست", callback_data=f'friend-{user_id}', style="success")],
        [InlineKeyboardButton("منشی", callback_data=f'secretary-{user_id}', style="success")],
        [InlineKeyboardButton("اسپم", callback_data=f'spam_main-{user_id}', style="primary"),
         InlineKeyboardButton("هشدار تگ", callback_data=f'tag_alert-{user_id}', style="danger")],
        [InlineKeyboardButton("ساخت کانال", callback_data=f'create_channel-{user_id}', style="danger")],
        [InlineKeyboardButton("→", callback_data=f'sarasari3-{user_id}', style="primary"),
         InlineKeyboardButton("2/6", callback_data=f'pageinfo-{user_id}', style="success"),
         InlineKeyboardButton("←", callback_data=f'sarasari1-{user_id}', style="success")],
        [InlineKeyboardButton("‹ برگشت ›", callback_data=f'menu1-{user_id}', style="success")]
    ])

# دکمه‌های سراسری - صفحه 3
def get_sarasari_page3_buttons(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("ساخت گروه", callback_data=f'create_group-{user_id}', style="success"),
         InlineKeyboardButton("ساخت سوپر گروه", callback_data=f'create_supergroup-{user_id}', style="danger")],
        [InlineKeyboardButton("حذف", callback_data=f'delete_main-{user_id}', style="success")],
        [InlineKeyboardButton("خوش آمدگویی", callback_data=f'welcome_main-{user_id}', style="primary"),
         InlineKeyboardButton("پاسخ خودکار", callback_data=f'auto_response-{user_id}', style="success")],
        [InlineKeyboardButton("کامنت اول", callback_data=f'first_comment-{user_id}', style="primary")],
        [InlineKeyboardButton("→", callback_data=f'sarasari4-{user_id}', style="primary"),
         InlineKeyboardButton("3/6", callback_data=f'pageinfo-{user_id}', style="primary"),
         InlineKeyboardButton("←", callback_data=f'sarasari2-{user_id}', style="success")],
        [InlineKeyboardButton("‹ برگشت ›", callback_data=f'menu1-{user_id}', style="primary")]
    ])

# دکمه‌های سراسری - صفحه 4
def get_sarasari_page4_buttons(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("بن", callback_data=f'ban-{user_id}', style="primary"),
         InlineKeyboardButton("آنبن", callback_data=f'unban-{user_id}', style="danger")],
        [InlineKeyboardButton("تنظیم سکوت", callback_data=f'set_silence-{user_id}', style="danger")],
        [InlineKeyboardButton("حذف سکوت گروه", callback_data=f'unsilence-{user_id}', style="primary"),
         InlineKeyboardButton("تنظیم پروفایل گروه", callback_data=f'set_group_pic-{user_id}', style="success")],
        [InlineKeyboardButton("تنظیم نام گروه", callback_data=f'set_group_name-{user_id}', style="success")],
        [InlineKeyboardButton("→", callback_data=f'sarasari5-{user_id}', style="success"),
         InlineKeyboardButton("4/6", callback_data=f'pageinfo-{user_id}', style="danger"),
         InlineKeyboardButton("←", callback_data=f'sarasari3-{user_id}', style="success")],
        [InlineKeyboardButton("‹ برگشت ›", callback_data=f'menu1-{user_id}', style="danger")]
    ])

# دکمه‌های سراسری - صفحه 5
def get_sarasari_page5_buttons(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("تنظیم بیو گروه", callback_data=f'set_group_bio-{user_id}', style="primary"),
         InlineKeyboardButton("تنظیم یوزرنیم گروه", callback_data=f'set_group_username-{user_id}', style="success")],
        [InlineKeyboardButton("پین", callback_data=f'pin-{user_id}', style="primary")],
        [InlineKeyboardButton("حذف پین", callback_data=f'unpin-{user_id}', style="success"),
         InlineKeyboardButton("حذف همه پین", callback_data=f'unpin_all-{user_id}', style="primary")],
        [InlineKeyboardButton("→", callback_data=f'sarasari6-{user_id}', style="danger"),
         InlineKeyboardButton("5/6", callback_data=f'pageinfo-{user_id}', style="primary"),
         InlineKeyboardButton("←", callback_data=f'sarasari4-{user_id}', style="success")],
        [InlineKeyboardButton("‹ برگشت ›", callback_data=f'menu1-{user_id}', style="success")]
    ])

# دکمه‌های سراسری - صفحه 6
def get_sarasari_page6_buttons(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("حالت آرام", callback_data=f'silence-{user_id}', style="success"),
         InlineKeyboardButton("حذف", callback_data=f'delete_main-{user_id}', style="primary")],
        [InlineKeyboardButton("تگ ادمین", callback_data=f'tag_admin-{user_id}', style="success"),
         InlineKeyboardButton("تگ اعضا", callback_data=f'tag_members-{user_id}', style="success")],
        [InlineKeyboardButton("→", callback_data=f'sarasari1-{user_id}', style="primary"),
         InlineKeyboardButton("6/6", callback_data=f'pageinfo-{user_id}', style="primary"),
         InlineKeyboardButton("←", callback_data=f'sarasari5-{user_id}', style="success")],
        [InlineKeyboardButton("‹ برگشت ›", callback_data=f'menu1-{user_id}', style="primary")]
    ])

# دکمه‌های ابزار - صفحه 1
def get_tools_page1_buttons(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("استخراج فایل", callback_data=f'extract_file-{user_id}', style="success"),
         InlineKeyboardButton("قیمت ماشین", callback_data=f'car_price-{user_id}', style="primary")],
        [InlineKeyboardButton("تغییر نام فایل", callback_data=f'rename_file-{user_id}', style="success")],
        [InlineKeyboardButton("چکر شماره", callback_data=f'number_checker-{user_id}', style="primary"),
         InlineKeyboardButton("اسکرین شات متن", callback_data=f'text_screenshot-{user_id}', style="primary")],
        [InlineKeyboardButton("اسکرین شات دلخواه", callback_data=f'custom_screenshot-{user_id}', style="primary")],
        [InlineKeyboardButton("→", callback_data=f'tools2-{user_id}', style="success"),
         InlineKeyboardButton("1/6", callback_data=f'pageinfo-{user_id}', style="danger"),
         InlineKeyboardButton("←", callback_data=f'tools6-{user_id}', style="danger")],
        [InlineKeyboardButton("‹ برگشت ›", callback_data=f'menu1-{user_id}', style="success")]
    ])

# دکمه‌های ابزار - صفحه 2
def get_tools_page2_buttons(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("دریافت آیپی", callback_data=f'get_ip-{user_id}', style="danger"),
         InlineKeyboardButton("وضعیت هوا", callback_data=f'weather-{user_id}', style="primary")],
        [InlineKeyboardButton("اذان", callback_data=f'azan-{user_id}', style="primary")],
        [InlineKeyboardButton("اطلاعات آیپی", callback_data=f'ip_info-{user_id}', style="danger")],
        [InlineKeyboardButton("→", callback_data=f'tools3-{user_id}', style="danger"),
         InlineKeyboardButton("2/6", callback_data=f'pageinfo-{user_id}', style="danger"),
         InlineKeyboardButton("←", callback_data=f'tools1-{user_id}', style="success")],
        [InlineKeyboardButton("‹ برگشت ›", callback_data=f'menu1-{user_id}', style="primary")]
    ])

# دکمه‌های ابزار - صفحه 3
def get_tools_page3_buttons(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("نتایج کریکت", callback_data=f'cricket-{user_id}', style="success"),
         InlineKeyboardButton("پینگ سایت", callback_data=f'site_ping-{user_id}', style="danger")],
        [InlineKeyboardButton("اسکرین شات سایت", callback_data=f'site_screenshot-{user_id}', style="primary")],
        [InlineKeyboardButton("کپی پروفایل", callback_data=f'copy_profile-{user_id}', style="success"),
         InlineKeyboardButton("تاریخ ساخت اکانت", callback_data=f'account_date-{user_id}', style="primary")],
        [InlineKeyboardButton("وضعیت محدودیت", callback_data=f'limit_status-{user_id}', style="success")],
        [InlineKeyboardButton("سیستم", callback_data=f'system-{user_id}', style="danger")],
        [InlineKeyboardButton("→", callback_data=f'tools4-{user_id}', style="danger"),
         InlineKeyboardButton("3/6", callback_data=f'pageinfo-{user_id}', style="success"),
         InlineKeyboardButton("←", callback_data=f'tools2-{user_id}', style="danger")],
        [InlineKeyboardButton("‹ برگشت ›", callback_data=f'menu1-{user_id}', style="primary")]
    ])

# دکمه‌های ابزار - صفحه 4
def get_tools_page4_buttons(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("اطلاعات کشور", callback_data=f'country_info-{user_id}', style="danger"),
         InlineKeyboardButton("ترجمه به فارسی", callback_data=f'translate_fa-{user_id}', style="success")],
        [InlineKeyboardButton("ترجمه به انگلیسی", callback_data=f'translate_en-{user_id}', style="success")],
        [InlineKeyboardButton("دانلود فیلم", callback_data=f'download_movie-{user_id}', style="primary"),
         InlineKeyboardButton("دانلود انیمه", callback_data=f'download_anime-{user_id}', style="success")],
        [InlineKeyboardButton("ساخت پسورد", callback_data=f'create_password-{user_id}', style="success")],
        [InlineKeyboardButton("→", callback_data=f'tools5-{user_id}', style="danger"),
         InlineKeyboardButton("4/6", callback_data=f'pageinfo-{user_id}', style="success"),
         InlineKeyboardButton("←", callback_data=f'tools3-{user_id}', style="success")],
        [InlineKeyboardButton("‹ برگشت ›", callback_data=f'menu1-{user_id}', style="danger")]
    ])

# دکمه‌های ابزار - صفحه 5
def get_tools_page5_buttons(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("تبدیل متن به مورس", callback_data=f'text_to_morse-{user_id}', style="success"),
         InlineKeyboardButton("تبدیل مورس به متن", callback_data=f'morse_to_text-{user_id}', style="danger")],
        [InlineKeyboardButton("دریافت تاریخ", callback_data=f'get_date-{user_id}', style="primary")],
        [InlineKeyboardButton("اطلاعات اکانت", callback_data=f'account_info-{user_id}', style="success"),
         InlineKeyboardButton("اطلاعات پیام", callback_data=f'message_info-{user_id}', style="success")],
        [InlineKeyboardButton("منشن کاربر", callback_data=f'mention_user-{user_id}', style="success")],
        [InlineKeyboardButton("→", callback_data=f'tools6-{user_id}', style="success"),
         InlineKeyboardButton("5/6", callback_data=f'pageinfo-{user_id}', style="success"),
         InlineKeyboardButton("←", callback_data=f'tools4-{user_id}', style="danger")],
        [InlineKeyboardButton("‹ برگشت ›", callback_data=f'menu1-{user_id}', style="danger")]
    ])

# دکمه‌های ابزار - صفحه 6
def get_tools_page6_buttons(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("بررسی کد ملی", callback_data=f'national_code-{user_id}', style="danger"),
         InlineKeyboardButton("استعلام کارت بانکی", callback_data=f'card_inquiry-{user_id}', style="danger")],
        [InlineKeyboardButton("استخراج متن از عکس", callback_data=f'extract_text-{user_id}', style="success")],
        [InlineKeyboardButton("دانلود پرایوت", callback_data=f'private_download-{user_id}', style="danger")],
        [InlineKeyboardButton("→", callback_data=f'tools1-{user_id}', style="success"),
         InlineKeyboardButton("6/6", callback_data=f'pageinfo-{user_id}', style="success"),
         InlineKeyboardButton("←", callback_data=f'tools5-{user_id}', style="danger")],
        [InlineKeyboardButton("‹ برگشت ›", callback_data=f'menu1-{user_id}', style="danger")]
    ])

# دکمه‌های سرگرمی - صفحه 1
def get_entertainment_page1_buttons(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("تاس", callback_data=f'dice-{user_id}', style="success"),
         InlineKeyboardButton("دارت", callback_data=f'dart-{user_id}', style="success")],
        [InlineKeyboardButton("بولینگ", callback_data=f'bowling-{user_id}', style="success")],
        [InlineKeyboardButton("بسکتبال", callback_data=f'basketball-{user_id}', style="success"),
         InlineKeyboardButton("فوتبال", callback_data=f'football-{user_id}', style="danger")],
        [InlineKeyboardButton("فال", callback_data=f'faal-{user_id}', style="primary")],
        [InlineKeyboardButton("→", callback_data=f'entertainment2-{user_id}', style="success"),
         InlineKeyboardButton("1/2", callback_data=f'pageinfo-{user_id}', style="danger"),
         InlineKeyboardButton("←", callback_data=f'entertainment2-{user_id}', style="primary")],
        [InlineKeyboardButton("‹ برگشت ›", callback_data=f'menu1-{user_id}', style="primary")]
    ])

# دکمه‌های سرگرمی - صفحه 2
def get_entertainment_page2_buttons(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("بازی رندوم 2", callback_data=f'random_game2-{user_id}', style="success"),
         InlineKeyboardButton("بازی رندوم 1", callback_data=f'random_game1-{user_id}', style="primary")],
        [InlineKeyboardButton("بازی رندوم 3", callback_data=f'random_game3-{user_id}', style="primary")],
        [InlineKeyboardButton("سایر سرگرمی", callback_data=f'other_fun-{user_id}', style="danger")],
        [InlineKeyboardButton("→", callback_data=f'entertainment1-{user_id}', style="success"),
         InlineKeyboardButton("2/2", callback_data=f'pageinfo-{user_id}', style="success"),
         InlineKeyboardButton("←", callback_data=f'entertainment1-{user_id}', style="primary")],
        [InlineKeyboardButton("‹ برگشت ›", callback_data=f'menu1-{user_id}', style="primary")]
    ])

# دکمه‌های تغییر
def get_taghvir_buttons(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("استیکر", callback_data=f'sticker-{user_id}', style="primary"),
         InlineKeyboardButton("گیف", callback_data=f'gif-{user_id}', style="success")],
        [InlineKeyboardButton("عکس", callback_data=f'photo-{user_id}', style="danger")],
        [InlineKeyboardButton("ساخت استیکر", callback_data=f'create_sticker-{user_id}', style="primary"),
         InlineKeyboardButton("ساخت گیف", callback_data=f'create_gif-{user_id}', style="primary")],
        [InlineKeyboardButton("‹ برگشت ›", callback_data=f'menu1-{user_id}', style="success")]
    ])

# دکمه‌های دشمن
def get_enemy_buttons(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("تنظیم دشمن", callback_data=f'set_enemy-{user_id}', style="success"),
         InlineKeyboardButton("پاکسازی دشمن", callback_data=f'clear_enemy-{user_id}', style="danger")],
        [InlineKeyboardButton("حذف دشمن", callback_data=f'remove_enemy-{user_id}', style="primary"),
         InlineKeyboardButton("لیست دشمن", callback_data=f'list_enemy-{user_id}', style="danger")],
        [InlineKeyboardButton("‹ برگشت ›", callback_data=f'menu2-{user_id}', style="success")]
    ])

# دکمه‌های دوست
def get_friend_buttons(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("افزودن دوست", callback_data=f'add_friend-{user_id}', style="success"),
         InlineKeyboardButton("پاکسازی دوست", callback_data=f'clear_friend-{user_id}', style="success")],
        [InlineKeyboardButton("حذف دوست", callback_data=f'remove_friend-{user_id}', style="danger"),
         InlineKeyboardButton("لیست دوست", callback_data=f'list_friend-{user_id}', style="success")],
        [InlineKeyboardButton("‹ برگشت ›", callback_data=f'menu2-{user_id}', style="primary")]
    ])

# دکمه‌های منشی
def get_secretary_buttons(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("تنظیم متن", callback_data=f'secretary_text-{user_id}', style="success"),
         InlineKeyboardButton("خود منشی", callback_data=f'secretary_self-{user_id}', style="success")],
        [InlineKeyboardButton("تایم منشی", callback_data=f'secretary_time-{user_id}', style="danger")],
        [InlineKeyboardButton("‹ برگشت ›", callback_data=f'menu2-{user_id}', style="success")]
    ])

# دکمه‌های ساعت پروفایل
def get_saat_buttons(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("ساعت پروفایل", callback_data=f'saat_main-{user_id}', style="danger")],
        [InlineKeyboardButton("فونت ساعت", callback_data=f'font_saat-{user_id}', style="success"),
         InlineKeyboardButton("بال ساعت", callback_data=f'bal_saat-{user_id}', style="success")],
        [InlineKeyboardButton("‹ برگشت ›", callback_data=f'menu2-{user_id}', style="primary")]
    ])

# دکمه‌های دانلودر
def get_downloader_buttons(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("دانلودر پرایوت", callback_data=f'private_download-{user_id}', style="danger")],
        [InlineKeyboardButton("‹ برگشت ›", callback_data=f'menu2-{user_id}', style="primary")]
    ])

# دکمه برگشت عمومی
def get_back_button(user_id, back_to):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("‹ برگشت ›", callback_data=f'{back_to}-{user_id}', style="danger")]
    ])

# ==================== هندلر اینلاین ==================== #
@app.on_inline_query()
async def answer(client, inline_query):
     chat_id = inline_query.from_user.id
     
     if inline_query.query == "panel":
          user_id = str(inline_query.from_user.id)
          
          # پنل اصلی با دکمه‌های منوی 1
          await inline_query.answer(
               results=[
                    InlineQueryResultArticle(
                         title="پنل مدیریت سلف",
                         input_message_content=InputTextMessageContent("👑 دستورات سلف! بخش راهنمای دستورات سلف ✔️ - با استفاده از دکمه های زیر بخش موردنظرت رو ببین."),
                         description="پنل مدیریت با سه منوی اصلی",
                         thumb_url="https://telegra.ph/file/7a3b0c5c5c9d2b2b2b2b2.png",
                         reply_markup=get_menu1_buttons(user_id)
                    ),
               ],
               cache_time=1
          )

     elif inline_query.query == "expire" or inline_query.query == "انقضا":
          user_id = str(inline_query.from_user.id)
          diamonds = get_user_diamonds(user_id)
          
          hours, days, remaining_hours, time_text = calculate_expire_time(diamonds)
          
          if hours > 0:
               expire_text = f"""<blockquote>⏰ **زمان باقیمانده**

💎 الماس شما: {diamonds}
⏳ زمان باقیمانده: {time_text}

📊 {hours} ساعت ({days} روز و {remaining_hours} ساعت)</blockquote>"""
          else:
               expire_text = "<blockquote>⏰ **زمان باقیمانده**\n\n💎 الماس کافی ندارید.\nبرای تمدید سلف اقدام کنید.</blockquote>"
          
          await inline_query.answer(
               results=[
                    InlineQueryResultArticle(
                         title="بررسی زمان انقضا",
                         input_message_content=InputTextMessageContent(expire_text),
                         description="زمان باقیمانده از سلف شما بر اساس الماس",
                         thumb_url="https://telegra.ph/file/7a3b0c5c5c9d2b2b2b2b2.png",
                    ),
               ],
               cache_time=1
          )

     elif inline_query.query == "coinprice":
          try:
               s = requests.get('https://api.nobitex.ir/market/stats?srcCurrency=usdt,trx,ton,btc,shib,eth,etc,usdt,ada,bch,ltc,bnb&dstCurrency=irt,rls,usdt')
               s = s.text
               js = json.loads(s)
               byusdt = js['stats']['usdt-irt']['bestBuy']
               sellusdt = js['stats']['usdt-irt']['bestSell']
               bytrx = js['stats']['trx-irt']['bestBuy']
               selltrx = js['stats']['trx-irt']['bestSell']
               byton = js['stats']['ton-irt']['bestBuy']
               sellton = js['stats']['ton-irt']['bestSell']
               byshib = js['stats']['shib-usdt']['bestBuy']
               sellshib = js['stats']['shib-usdt']['bestSell']
               bybit = js['stats']['btc-usdt']['bestBuy']
               sellbit = js['stats']['btc-usdt']['bestSell']
               byet = js['stats']['eth-usdt']['bestBuy']
               sellet = js['stats']['eth-usdt']['bestSell']
               byetc = js['stats']['etc-usdt']['bestBuy']
               selletc = js['stats']['etc-usdt']['bestSell']
               byada = js['stats']['ada-usdt']['bestBuy']
               sellada = js['stats']['ada-usdt']['bestSell']
               bybch = js['stats']['bch-usdt']['bestBuy']
               sellbch = js['stats']['bch-usdt']['bestSell']
               byltc = js['stats']['ltc-usdt']['bestBuy']
               sellltc = js['stats']['ltc-usdt']['bestSell']
               bybnb = js['stats']['bnb-usdt']['bestBuy']
               sellbnb = js['stats']['bnb-usdt']['bestSell']

               coind = InlineKeyboardMarkup(
                    [
                         [
                              InlineKeyboardButton("Currency", callback_data="outside", style="success"),
                              InlineKeyboardButton("Best Buy", callback_data="outside", style="primary"),
                              InlineKeyboardButton("Best Sell", callback_data="outside", style="primary")
                         ],
                         [
                              InlineKeyboardButton("USDT", callback_data="outside", style="danger"),
                              InlineKeyboardButton("☫%s" % byusdt, callback_data="outside", style="primary"),
                              InlineKeyboardButton("☫%s" % sellusdt, callback_data="outside", style="danger")
                         ],
                         [
                              InlineKeyboardButton("TRX", callback_data="outside", style="success"),
                              InlineKeyboardButton("☫%s" % bytrx, callback_data="outside", style="danger"),
                              InlineKeyboardButton("☫%s" % selltrx, callback_data="outside", style="danger")
                         ],
                         [
                              InlineKeyboardButton("TON", callback_data="outside", style="danger"),
                              InlineKeyboardButton("☫%s" % byton, callback_data="outside", style="danger"),
                              InlineKeyboardButton("☫%s" % sellton, callback_data="outside", style="primary")
                         ],
                         [
                              InlineKeyboardButton("SHIB", callback_data="outside", style="danger"),
                              InlineKeyboardButton("$%s" % byshib, callback_data="outside", style="danger"),
                              InlineKeyboardButton("$%s" % sellshib, callback_data="outside", style="primary")
                         ],
                         [
                              InlineKeyboardButton("BTC", callback_data="outside", style="primary"),
                              InlineKeyboardButton("$%s" % bybit, callback_data="outside", style="primary"),
                              InlineKeyboardButton("$%s" % sellbit, callback_data="outside", style="success")
                         ],
                         [
                              InlineKeyboardButton("ETH", callback_data="outside", style="primary"),
                              InlineKeyboardButton("$%s" % byet, callback_data="outside", style="primary"),
                              InlineKeyboardButton("$%s" % sellet, callback_data="outside", style="primary")
                         ],
                         [
                              InlineKeyboardButton("ETC", callback_data="outside", style="success"),
                              InlineKeyboardButton("$%s" % byetc, callback_data="outside", style="primary"),
                              InlineKeyboardButton("$%s" % selletc, callback_data="outside", style="success")
                         ],
                         [
                              InlineKeyboardButton("ADA", callback_data="outside", style="success"),
                              InlineKeyboardButton("$%s" % byada, callback_data="outside", style="primary"),
                              InlineKeyboardButton("$%s" % sellada, callback_data="outside", style="danger")
                         ],
                         [
                              InlineKeyboardButton("BCH", callback_data="outside", style="danger"),
                              InlineKeyboardButton("$%s" % bybch, callback_data="outside", style="primary"),
                              InlineKeyboardButton("$%s" % sellbch, callback_data="outside", style="success")
                         ],
                         [
                              InlineKeyboardButton("LTC", callback_data="outside", style="success"),
                              InlineKeyboardButton("$%s" % byltc, callback_data="outside", style="success"),
                              InlineKeyboardButton("$%s" % sellltc, callback_data="outside", style="primary")
                         ],
                         [
                              InlineKeyboardButton("BNB", callback_data="outside", style="primary"),
                              InlineKeyboardButton("$%s" % bybnb, callback_data="outside", style="primary"),
                              InlineKeyboardButton("$%s" % sellbnb, callback_data="outside", style="success")
                         ],
                         [
                              InlineKeyboardButton("Close ×", callback_data=f'Close-{inline_query.from_user.id}', style="success")
                         ]
                    ]
               )

               await inline_query.answer(
                    results=[
                         InlineQueryResultArticle(
                              title="Coin price",
                              input_message_content=InputTextMessageContent("➣ **Currency price list**"),
                              url="https://t.me/KING_MEMBEER",
                              description="ᴄʀɪᴛᴜs",
                              thumb_url="https://t.me/KING_MEMBEER/33",
                              reply_markup=coind
                         ),
                    ],
                    cache_time=1
               )
          except:
               pass

# ==================== هندلر کالبک ==================== #
@app.on_callback_query()
async def call(app, call):
     if call.data != "outside":
          if int(call.from_user.id) == int(call.data.split("-")[1]):
               callback_type = call.data.split("-")[0]
               user_id = call.data.split("-")[1]
               
               # ============ منوهای اصلی ============ #
               if callback_type == "menu1":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text="👑 دستورات سلف! بخش راهنمای دستورات سلف ✔️ - با استفاده از دکمه های زیر بخش موردنظرت رو ببین.", 
                                              reply_markup=get_menu1_buttons(user_id))
               
               elif callback_type == "menu2":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text="👑 دستورات سلف! بخش راهنمای دستورات سلف ✔️ - با استفاده از دکمه های زیر بخش موردنظرت رو ببین.", 
                                              reply_markup=get_menu2_buttons(user_id))
               
               elif callback_type == "menu3":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text="👑 دستورات سلف! بخش راهنمای دستورات سلف ✔️ - با استفاده از دکمه های زیر بخش موردنظرت رو ببین.", 
                                              reply_markup=get_menu3_buttons(user_id))
               
               # ============ تنظیمات ============ #
               elif callback_type == "tanzimat":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text="<b>‹ بخش ﹝ تنظیمات ﹞ ›</b>\n\nلطفاً دستور مورد نظر را انتخاب کنید:", 
                                              reply_markup=get_tanzimat_buttons(user_id))
               
               elif callback_type == "modiriat":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text="<b>‹ بخش ﹝ مدیریت ﹞ ›</b>\n\nلطفاً دستور مورد نظر را انتخاب کنید:", 
                                              reply_markup=get_modiriat_buttons(user_id))
               
               elif callback_type == "profile_main":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text="<b>‹ بخش ﹝ پروفایل ﹞ ›</b>\n\nلطفاً دستور مورد نظر را انتخاب کنید:", 
                                              reply_markup=get_profile_buttons(user_id))
               
               # ============ سراسری (صفحات) ============ #
               elif callback_type == "sarasari" or callback_type == "sarasari1":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text="<b>‹ بخش ﹝ سراسری ﹞ ›</b>\n\nلطفاً دستور مورد نظر را انتخاب کنید:", 
                                              reply_markup=get_sarasari_page1_buttons(user_id))
               
               elif callback_type == "sarasari2":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text="<b>‹ بخش ﹝ سراسری ﹞ ›</b>\n\nلطفاً دستور مورد نظر را انتخاب کنید:", 
                                              reply_markup=get_sarasari_page2_buttons(user_id))
               
               elif callback_type == "sarasari3":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text="<b>‹ بخش ﹝ سراسری ﹞ ›</b>\n\nلطفاً دستور مورد نظر را انتخاب کنید:", 
                                              reply_markup=get_sarasari_page3_buttons(user_id))
               
               elif callback_type == "sarasari4":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text="<b>‹ بخش ﹝ سراسری ﹞ ›</b>\n\nلطفاً دستور مورد نظر را انتخاب کنید:", 
                                              reply_markup=get_sarasari_page4_buttons(user_id))
               
               elif callback_type == "sarasari5":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text="<b>‹ بخش ﹝ سراسری ﹞ ›</b>\n\nلطفاً دستور مورد نظر را انتخاب کنید:", 
                                              reply_markup=get_sarasari_page5_buttons(user_id))
               
               elif callback_type == "sarasari6":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text="<b>‹ بخش ﹝ سراسری ﹞ ›</b>\n\nلطفاً دستور مورد نظر را انتخاب کنید:", 
                                              reply_markup=get_sarasari_page6_buttons(user_id))
               
               # ============ ابزار (صفحات) ============ #
               elif callback_type == "tools_main" or callback_type == "tools1":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text="<b>‹ بخش ﹝ ابزار ﹞ ›</b>\n\nلطفاً دستور مورد نظر را انتخاب کنید:", 
                                              reply_markup=get_tools_page1_buttons(user_id))
               
               elif callback_type == "tools2":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text="<b>‹ بخش ﹝ ابزار ﹞ ›</b>\n\nلطفاً دستور مورد نظر را انتخاب کنید:", 
                                              reply_markup=get_tools_page2_buttons(user_id))
               
               elif callback_type == "tools3":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text="<b>‹ بخش ﹝ ابزار ﹞ ›</b>\n\nلطفاً دستور مورد نظر را انتخاب کنید:", 
                                              reply_markup=get_tools_page3_buttons(user_id))
               
               elif callback_type == "tools4":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text="<b>‹ بخش ﹝ ابزار ﹞ ›</b>\n\nلطفاً دستور مورد نظر را انتخاب کنید:", 
                                              reply_markup=get_tools_page4_buttons(user_id))
               
               elif callback_type == "tools5":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text="<b>‹ بخش ﹝ ابزار ﹞ ›</b>\n\nلطفاً دستور مورد نظر را انتخاب کنید:", 
                                              reply_markup=get_tools_page5_buttons(user_id))
               
               elif callback_type == "tools6":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text="<b>‹ بخش ﹝ ابزار ﹞ ›</b>\n\nلطفاً دستور مورد نظر را انتخاب کنید:", 
                                              reply_markup=get_tools_page6_buttons(user_id))
               
               # ============ سرگرمی ============ #
               elif callback_type == "entertainment" or callback_type == "entertainment1":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text="<b>‹ بخش ﹝ سرگرمی ﹞ ›</b>\n\nلطفاً دستور مورد نظر را انتخاب کنید:", 
                                              reply_markup=get_entertainment_page1_buttons(user_id))
               
               elif callback_type == "entertainment2":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text="<b>‹ بخش ﹝ سرگرمی ﹞ ›</b>\n\nلطفاً دستور مورد نظر را انتخاب کنید:", 
                                              reply_markup=get_entertainment_page2_buttons(user_id))
               
               # ============ تغییر ============ #
               elif callback_type == "taghvir":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text="<b>‹ بخش ﹝ تغییر ﹞ ›</b>\n\nلطفاً دستور مورد نظر را انتخاب کنید:", 
                                              reply_markup=get_taghvir_buttons(user_id))
               
               # ============ دشمن ============ #
               elif callback_type == "enemy_main":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text="<b>‹ بخش ﹝ دشمن ﹞ ›</b>\n\nلطفاً دستور مورد نظر را انتخاب کنید:", 
                                              reply_markup=get_enemy_buttons(user_id))
               
               # ============ دوست ============ #
               elif callback_type == "friend_main":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text="<b>‹ بخش ﹝ دوست ﹞ ›</b>\n\nلطفاً دستور مورد نظر را انتخاب کنید:", 
                                              reply_markup=get_friend_buttons(user_id))
               
               # ============ منشی ============ #
               elif callback_type == "secretary_main":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text="<b>‹ بخش ﹝ منشی ﹞ ›</b>\n\nلطفاً دستور مورد نظر را انتخاب کنید:", 
                                              reply_markup=get_secretary_buttons(user_id))
               
               # ============ ساعت پروفایل ============ #
               elif callback_type == "saat":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text="<b>‹ بخش ﹝ ساعت پروفایل ﹞ ›</b>\n\nلطفاً دستور مورد نظر را انتخاب کنید:", 
                                              reply_markup=get_saat_buttons(user_id))
               
               # ============ دانلودر ============ #
               elif callback_type == "downloader":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text="<b>‹ بخش ﹝ دانلودر ﹞ ›</b>\n\nلطفاً دستور مورد نظر را انتخاب کنید:", 
                                              reply_markup=get_downloader_buttons(user_id))
               
               # ============ تنظیمات (دکمه‌های داخلی) ============ #
               elif callback_type == "self":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_self, 
                                              reply_markup=get_back_button(user_id, "tanzimat"))
               
               elif callback_type == "tag":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_tag, 
                                              reply_markup=get_back_button(user_id, "tanzimat"))
               
               elif callback_type == "filter_words":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_filter_words, 
                                              reply_markup=get_back_button(user_id, "tanzimat"))
               
               elif callback_type == "auto_response":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_auto_response, 
                                              reply_markup=get_back_button(user_id, "tanzimat"))
               
               # ============ مدیریت (دکمه‌های داخلی) ============ #
               elif callback_type == "expire":
                    diamonds = get_user_diamonds(user_id)
                    hours, days, remaining_hours, time_text = calculate_expire_time(diamonds)
                    
                    if hours > 0:
                         expire_text = f"""<blockquote>⏰ **زمان باقیمانده**

💎 الماس شما: {diamonds}
⏳ زمان باقیمانده: {time_text}

📊 {hours} ساعت ({days} روز و {remaining_hours} ساعت)</blockquote>"""
                    else:
                         expire_text = "<blockquote>⏰ **زمان باقیمانده**\n\n💎 الماس کافی ندارید.\nبرای تمدید سلف اقدام کنید.</blockquote>"
                    
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=expire_text, 
                                              reply_markup=get_back_button(user_id, "modiriat"))
               
               elif callback_type == "restart_self":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_restart_self, 
                                              reply_markup=get_back_button(user_id, "modiriat"))
               
               elif callback_type == "card":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_card, 
                                              reply_markup=get_back_button(user_id, "modiriat"))
               
               elif callback_type == "proxy":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_proxy, 
                                              reply_markup=get_back_button(user_id, "modiriat"))
               
               # ============ پروفایل (دکمه‌های داخلی) ============ #
               elif callback_type == "name":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_name, 
                                              reply_markup=get_back_button(user_id, "profile_main"))
               
               elif callback_type == "lastname":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_lastname, 
                                              reply_markup=get_back_button(user_id, "profile_main"))
               
               elif callback_type == "bios":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_bio, 
                                              reply_markup=get_back_button(user_id, "profile_main"))
               
               elif callback_type == "time_bio":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_time_bio, 
                                              reply_markup=get_back_button(user_id, "profile_main"))
               
               elif callback_type == "profile_pic":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_profile_pic, 
                                              reply_markup=get_back_button(user_id, "profile_main"))
               
               elif callback_type == "delete_profile":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_delete_profile, 
                                              reply_markup=get_back_button(user_id, "profile_main"))
               
               # ============ سراسری (دکمه‌های داخلی) ============ #
               elif callback_type == "silence":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_silence, 
                                              reply_markup=get_back_button(user_id, "sarasari1"))
               
               elif callback_type == "unsilence":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_unsilence, 
                                              reply_markup=get_back_button(user_id, "sarasari1"))
               
               elif callback_type == "clear_silence":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_clear_silence, 
                                              reply_markup=get_back_button(user_id, "sarasari1"))
               
               elif callback_type == "block":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_block, 
                                              reply_markup=get_back_button(user_id, "sarasari1"))
               
               elif callback_type == "unblock":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_unblock, 
                                              reply_markup=get_back_button(user_id, "sarasari1"))
               
               elif callback_type == "enemy":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_enemy, 
                                              reply_markup=get_back_button(user_id, "sarasari1"))
               
               elif callback_type == "offline":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_offline, 
                                              reply_markup=get_back_button(user_id, "sarasari2"))
               
               elif callback_type == "friend":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_friend, 
                                              reply_markup=get_back_button(user_id, "sarasari2"))
               
               elif callback_type == "secretary":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_secretary_main, 
                                              reply_markup=get_back_button(user_id, "sarasari2"))
               
               elif callback_type == "spam_main":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_spam_main, 
                                              reply_markup=get_back_button(user_id, "sarasari2"))
               
               elif callback_type == "tag_alert":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_tag_alert, 
                                              reply_markup=get_back_button(user_id, "sarasari2"))
               
               elif callback_type == "create_channel":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_create_channel, 
                                              reply_markup=get_back_button(user_id, "sarasari2"))
               
               elif callback_type == "create_group":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_create_group, 
                                              reply_markup=get_back_button(user_id, "sarasari3"))
               
               elif callback_type == "create_supergroup":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_create_supergroup, 
                                              reply_markup=get_back_button(user_id, "sarasari3"))
               
               elif callback_type == "delete_main":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_delete_main, 
                                              reply_markup=get_back_button(user_id, "sarasari3"))
               
               elif callback_type == "welcome_main":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_welcome_main, 
                                              reply_markup=get_back_button(user_id, "sarasari3"))
               
               elif callback_type == "first_comment":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_first_comment, 
                                              reply_markup=get_back_button(user_id, "sarasari3"))
               
               elif callback_type == "ban":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_ban, 
                                              reply_markup=get_back_button(user_id, "sarasari4"))
               
               elif callback_type == "unban":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_unban, 
                                              reply_markup=get_back_button(user_id, "sarasari4"))
               
               elif callback_type == "set_silence":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_set_silence, 
                                              reply_markup=get_back_button(user_id, "sarasari4"))
               
               elif callback_type == "set_group_pic":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_set_group_pic, 
                                              reply_markup=get_back_button(user_id, "sarasari4"))
               
               elif callback_type == "set_group_name":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_set_group_name, 
                                              reply_markup=get_back_button(user_id, "sarasari4"))
               
               elif callback_type == "set_group_bio":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_set_group_bio, 
                                              reply_markup=get_back_button(user_id, "sarasari5"))
               
               elif callback_type == "set_group_username":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_set_group_username, 
                                              reply_markup=get_back_button(user_id, "sarasari5"))
               
               elif callback_type == "pin":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_pin, 
                                              reply_markup=get_back_button(user_id, "sarasari5"))
               
               elif callback_type == "unpin":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_unpin, 
                                              reply_markup=get_back_button(user_id, "sarasari5"))
               
               elif callback_type == "unpin_all":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_unpin_all, 
                                              reply_markup=get_back_button(user_id, "sarasari5"))
               
               elif callback_type == "tag_admin":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_tag_admin, 
                                              reply_markup=get_back_button(user_id, "sarasari6"))
               
               elif callback_type == "tag_members":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_tag_members, 
                                              reply_markup=get_back_button(user_id, "sarasari6"))
               
               # ============ ابزار (دکمه‌های داخلی) ============ #
               elif callback_type == "extract_file":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_extract_file, 
                                              reply_markup=get_back_button(user_id, "tools1"))
               
               elif callback_type == "car_price":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_car_price, 
                                              reply_markup=get_back_button(user_id, "tools1"))
               
               elif callback_type == "rename_file":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_rename_file, 
                                              reply_markup=get_back_button(user_id, "tools1"))
               
               elif callback_type == "number_checker":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_number_checker, 
                                              reply_markup=get_back_button(user_id, "tools1"))
               
               elif callback_type == "text_screenshot":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_text_screenshot, 
                                              reply_markup=get_back_button(user_id, "tools1"))
               
               elif callback_type == "custom_screenshot":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_custom_screenshot, 
                                              reply_markup=get_back_button(user_id, "tools1"))
               
               elif callback_type == "get_ip":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_get_ip, 
                                              reply_markup=get_back_button(user_id, "tools2"))
               
               elif callback_type == "weather":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_weather, 
                                              reply_markup=get_back_button(user_id, "tools2"))
               
               elif callback_type == "azan":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_azan, 
                                              reply_markup=get_back_button(user_id, "tools2"))
               
               elif callback_type == "currency":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_currency, 
                                              reply_markup=get_back_button(user_id, "tools2"))
               
               elif callback_type == "calculator":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_calculator, 
                                              reply_markup=get_back_button(user_id, "tools2"))
               
               elif callback_type == "ip_info":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_ip_info, 
                                              reply_markup=get_back_button(user_id, "tools2"))
               
               elif callback_type == "gold":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_gold, 
                                              reply_markup=get_back_button(user_id, "tools2"))
               
               elif callback_type == "cricket":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_cricket, 
                                              reply_markup=get_back_button(user_id, "tools3"))
               
               elif callback_type == "site_ping":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_site_ping, 
                                              reply_markup=get_back_button(user_id, "tools3"))
               
               elif callback_type == "site_screenshot":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_site_screenshot, 
                                              reply_markup=get_back_button(user_id, "tools3"))
               
               elif callback_type == "copy_profile":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_copy_profile, 
                                              reply_markup=get_back_button(user_id, "tools3"))
               
               elif callback_type == "account_date":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_account_date, 
                                              reply_markup=get_back_button(user_id, "tools3"))
               
               elif callback_type == "limit_status":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_limit_status, 
                                              reply_markup=get_back_button(user_id, "tools3"))
               
               elif callback_type == "system":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_system, 
                                              reply_markup=get_back_button(user_id, "tools3"))
               
               elif callback_type == "country_info":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_country_info, 
                                              reply_markup=get_back_button(user_id, "tools4"))
               
               elif callback_type == "translate_fa":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_translate_fa, 
                                              reply_markup=get_back_button(user_id, "tools4"))
               
               elif callback_type == "translate_en":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_translate_en, 
                                              reply_markup=get_back_button(user_id, "tools4"))
               
               elif callback_type == "download_movie":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_download_movie, 
                                              reply_markup=get_back_button(user_id, "tools4"))
               
               elif callback_type == "download_anime":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_download_anime, 
                                              reply_markup=get_back_button(user_id, "tools4"))
               
               elif callback_type == "create_password":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_create_password, 
                                              reply_markup=get_back_button(user_id, "tools4"))
               
               elif callback_type == "text_to_morse":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_text_to_morse, 
                                              reply_markup=get_back_button(user_id, "tools5"))
               
               elif callback_type == "morse_to_text":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_morse_to_text, 
                                              reply_markup=get_back_button(user_id, "tools5"))
               
               elif callback_type == "get_date":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_get_date, 
                                              reply_markup=get_back_button(user_id, "tools5"))
               
               elif callback_type == "account_info":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_account_info, 
                                              reply_markup=get_back_button(user_id, "tools5"))
               
               elif callback_type == "message_info":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_message_info, 
                                              reply_markup=get_back_button(user_id, "tools5"))
               
               elif callback_type == "mention_user":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_mention_user, 
                                              reply_markup=get_back_button(user_id, "tools5"))
               
               elif callback_type == "national_code":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_national_code, 
                                              reply_markup=get_back_button(user_id, "tools6"))
               
               elif callback_type == "card_inquiry":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_card_inquiry, 
                                              reply_markup=get_back_button(user_id, "tools6"))
               
               elif callback_type == "extract_text":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_extract_text, 
                                              reply_markup=get_back_button(user_id, "tools6"))
               
               elif callback_type == "private_download":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_private_download, 
                                              reply_markup=get_back_button(user_id, "tools6"))
               
               elif callback_type == "instagram_dl":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_instagram_dl, 
                                              reply_markup=get_back_button(user_id, "tools6"))
               
               # ============ سرگرمی (دکمه‌های داخلی) ============ #
               elif callback_type == "dice":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_dice, 
                                              reply_markup=get_back_button(user_id, "entertainment1"))
               
               elif callback_type == "dart":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_dart, 
                                              reply_markup=get_back_button(user_id, "entertainment1"))
               
               elif callback_type == "bowling":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_bowling, 
                                              reply_markup=get_back_button(user_id, "entertainment1"))
               
               elif callback_type == "basketball":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_basketball, 
                                              reply_markup=get_back_button(user_id, "entertainment1"))
               
               elif callback_type == "football":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_football, 
                                              reply_markup=get_back_button(user_id, "entertainment1"))
               
               elif callback_type == "faal":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_faal, 
                                              reply_markup=get_back_button(user_id, "entertainment1"))
               
               elif callback_type == "random_game1":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_random_game1, 
                                              reply_markup=get_back_button(user_id, "entertainment2"))
               
               elif callback_type == "random_game2":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_random_game2, 
                                              reply_markup=get_back_button(user_id, "entertainment2"))
               
               elif callback_type == "random_game3":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_random_game3, 
                                              reply_markup=get_back_button(user_id, "entertainment2"))
               
               elif callback_type == "other_fun":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_other_fun, 
                                              reply_markup=get_back_button(user_id, "entertainment2"))
               
               # ============ تغییر (دکمه‌های داخلی) ============ #
               elif callback_type == "sticker":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_sticker, 
                                              reply_markup=get_back_button(user_id, "taghvir"))
               
               elif callback_type == "gif":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_gif, 
                                              reply_markup=get_back_button(user_id, "taghvir"))
               
               elif callback_type == "photo":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_photo, 
                                              reply_markup=get_back_button(user_id, "taghvir"))
               
               elif callback_type == "create_sticker":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_create_sticker, 
                                              reply_markup=get_back_button(user_id, "taghvir"))
               
               elif callback_type == "create_gif":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_create_gif, 
                                              reply_markup=get_back_button(user_id, "taghvir"))
               
               # ============ تبچی ============ #
               elif callback_type == "tabchi_main":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_tabchi_main, 
                                              reply_markup=get_back_button(user_id, "menu1"))
               
               # ============ هوش مصنوعی ============ #
               elif callback_type == "ai":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_ai, 
                                              reply_markup=get_back_button(user_id, "menu2"))
               
               # ============ ساعت پروفایل (دکمه‌های داخلی) ============ #
               elif callback_type == "saat_main":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_saat, 
                                              reply_markup=get_back_button(user_id, "saat"))
               
               elif callback_type == "font_saat":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_font_saat, 
                                              reply_markup=get_back_button(user_id, "saat"))
               
               elif callback_type == "bal_saat":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_balsaat, 
                                              reply_markup=get_back_button(user_id, "saat"))
               
               # ============ حالت متن ============ #
               elif callback_type == "text_mode":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_text_mode, 
                                              reply_markup=get_back_button(user_id, "menu2"))
               
               # ============ اطلاعات ============ #
               elif callback_type == "info_main":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_info_user, 
                                              reply_markup=get_back_button(user_id, "menu2"))
               
               # ============ حالت اکشن ============ #
               elif callback_type == "action_mode":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_action_mode, 
                                              reply_markup=get_back_button(user_id, "menu2"))
               
               # ============ ذخیره تایمدار ============ #
               elif callback_type == "time_save" or callback_type == "time_save2":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_time_save, 
                                              reply_markup=get_back_button(user_id, "menu3"))
               
               # ============ سین خودکار ============ #
               elif callback_type == "auto_seen":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_auto_seen, 
                                              reply_markup=get_back_button(user_id, "menu3"))
               
               # ============ ضدلاگین ============ #
               elif callback_type == "anti_login":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_anti_login, 
                                              reply_markup=get_back_button(user_id, "menu3"))
               
               # ============ ری‌اکشن ============ #
               elif callback_type == "reaction":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_reaction, 
                                              reply_markup=get_back_button(user_id, "menu3"))
               
               # ============ دشمن (دکمه‌های داخلی) ============ #
               elif callback_type == "set_enemy":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_enemy, 
                                              reply_markup=get_back_button(user_id, "enemy_main"))
               
               elif callback_type == "clear_enemy":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_clear_enemy, 
                                              reply_markup=get_back_button(user_id, "enemy_main"))
               
               elif callback_type == "remove_enemy":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_enemy, 
                                              reply_markup=get_back_button(user_id, "enemy_main"))
               
               elif callback_type == "list_enemy":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_list_enemy, 
                                              reply_markup=get_back_button(user_id, "enemy_main"))
               
               # ============ دوست (دکمه‌های داخلی) ============ #
               elif callback_type == "add_friend":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_add_friend, 
                                              reply_markup=get_back_button(user_id, "friend_main"))
               
               elif callback_type == "clear_friend":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_clear_friend, 
                                              reply_markup=get_back_button(user_id, "friend_main"))
               
               elif callback_type == "remove_friend":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_add_friend, 
                                              reply_markup=get_back_button(user_id, "friend_main"))
               
               elif callback_type == "list_friend":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_list_friend, 
                                              reply_markup=get_back_button(user_id, "friend_main"))
               
               # ============ منشی (دکمه‌های داخلی) ============ #
               elif callback_type == "secretary_text":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_secretary_text, 
                                              reply_markup=get_back_button(user_id, "secretary_main"))
               
               elif callback_type == "secretary_self":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_secretary_self, 
                                              reply_markup=get_back_button(user_id, "secretary_main"))
               
               elif callback_type == "secretary_time":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text=help_secretary_time, 
                                              reply_markup=get_back_button(user_id, "secretary_main"))
               
               # ============ بستن پنل ============ #
               elif callback_type == "closepanel":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text="**● پنل بسته شد ●**")
               
               elif callback_type == "Close":
                    await app.edit_inline_text(inline_message_id=call.inline_message_id, 
                                              text="**● Closed ●**")
               
               elif callback_type == "pageinfo":
                    await call.answer("شما در این صفحه هستید", show_alert=False)
               
               else:
                    await call.answer("این بخش در حال توسعه است", show_alert=True)
          else:
               await call.answer("🚫 شما فقط می‌توانید به پنل خودتان دسترسی داشته باشید!", show_alert=True)
     else:
          await call.answer("این دکمه نمایشی است", show_alert=True)

@app.on_message(filters.private&filters.command("restart"), group=1)
async def updates(app, m:Message):
     OwnerUser = get_data(f"SELECT * FROM ownerlist WHERE id = '{m.chat.id}' LIMIT 1")
     if OwnerUser is not None:
          await app.send_message(m.chat.id, "**Helper Restart was successful**")
          python = sys.executable
          os.execl(python, python, *sys.argv)
          update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
    
@app.on_message(filters.private&filters.command("panel"))
async def updates(app, m:Message):
     OwnerUser = get_data(f"SELECT * FROM ownerlist WHERE id = '{m.chat.id}' LIMIT 1")
     if OwnerUser is not None:
          await app.send_message(m.chat.id, "**QuiteCreateCliBot Panel Owner**", reply_markup=keyboard_idk)
          update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
    
@app.on_message(filters.private&filters.command("start"))
async def updates(app, m:Message):
     # همه کاربران می‌توانند /start بزنند
     await app.send_message(m.chat.id, 
          f"""سلام {m.from_user.first_name} 👋

برای باز کردن پنل ، روی دکمه زیر کلیک کنید:
          """, 
          reply_markup=openpanelbot)
     
     update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")

# دستور پنل برای همه کاربران
@app.on_message(filters.private & (filters.regex('^پنل$') | filters.regex('^راهنما$')))
async def show_panel(app, m):
    await app.send_message(
        m.chat.id,
        "برای باز کردن پنل مدیریت، روی دکمه زیر کلیک کنید:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎛 باز کردن پنل", switch_inline_query_current_chat='panel', style="danger")]
        ])
    )
   #______________________________Owner Panel________________________

Back = ReplyKeyboardMarkup(
     [
          [
               ("Back")
          ]
     ],resize_keyboard=True
)

@app.on_message(filters.private)
async def updates(app, m:Message):
 OwnerUser = get_data(f"SELECT * FROM ownerlist WHERE id = '{m.chat.id}' LIMIT 1")
 if OwnerUser is not None:
     user = get_data(f"SELECT * FROM user WHERE id = '{m.chat.id}' LIMIT 1")
     OwnerList = get_datas("SELECT * FROM ownerlist")
     AdminList = get_datas("SELECT * FROM adminlist")
     text = m.text

     if text == "Back":
          await app.send_message(m.chat.id, "**QuiteCreateCliBot Panel Owner**", reply_markup=keyboard_idk)
          update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")

     elif text == "Add Admin":
          await app.send_message(m.chat.id, "**Send Me User ID**:", reply_markup=Back)
          update_data(f"UPDATE user SET step = 'addadmin' WHERE id = '{m.chat.id}' LIMIT 1")

     elif user["step"] == "addadmin":
          if text.isdigit():
               user_id = int(text.strip())
               if get_data(f"SELECT * FROM adminlist WHERE id = '{user_id}' LIMIT 1") is None:
                    await app.send_message(m.chat.id, f"Successfull\nUser [ `{user_id}` ] Added to Admin List")
                    update_data(f"INSERT INTO adminlist(id) VALUES({user_id})")
               else:
                    await app.send_message(m.chat.id, "This user in the Admin list")
          else:
               await app.send_message(m.chat.id, "Invalid entry! Only sending numbers is allowed")

     elif text == "Delete Admin":
          await app.send_message(m.chat.id, "**Send Me User ID**:", reply_markup=Back)
          update_data(f"UPDATE user SET step = 'deladmin' WHERE id = '{m.chat.id}' LIMIT 1")

     elif user["step"] == "deladmin":
          if text.isdigit():
               user_id = int(text.strip())
               if get_data(f"SELECT * FROM adminlist WHERE id = '{user_id}' LIMIT 1") is not None:
                    await app.send_message(m.chat.id, f"Successfull\nUser [ `{user_id}` ] Deleted From User List")
                    update_data(f"DELETE FROM adminlist WHERE id = '{user_id}' LIMIT 1")
               else:
                    await app.send_message(m.chat.id, f"This user not in Admin list")
          else:
               await app.send_message(m.chat.id, "Invalid entry! Only sending numbers is allowed")
             
     elif text == "Admin List":
          s = ""
          if AdminList:
               for index, user in enumerate(AdminList, start=1):
                    s += f"֍ {index} -> `{user[0]}`\n"
               await app.send_message(m.chat.id, f"**Admin List:**\n{s}")
          else:
               await app.send_message(m.chat.id, f"**Admin List is Empty**")
          update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")

     elif text == "Add Owner":
          await app.send_message(m.chat.id, "**Send Me User ID**:", reply_markup=Back)
          update_data(f"UPDATE user SET step = 'addowner' WHERE id = '{m.chat.id}' LIMIT 1")

     elif user["step"] == "addowner":
          if text.isdigit():
               user_id = int(text.strip())
               if get_data(f"SELECT * FROM ownerlist WHERE id = '{user_id}' LIMIT 1") is None:
                    if get_data(f"SELECT * FROM adminlist WHERE id = '{user_id}' LIMIT 1") is not None:
                         await app.send_message(m.chat.id, f"Successfull\nUser [ `{user_id}` ] Added to Owner List")
                         update_data(f"INSERT INTO ownerlist(id) VALUES({user_id})")
                    else:
                         await app.send_message(m.chat.id, "ابتدا کاربر مورد نظر را به لیست ادمین اضافه کنید!")
               else:
                    await app.send_message(m.chat.id, "This user in the Owner list")
          else:
               await app.send_message(m.chat.id, "Invalid entry! Only sending numbers is allowed")

     elif text == "Delete Owner":
          await app.send_message(m.chat.id, "**Send Me User ID**:", reply_markup=Back)
          update_data(f"UPDATE user SET step = 'delowner' WHERE id = '{m.chat.id}' LIMIT 1")

     elif user["step"] == "delowner":
          if text.isdigit():
               user_id = int(text.strip())
               if get_data(f"SELECT * FROM ownerlist WHERE id = '{user_id}' LIMIT 1") is not None:
                    await app.send_message(m.chat.id, f"Successfull\nUser [ `{user_id}` ] Deleted From User List")
                    update_data(f"DELETE FROM ownerlist WHERE id = '{user_id}' LIMIT 1")
               else:
                    await app.send_message(m.chat.id, f"This user not in Owner list")
          else:
               await app.send_message(m.chat.id, "Invalid entry! Only sending numbers is allowed")
             
     elif text == "Owner List":
          s = ""
          if OwnerList:
               for index, user in enumerate(OwnerList, start=1):
                    s += f"֍ {index} -> `{user[0]}`\n"
               await app.send_message(m.chat.id, f"**Owner List:**\n{s}")
          else:
               await app.send_message(m.chat.id, f"**Owner List is Empty**")
          update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")

app.start(), print(Fore.YELLOW+"Started..."), idle(), app.stop()