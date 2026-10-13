from colorama import Fore
from pyrogram import Client, filters, idle, errors
from pyrogram.types import *
from functools import wraps
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
import subprocess
import html
import zipfile
import pymysql
import shutil
import signal
import re
import os

#==================== Config =====================#
Admin = 8335031839  # عددی مالک
Token = "" #توکن بزار
API_ID = اپی ایدی  # ایپی ایدی اکانت مالک
API_HASH = "اپی هش"  # ایپی هش اکانت مالک
Channel_ID = "Vortex_Selff"  # ایدی چنل بدون @ (کانال پیشفرض اول)
Helper_ID = "Vortex_SelfPanel_Bot"  # ایدی ربات هلپر بدون 
DBName = "selfsazv_self"  # اسم دیتابیس اصلی
DBUser = "selfsazv_self"  # یوزرنیم دیتابیس اصلی
DBPass = "selfsazv_self"  # پسورد دیتابیس اصلی
HelperDBName = "selfsazv_panel"  # اسم دیتابیس هلپر
HelperDBUser = "selfsazv_panel"  # یوزرنیم دیتابیس هلپر
HelperDBPass = "selfsazv_panel"  # پسورد دیتابیس هلپر
CardNumber = "6037701589357612"  # شماره کارت برای فروش
CardName = "محمد دارانی"  # اسم دارنده کارت

#==================== Create =====================#
if not os.path.isdir("sessions"):
    os.mkdir("sessions")
if not os.path.isdir("selfs"):
    os.mkdir("selfs")

#===================== App =======================#
app = Client("Bot", api_id=API_ID, api_hash=API_HASH, bot_token=Token)
scheduler = AsyncIOScheduler()
scheduler.start()
def safe_config_check():
    missing = []
    if not Token: missing.append("Token")
    if not API_ID: missing.append("API_ID")
    if not API_HASH: missing.append("API_HASH")
    if missing:
        raise RuntimeError(f"Missing required config values: {', '.join(missing)}")
    if not all([DBName, DBUser, DBPass]):
        print("[WARN] Database credentials are empty; DB operations will fail until configured.")

safe_config_check()
temp_Client = {}
lock = asyncio.Lock()

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


def get_datas(query, params=None):
    with pymysql.connect(host="localhost", database=DBName, user=DBUser, password=DBPass) as connect:
        db = connect.cursor()
        db.execute(query, params or ())
        result = db.fetchall()
        return result

def update_data(query, params=None):
    with pymysql.connect(host="localhost", database=DBName, user=DBUser, password=DBPass) as connect:
        db = connect.cursor()
        db.execute(query, params or ())
        connect.commit()

def helper_getdata(query, params=None):
    with pymysql.connect(host="localhost", database=HelperDBName, user=HelperDBUser, password=HelperDBPass) as connect:
        db = connect.cursor()
        db.execute(query, params or ())
        result = db.fetchone()
        return result

def helper_updata(query, params=None):
    with pymysql.connect(host="localhost", database=HelperDBName, user=HelperDBUser, password=HelperDBPass) as connect:
        db = connect.cursor()
        db.execute(query, params or ())
        connect.commit()

# ایجاد فیلدهای پیشرفته و جدول کانال‌های جوین اجباری در صورت عدم وجود
update_data("""
CREATE TABLE IF NOT EXISTS bot(
status varchar(10) DEFAULT 'ON',
channel_id varchar(150) DEFAULT 'vexelbot_tm',
card_number varchar(50) DEFAULT '6219861995063954',
card_name varchar(150) DEFAULT 'محمدرضا نقدی',
p1 bigint DEFAULT 70000, p2 bigint DEFAULT 140000, p3 bigint DEFAULT 210000, p4 bigint DEFAULT 280000, p5 bigint DEFAULT 350000,
start_text text DEFAULT NULL,
help_text text DEFAULT NULL
) default charset=utf8mb4;
""")
update_data("""
CREATE TABLE IF NOT EXISTS user(
id bigint PRIMARY KEY,
step varchar(150) DEFAULT 'none',
phone varchar(150) DEFAULT NULL,
amount bigint DEFAULT '0',
expir bigint DEFAULT '0',
account varchar(50) DEFAULT 'verified',
self varchar(50) DEFAULT 'inactive',
pid bigint DEFAULT NULL
) default charset=utf8mb4;
""")
update_data("""
CREATE TABLE IF NOT EXISTS block(
id bigint PRIMARY KEY
) default charset=utf8mb4;
""")
update_data("""
CREATE TABLE IF NOT EXISTS fjoin_channels(
username varchar(150) PRIMARY KEY
) default charset=utf8mb4;
""")
helper_updata("""
CREATE TABLE IF NOT EXISTS ownerlist(
id bigint PRIMARY KEY
) default charset=utf8mb4;
""")
helper_updata("""
CREATE TABLE IF NOT EXISTS adminlist(
id bigint PRIMARY KEY
) default charset=utf8mb4;
""")

bot = get_data("SELECT * FROM bot")
if bot is None:
    update_data("INSERT INTO bot() VALUES()")
    update_data(f"INSERT IGNORE INTO fjoin_channels(username) VALUES('{Channel_ID}')")
else:
    # بررسی داینامیک ستون‌های پیشرفته دیتابیس
    bot_columns = [row[0] for row in get_datas("SHOW COLUMNS FROM bot")]
    for col, expr in [("channel_id", "varchar(150) DEFAULT 'vexelbot_tm'"), ("card_number", "varchar(50) DEFAULT '6219861995063954'"), ("card_name", "varchar(150) DEFAULT 'محمدرضا نقدی'"), ("p1", "bigint DEFAULT 70000"), ("p2", "bigint DEFAULT 140000"), ("p3", "bigint DEFAULT 210000"), ("p4", "bigint DEFAULT 280000"), ("p5", "bigint DEFAULT 350000"), ("start_text", "text DEFAULT NULL"), ("help_text", "text DEFAULT NULL")]:
        if col not in bot_columns: update_data(f"ALTER TABLE bot ADD COLUMN {col} {expr}")
    # اگر جدول کانال‌ها خالی بود کانال اصلی اولیه ادد بشه
    if not get_datas("SELECT * FROM fjoin_channels"):
        update_data(f"INSERT IGNORE INTO fjoin_channels(username) VALUES('{bot['channel_id']}')")

OwnerUser = helper_getdata(f"SELECT * FROM ownerlist WHERE id = '{Admin}' LIMIT 1")
if OwnerUser is None:
    helper_updata(f"INSERT INTO ownerlist(id) VALUES({Admin})")

AdminUser = helper_getdata(f"SELECT * FROM adminlist WHERE id = '{Admin}' LIMIT 1")
if AdminUser is None:
    helper_updata(f"INSERT INTO adminlist(id) VALUES({Admin})")

def add_admin(user_id):
    if helper_getdata(f"SELECT * FROM adminlist WHERE id = '{user_id}' LIMIT 1") is None:
        helper_updata(f"INSERT INTO adminlist(id) VALUES({user_id})")

def delete_admin(user_id):
    if helper_getdata(f"SELECT * FROM adminlist WHERE id = '{user_id}' LIMIT 1") is not None:
        helper_updata(f"DELETE FROM adminlist WHERE id = '{user_id}' LIMIT 1")

def check_is_admin(user_id):
    if user_id == Admin: return True
    return helper_getdata(f"SELECT * FROM adminlist WHERE id = '{user_id}' LIMIT 1") is not None

# تابع چکر ارتقایافته برای بررسی بی‌نهایت کانال جوین اجباری به صورت همزمان
def checker(func):
    @wraps(func)
    async def wrapper(c, m, *args, **kwargs):
        chat_id = m.chat.id if hasattr(m, "chat") else m.from_user.id
        bot = get_data("SELECT * FROM bot")
        block = get_data(f"SELECT * FROM block WHERE id = '{chat_id}' LIMIT 1")

        if block is not None and chat_id != Admin:
            return

        # استخراج کل کانال‌های قفل شده از دیتابیس
        channels = get_datas("SELECT username FROM fjoin_channels")
        for ch in channels:
            ch_username = ch[0]
            try:
                await app.get_chat_member(ch_username, chat_id)
            except errors.UserNotParticipant:
                await app.send_message(chat_id, f"""**• برای استفاده از خدمات ما باید ابتدا در کانال زیر عضو باشید ، بعد از اینکه عضو شدید ربات را مجدد استارت کنید.\n/start**""", reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(text="عضویت در چنل قفل شده 🔐", url=f"https://t.me/{ch_username}", style="danger")
                        ]
                    ]
                ))
                return
            except errors.ChatAdminRequired:
                if chat_id == Admin:
                    await app.send_message(Admin, f"ربات برای فعال شدن جوین اجباری در کانال @{ch_username} ادمین نمی باشد!\nلطفا ربات را در این کانال ادمین کنید.")
                return
            except Exception:
                pass

        if bot["status"] == "OFF" and chat_id != Admin and not check_is_admin(chat_id):
            await app.send_message(chat_id, "**ربات خاموش میباشد!**")
            return

        return await func(c, m, *args, **kwargs)
    return wrapper

# تابع کسر ساعتی انقضا - بدون تغییر
async def expirdec(user_id):
    user = get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1")
    user_expir = user["expir"]
    if user_expir > 0:
        user_upexpir = user_expir - 1
        update_data(f"UPDATE user SET expir = '{user_upexpir}' WHERE id = '{user_id}' LIMIT 1")
    else:
        job = scheduler.get_job(str(user_id))
        if job:
            scheduler.remove_job(str(user_id))
        if user_id != Admin:
            delete_admin(user_id)
        if os.path.isdir(f"selfs/self-{user_id}"):
            pid = user["pid"]
            try:
                if pid:
                    os.killpg(os.getpgid(pid), signal.SIGKILL)
                    await asyncio.sleep(2)
            except:
                pass
            shutil.rmtree(f"selfs/self-{user_id}")
        if os.path.isfile(f"sessions/{user_id}.session"):
            async with Client(f"sessions/{user_id}") as user_client:
                await user_client.log_out()
            if os.path.isfile(f"sessions/{user_id}.session"):
                os.remove(f"sessions/{user_id}.session")
        if os.path.isfile(f"sessions/{user_id}.session-journal"):
            os.remove(f"sessions/{user_id}.session-journal")
        await app.send_message(user_id, "کاربر گرامی اشتراک سلف شما به پایان رسید. برای خرید مجدد اشتراک به قسمت خرید اشتراک مراجعه کنید")
        update_data(f"UPDATE user SET self = 'inactive' WHERE id = '{user_id}' LIMIT 1")
        update_data(f"UPDATE user SET pid = NULL WHERE id = '{user_id}' LIMIT 1")

async def setscheduler(user_id):
    job = scheduler.get_job(str(user_id))
    if not job:
        scheduler.add_job(expirdec, "interval", hours=1, args=[user_id], id=str(user_id))

Main = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(text="🤔 سلف چیست؟", callback_data="WhatSelf", style="success")
        ],
        [
            InlineKeyboardButton(text="💲 بها", callback_data="Price", style="success"),
            InlineKeyboardButton(text="➕ افزایش موجودی", callback_data="BuyAmount", style="danger")
        ],
        [
            InlineKeyboardButton(text="🛒 خرید اشتراک", callback_data="BuySub", style="primary")
        ],
        [
            InlineKeyboardButton(text="🤖 سلف های من", callback_data="Subinfo", style="danger"),
            InlineKeyboardButton(text="👤 حساب کاربری", callback_data="MyAccount", style="success")
        ],
        [
            InlineKeyboardButton(text="👨‍💻 پشتیبانی", callback_data="Support", style="success")
        ]
    ]
)

@app.on_message(filters.private, group=-1)
async def update(c, m):
    user = get_data(f"SELECT * FROM user WHERE id = '{m.chat.id}' LIMIT 1")
    if user is None:
        update_data(f"INSERT INTO user(id) VALUES({m.chat.id})")

@app.on_message(filters.private&filters.command("start"))
@checker
async def update(c, m):
    bot_cfg = get_data("SELECT * FROM bot")
    welcome = bot_cfg["start_text"] if bot_cfg["start_text"] else f"**🫡 سلام {html.escape(m.chat.first_name)} عزیز\n\n• به ربات خرید , پشتیبانی و مدیریت ورتکس سلف خوش آمدید\n\n• این ربات جهت اتوماتیک بودن خرید , تمدید و مدیریت سلف شما کاربران عزیز طراحی شده است\n\n• جهت ادامه کار یکی از گزینه های زیر را انتخاب کنید :**"
    await app.send_message(m.chat.id, welcome, reply_markup=Main)
    update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
    async with lock:
        if m.chat.id in temp_Client:
            del temp_Client[m.chat.id]
    if os.path.isfile(f"sessions/{m.chat.id}.session") and not os.path.isfile(f"sessions/{m.chat.id}.session-journal"):
        os.remove(f"sessions/{m.chat.id}.session")

@app.on_callback_query()
@checker
async def call(c, call):
    global temp_Client
    bot_cfg = get_data("SELECT * FROM bot")
    user = get_data(f"SELECT * FROM user WHERE id = '{call.from_user.id}' LIMIT 1")
    phone_number = user["phone"]
    expir = user["expir"]
    amount = user["amount"]
    chat_id = call.from_user.id
    m_id = call.message.id
    data = call.data
    username = f"@{call.from_user.username}" if call.from_user.username else "وجود ندارد"

    if data == "MyAccount":
        await app.edit_message_text(chat_id, m_id, "**اطلاعات حساب کاربری شما در Tabchi Land به شرح زیر می باشد:**", reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="نام شما", callback_data="text", style="danger"),
                    InlineKeyboardButton(text=f"{call.from_user.first_name}", callback_data="text", style="success")
                ],
                [
                    InlineKeyboardButton(text="آیدی شما", callback_data="text", style="primary"),
                    InlineKeyboardButton(text=f"{call.from_user.id}", callback_data="text", style="primary")
                ],
                [
                    InlineKeyboardButton(text="یوزرنیم شما", callback_data="text", style="danger"),
                    InlineKeyboardButton(text=f"{username}", callback_data="text", style="primary")
                ],
                [
                    InlineKeyboardButton(text="موجودی شما", callback_data="text", style="danger"),
                    InlineKeyboardButton(text=f"{amount} تومان", callback_data="text", style="danger")
                ],
                [
                    InlineKeyboardButton(text="----------------", callback_data="text", style="success")
                ],
                [
                    InlineKeyboardButton(text=f"انقضای شما ({expir} ساعت)", callback_data="text", style="danger")
                ],
                [
                    InlineKeyboardButton(text="برگشت", callback_data="Back", style="success")
                ]
            ]
        ))
        update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")

    elif data == "BuySub" or data == "Back2":
        if user["phone"] is None:
            await app.delete_messages(chat_id, m_id)
            await app.send_message(chat_id, "**لطفا با استفاده از دکمه زیر شماره خود را به اشتراک بگذارید**", reply_markup=ReplyKeyboardMarkup(
                [
                    [
                        KeyboardButton(text="اشتراک گذاری شماره", request_contact=True, style="danger")
                    ]
                ], resize_keyboard=True
            ))
            update_data(f"UPDATE user SET step = 'contact' WHERE id = '{call.from_user.id}' LIMIT 1")
        else:
            if not os.path.isfile(f"sessions/{chat_id}.session-journal"):
                await app.edit_message_text(chat_id, m_id, "مدت زمان اشتراک را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(text=f"یک ماهه • {bot_cfg['p1']} تومان", callback_data=f"Login-720-{bot_cfg['p1']}", style="danger")
                        ],
                        [
                            InlineKeyboardButton(text=f"دو ماه • {bot_cfg['p2']} تومان", callback_data=f"Login-1440-{bot_cfg['p2']}", style="danger")
                        ],
                        [
                            InlineKeyboardButton(text=f"سه ماهه • {bot_cfg['p3']} تومان", callback_data=f"Login-2160-{bot_cfg['p3']}", style="primary")
                        ],
                        [
                            InlineKeyboardButton(text=f"چهار ماهه • {bot_cfg['p4']} تومان", callback_data=f"Login-2880-{bot_cfg['p4']}", style="primary")
                        ],
                        [
                            InlineKeyboardButton(text=f"پنج ماهه • {bot_cfg['p5']} تومان", callback_data=f"Login-3600-{bot_cfg['p5']}", style="success")
                        ],
                        [
                            InlineKeyboardButton(text="برگشت", callback_data="Back", style="success")
                        ]
                    ]
                ))
                update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")
                async with lock:
                    if chat_id in temp_Client:
                        del temp_Client[chat_id]
                if os.path.isfile(f"sessions/{chat_id}.session") and not os.path.isfile(f"sessions/{chat_id}.session-journal"):
                    os.remove(f"sessions/{chat_id}.session")
            else:
                await app.answer_callback_query(call.id, text="اشتراک سلف برای شما فعال است!", show_alert=True)

    elif data.split("-")[0] == "Login":
        expir_count = data.split("-")[1]
        cost = data.split("-")[2]
        if int(amount) >= int(cost):
            mess = await app.edit_message_text(chat_id, m_id, "در حال پردازش...")
            async with lock:
                if chat_id not in temp_Client:
                    temp_Client[chat_id] = {}
                temp_Client[chat_id]["client"] = Client(f"sessions/{chat_id}", api_id=API_ID, api_hash=API_HASH, device_model="Tabchi-Land", system_version="Linux")
                temp_Client[chat_id]["number"] = phone_number
                await temp_Client[chat_id]["client"].connect()
            try:
                await app.edit_message_text(chat_id, mess.id, "کد تایید 5 رقمی را با فرمت زیر ارسال کنید:\n1.2.3.4.5", reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(text="برگشت", callback_data="Back2", style="success")
                        ]
                    ]
                ))
                async with lock:
                    temp_Client[chat_id]["response"] = await temp_Client[chat_id]["client"].send_code(temp_Client[chat_id]["number"])
                update_data(f"UPDATE user SET step = 'login1-{expir_count}-{cost}' WHERE id = '{call.from_user.id}' LIMIT 1")

            except errors.BadRequest:
                await app.edit_message_text(chat_id, mess.id, "اتصال ناموفق بود! لطفا دوباره تلاش کنید", reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(text="برگشت", callback_data="Back2", style="success")
                        ]
                    ]
                ))
                update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")
                async with lock:
                    await temp_Client[chat_id]["client"].disconnect()
                    if chat_id in temp_Client:
                        del temp_Client[chat_id]
                if os.path.isfile(f"sessions/{chat_id}.session"):
                    os.remove(f"sessions/{chat_id}.session")

            except errors.PhoneNumberInvalid:
                await app.edit_message_text(chat_id, mess.id, "این شماره نامعتبر است!", reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(text="برگشت", callback_data="Back2", style="danger")
                        ]
                    ]
                ))
                update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")
                async with lock:
                    await temp_Client[chat_id]["client"].disconnect()
                    if chat_id in temp_Client:
                        del temp_Client[chat_id]
                if os.path.isfile(f"sessions/{chat_id}.session"):
                    os.remove(f"sessions/{chat_id}.session")

            except errors.PhoneNumberBanned:
                await app.edit_message_text(chat_id, mess.id, "این اکانت محدود است!", reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(text="برگشت", callback_data="Back2", style="danger")
                        ]
                    ]
                ))
                update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")
                async with lock:
                    await temp_Client[chat_id]["client"].disconnect()
                    if chat_id in temp_Client:
                        del temp_Client[chat_id]
                if os.path.isfile(f"sessions/{chat_id}.session"):
                    os.remove(f"sessions/{chat_id}.session")

            except Exception:
                async with lock:
                    await temp_Client[chat_id]["client"].disconnect()
                    if chat_id in temp_Client:
                        del temp_Client[chat_id]
                if os.path.isfile(f"sessions/{chat_id}.session"):
                    os.remove(f"sessions/{chat_id}.session")
        else:
            await app.edit_message_text(chat_id, m_id, "موجودی حساب شما برای خرید این اشتراک کافی نیست", reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="افزایش موجودی", callback_data="Wallet", style="danger")
                    ],
                    [
                        InlineKeyboardButton(text="برگشت", callback_data="Back2", style="success")
                    ]
                ]
            ))
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")

    elif data == "Price":
        await app.edit_message_text(chat_id, m_id, f"""**
⤸ بَهاء سلف عبارت است از : 

↤ 1 ماهه: `{bot_cfg['p1']}` هزار تومان
↤ 2 ماهه: `{bot_cfg['p2']}` هزار تومان
↤ 3 ماهه: `{bot_cfg['p3']}` هزار تومان
↤ 4 ماهه: `{bot_cfg['p4']}` هزار تومان
↤ 5 ماهه: `{bot_cfg['p5']}` هزار تومان
**""", reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="برگشت", callback_data="Back", style="danger")
                ]
            ]
        ))
        update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")

    elif data == "Wallet" or data == "Back3":
        await app.edit_message_text(chat_id, m_id, f"موجودی شما: {amount} تومان\nیکی از گزینه های زیر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="خرید موجودی", callback_data="BuyAmount", style="danger"),
                    InlineKeyboardButton(text="انتقال موجودی", callback_data="TransferAmount", style="success")
                ],
                [
                    InlineKeyboardButton(text="برگشت", callback_data="Back", style="success")
                ]
            ]
        ))
        update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")

    elif data == "BuyAmount":
        await app.edit_message_text(chat_id, m_id, "میزان موجودی مورد نظر خود را برای شارژ حساب وارد کنید:\nحداقل موجودی قابل خرید 10000 تومان است!", reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="برگشت", callback_data="Back3", style="primary")
                ]
            ]
        ))
        update_data(f"UPDATE user SET step = 'buyamount1' WHERE id = '{call.from_user.id}' LIMIT 1")

    elif data.split("-")[0] == "AcceptAmount":
        if not check_is_admin(chat_id): return
        user_id = int(data.split("-")[1])
        count = int(data.split("-")[2])
        user_amount = get_data(f"SELECT amount FROM user WHERE id = '{user_id}' LIMIT 1")
        user_upamount = int(user_amount["amount"]) + int(count)
        update_data(f"UPDATE user SET amount = '{user_upamount}' WHERE id = '{user_id}' LIMIT 1")
        await app.edit_message_text(chat_id, m_id, f"تایید انجام شد\nمبلغ {count} تومان به حساب کاربر [ {user_id} ] انتقال یافت\nموجودی جدید کاربر: {user_upamount} تومان")
        await app.send_message(user_id, f"شد🎉 پرداخت شما تایید شد!\nمقدار {count} تومان به حسابت اضافه شد.")

    elif data.split("-")[0] == "RejectAmount":
        if not check_is_admin(chat_id): return
        user_id = int(data.split("-")[1])
        await app.edit_message_text(chat_id, m_id, "درخواست کاربر مورد نظر برای افزایش موجودی رد شد")
        await app.send_message(user_id, "درخواست شما برای افزایش موجودی رد شد")

    elif data == "TransferAmount":
        await app.edit_message_text(chat_id, m_id, "آیدی عددی کاربری که قصد انتقال موجودی به او را دارید ارسال کنید:", reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="برگشت", callback_data="Back3", style="success")
                ]
            ]
        ))
        update_data(f"UPDATE user SET step = 'transferam1' WHERE id = '{call.from_user.id}' LIMIT 1")

    elif data.split("-")[0] == "AcceptExpir":
        if not check_is_admin(chat_id): return
        user_id = int(data.split("-")[1])
        count = int(data.split("-")[2])
        user_expir = get_data(f"SELECT expir FROM user WHERE id = '{user_id}' LIMIT 1")
        user_upexpir = int(user_expir["expir"]) + int(count)
        update_data(f"UPDATE user SET expir = '{user_upexpir}' WHERE id = '{user_id}' LIMIT 1")
        await app.edit_message_text(chat_id, m_id, f"تایید انجام شد\n{count} ساعت به انقضای کاربر [ {user_id} ] افزوده شد\nانقضای جدید کاربر: {user_upexpir} ساعت")
        await app.send_message(user_id, f"درخواست شما برای افزایش انقضا تایید شد\n{count} ساعت به انقضای شما افزوده شد\nانقضای جدید شما: {user_upexpir} ساعت")

    elif data.split("-")[0] == "RejectExpir":
        if not check_is_admin(chat_id): return
        user_id = int(data.split("-")[1])
        await app.edit_message_text(chat_id, m_id, "درخواست کاربر مورد نظر برای افزایش انقضا رد شد")
        await app.send_message(user_id, "درخواست شما برای افزایش انقضا رد شد")

    elif data == "Subinfo" or data == "Back4":
        if os.path.isfile(f"sessions/{chat_id}.session-journal"):
            substatus = "فعال" if user["self"] == "active" else "غیرفعال"
            await app.edit_message_text(chat_id, m_id, f"وضعیت اشتراک: {substatus}\nشماره اکانت: {phone_number}\nانقضا: {expir} ساعت", reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="خرید انقضا", callback_data="BuyExpir", style="primary"),
                        InlineKeyboardButton(text="انتقال انقضا", callback_data="TransferExpir", style="danger")
                    ],
                    [
                        InlineKeyboardButton(text="برگشت", callback_data="Back", style="success")
                    ]
                ]
            ))
        else:
            await app.answer_callback_query(call.id, text="شما اشتراک فعالی ندارید!", show_alert=True)

    elif data == "BuyExpir":
        await app.edit_message_text(chat_id, m_id, "میزان انقضای مورد نظر خود را برای افزایش وارد کنید (ساعت):\nهزینه هر 24 ساعت انقضا 1000 تومان است", reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="برگشت", callback_data="Back4", style="danger")
                ]
            ]
        ))
        update_data(f"UPDATE user SET step = 'buyexpir1' WHERE id = '{call.from_user.id}' LIMIT 1")

    elif data == "TransferExpir":
        await app.edit_message_text(chat_id, m_id, "آیدی عددی کاربری که قصد انتقال انقضا به او را دارید ارسال کنید:", reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="برگشت", callback_data="Back4", style="primary")
                ]
            ]
        ))
        update_data(f"UPDATE user SET step = 'transferex1' WHERE id = '{call.from_user.id}' LIMIT 1")

    elif data == "WhatSelf":
        guide_txt = bot_cfg["help_text"] if bot_cfg["help_text"] else """**\n🔴 سلف چیست؟\n\nسلف یک اکانت هوشمند تلگرام است که برای ارسال خودکار پیام، تبلیغات هدفمند و مدیریت هم‌زمان چندین گروه و پیوی استفاده می‌شود.\n\nاین سیستم با شبیه‌سازی رفتار یک کاربر واقعی، پیام‌ها را به‌صورت زمان‌بندی‌شده و کنترل‌شده ارسال می‌کند تا از فلود، فریز و بن شدن جلوگیری شود.\n\nسلف معمولاً برای:\n• تبلیغات گسترده و هوشمند  \n• ارسال پیام به گروه‌ها و پیوی‌ها  \n• مدیریت کمپین‌های تلگرامی  \n• افزایش بازدهی با حداقل ریسک  \n\nمورد استفاده قرار می‌گیرد.\n\n⚠️ توجه: استفاده نادرست از سلف (سرعت بالا، پیام تکراری، اکانت خام) می‌تواند باعث محدودیت یا مسدود شدن اکانت شود. به همین دلیل رعایت تنظیمات اصولی و نکات ایمنی الزامی است.\n\nاگر حرفه‌ای تنظیم شود، سلف یک ابزار قدرتمند است؛  \nاگر اشتباه استفاده شود، سریع حذف می‌شود.\n**"""
        await app.edit_message_text(chat_id, m_id, guide_txt, reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="برگشت", callback_data="Back", style="primary")
                ]
            ]
        ))
        update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")

    elif data == "Support":
        await app.edit_message_text(chat_id, m_id, "پیام خود را ارسال کنید:", reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="برگشت", callback_data="Back", style="primary")
                ]
            ]
        ))
        update_data(f"UPDATE user SET step = 'support' WHERE id = '{call.from_user.id}' LIMIT 1")

    elif data.split("-")[0] == "Reply":
        if not check_is_admin(chat_id): return
        exit = data.split("-")[1]
        getuser = await app.get_users(exit)
        await app.send_message(chat_id, f"پیام خود را برای کاربر [ {html.escape(getuser.first_name)} ] ارسال کنید:", reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="صفحه اصلی", callback_data="Back", style="primary"),
                    InlineKeyboardButton(text="پنل مدیریت", callback_data="Panel", style="primary")
                ]
            ]
        ))
        update_data(f"UPDATE user SET step = 'ureply-{exit}' WHERE id = '{chat_id}' LIMIT 1")

    elif data.split("-")[0] == "Block":
        if not check_is_admin(chat_id): return
        exit = data.split("-")[1]
        getuser = await app.get_users(exit)
        block = get_data(f"SELECT * FROM block WHERE id = '{exit}' LIMIT 1")
        if block is None:
            await app.send_message(exit, "کاربر محترم شما به دلیل نقض قوانین از ربات مسدود شدید")
            await app.send_message(chat_id, f"کاربر [ {html.escape(getuser.first_name)} ] از ربات بلاک شد")
            update_data(f"INSERT INTO block(id) VALUES({exit})")
        else:
            await app.send_message(chat_id, f"کاربر [ {html.escape(getuser.first_name)} ] از قبل بلاک است")

    elif data == "Back":
        bot_cfg = get_data("SELECT * FROM bot")
        welcome = bot_cfg["start_text"] if bot_cfg["start_text"] else f"**🫡 سلام {html.escape(call.from_user.first_name)} عزیز\n\n• به ربات خرید , پشتیبانی و مدیریت ورتکس سلف خوش آمدید\n\n• این ربات جهت اتوماتیک بودن خرید , تمدید و مدیریت سلف شما کاربران عزیز طراحی شده است\n\n• جهت ادامه کار یکی از گزینه های زیر را انتخاب کنید :**"
        try:
            await app.edit_message_text(
                chat_id,
                m_id,
                welcome,
                reply_markup=Main
            )
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")
            async with lock:
                if chat_id in temp_Client:
                    del temp_Client[chat_id]
        except errors.MessageNotModified:
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")
            async with lock:
                if chat_id in temp_Client:
                    del temp_Client[chat_id]
            await app.answer_callback_query(call.id, text="به منوی اصلی بازگشتید!", show_alert=True)
        except Exception as e:
            await app.answer_callback_query(call.id, text="خطایی رخ داد! لطفاً دوباره تلاش کنید.", show_alert=True)

    elif data == "text":
        await app.answer_callback_query(call.id, text="این دکمه نمایشی است", show_alert=True)

    # دکمه‌های مربوط به بخش پنل ادمین
    elif data.split("-")[0] == "DeleteSub":
        if not check_is_admin(chat_id): return
        user_id = int(data.split("-")[1])
        await app.edit_message_text(chat_id, m_id, "**هشدار! با این کار اشتراک کاربر مورد نظر به طور کامل حذف می شود و امکان فعالسازی دوباره از پنل مدیریت وجود ندارد\n\nاگر از این کار اطمینان دارید روی گزینه تایید و در غیر این صورت روی گزینه برگشت کلیک کنید**", reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="تایید", callback_data=f"AcceptDelSub-{user_id}", style="primary")
                ],
                [
                    InlineKeyboardButton(text="برگشت", callback_data="AdminBack", style="primary")
                ]
            ]
        ))
    
    elif data.split("-")[0] == "AcceptDelSub":
        if not check_is_admin(chat_id): return
        user_id = int(data.split("-")[1])
        await app.edit_message_text(chat_id, m_id, "اشتراک سلف کاربر مورد نظر به طور کامل حذف شد", reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="برگشت", callback_data="AdminBack", style="danger")
                ]
            ]
        ))
        if os.path.isdir(f"selfs/self-{user_id}"):
            shutil.rmtree(f"selfs/self-{user_id}")
        if os.path.isfile(f"sessions/{user_id}.session"):
            try:
                async with Client(f"sessions/{user_id}") as user_client:
                    await user_client.log_out()
            except: pass
            if os.path.isfile(f"sessions/{user_id}.session"):
                os.remove(f"sessions/{user_id}.session")
        if os.path.isfile(f"sessions/{user_id}.session-journal"):
            os.remove(f"sessions/{user_id}.session-journal")
        update_data(f"UPDATE user SET expir = '0' WHERE id = '{user_id}' LIMIT 1")
        update_data(f"UPDATE user SET self = 'inactive' WHERE id = '{user_id}' LIMIT 1")
        update_data(f"UPDATE user SET pid = NULL WHERE id = '{user_id}' LIMIT 1")
        await app.send_message(user_id, "کاربر گرامی اشتراک سلف شما توسط مدیر حذف شد\nبرای کسب اطلاعات بیشتر و دلیل حذف اشتراک به پشتیبانی مراجعه کنید")
    
    elif data == "AdminBack":
        if not check_is_admin(chat_id): return
        await app.delete_messages(chat_id, m_id)
        await app.send_message(chat_id, "مدیر گرامی به پنل مدیریت Tabchi Land خوش آمدید!", reply_markup=Panel)
        update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

@app.on_message(filters.contact)
@checker
async def update(c, m):
    user = get_data(f"SELECT * FROM user WHERE id = '{m.chat.id}' LIMIT 1")
    if user["step"] == "contact":
        phone_number = str(m.contact.phone_number)
        if not phone_number.startswith("+"):
            phone_number = f"+{phone_number}"
        contact_id = m.contact.user_id
        if m.contact and m.chat.id == contact_id:
            mess = await app.send_message(m.chat.id, "شماره شما تایید شد", reply_markup=ReplyKeyboardRemove())
            update_data(f"UPDATE user SET phone = '{phone_number}' WHERE id = '{m.chat.id}' LIMIT 1")
            await asyncio.sleep(1)
            await app.delete_messages(m.chat.id, mess.id)
            await app.send_message(m.chat.id, f"""**🫡 سلام {html.escape(m.chat.first_name)} عزیز

• به ربات خرید , پشتیبانی و مدیریت ورتکس سلف خوش آمدید

• این ربات جهت اتوماتیک بودن خرید , تمدید و مدیریت سلف شما کاربران عزیز طراحی شده است

• جهت ادامه کار یکی از گزینه های زیر را انتخاب کنید :**""", reply_markup=Main)
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
        else:
            await app.send_message(m.chat.id, "لطفا از دکمه اشتراک گذاری شماره استفاده کنید!")

@app.on_message(filters.private)
@checker
async def update(c, m):
    global temp_Client
    user = get_data(f"SELECT * FROM user WHERE id = '{m.chat.id}' LIMIT 1")
    bot_cfg = get_data("SELECT * FROM bot")
    username = f"@{m.from_user.username}" if m.from_user.username else "وجود ندارد"
    phone_number = user["phone"]
    expir = user["expir"]
    amount = user["amount"]
    chat_id = m.chat.id
    text = m.text
    m_id = m.id

    if user["step"].split("-")[0] == "login1":
        if re.match(r'^\d\.\d\.\d\.\d\.\d$', text):
            code = ''.join(re.findall(r'\d', text))
            expir_count = user["step"].split("-")[1]
            cost = user["step"].split("-")[2]
            mess = await app.send_message(chat_id, "در حال پردازش...")
            try:
                async with lock:
                    await temp_Client[chat_id]["client"].sign_in(temp_Client[chat_id]["number"], temp_Client[chat_id]["response"].phone_code_hash, code)
                    await temp_Client[chat_id]["client"].disconnect()
                    if chat_id in temp_Client:
                        del temp_Client[chat_id]
                mess = await app.edit_message_text(chat_id, mess.id, "لاگین با موفقیت انجام شد")
                mess = await app.edit_message_text(chat_id, mess.id, "در حال فعالسازی سلف...\n(ممکن است چند لحظه طول بکشد)")
                if not os.path.isdir(f"selfs/self-{m.chat.id}"):
                    os.mkdir(f"selfs/self-{m.chat.id}")
                    with zipfile.ZipFile("source/Self.zip", "r") as extract:
                        extract.extractall(f"selfs/self-{m.chat.id}")
                
                process = subprocess.Popen(
                    ["python3", "self.py", str(m.chat.id), str(API_ID), API_HASH, Helper_ID],
                    cwd=f"selfs/self-{m.chat.id}",
                    preexec_fn=os.setsid
                )
                
                await asyncio.sleep(10)
                if process.poll() is None:
                    await app.edit_message_text(chat_id, mess.id, f"سلف با موفقیت برای اکانت شما فعال شد\nمدت زمان اشتراک: {expir_count} ساعت", reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(text="برگشت", callback_data="Back", style="danger")
                            ]
                        ]
                    ))
                    upamount = int(amount) - int(cost)
                    update_data(f"UPDATE user SET amount = '{upamount}' WHERE id = '{m.chat.id}' LIMIT 1")
                    update_data(f"UPDATE user SET expir = '{expir_count}' WHERE id = '{m.chat.id}' LIMIT 1")
                    update_data(f"UPDATE user SET self = 'active' WHERE id = '{m.chat.id}' LIMIT 1")
                    update_data(f"UPDATE user SET pid = '{process.pid}' WHERE id = '{m.chat.id}' LIMIT 1")
                    update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
                    add_admin(m.chat.id)
                    await setscheduler(m.chat.id)
                    await app.send_message(Admin, f"#گزارش_خرید_اشتراک\n\nآیدی کاربر: `{m.chat.id}`\nشماره کاربر: {phone_number}\nقیمت اشتراک: {cost} تومان\nمدت زمان اشتراک: {expir_count} ساعت")
                else:
                    await app.edit_message_text(chat_id, mess.id, "در فعالسازی سلف برای اکانت شما مشکلی رخ داد! هیچ مبلغی از حساب شما کسر نشد\nلطفا دوباره امتحان کنید و در صورتی که مشکل ادامه داشت با پشتیبانی تماس بگیرید", reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(text="برگشت", callback_data="Back", style="danger")
                            ]
                        ]
                    ))
                    update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
                    if os.path.isfile(f"sessions/{chat_id}.session"):
                        os.remove(f"sessions/{chat_id}.session")
            except errors.SessionPasswordNeeded:
                await app.edit_message_text(chat_id, mess.id, "رمز تایید دو مرحله ای برای اکانت شما فعال است\nرمز را وارد کنید:", reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(text="برگشت", callback_data="Back2", style="success")
                        ]
                    ]
                ))
                update_data(f"UPDATE user SET step = 'login2-{expir_count}-{cost}' WHERE id = '{m.chat.id}' LIMIT 1")
            except errors.BadRequest:
                await app.edit_message_text(chat_id, mess.id, "کد نامعتبر است!")
            except errors.PhoneCodeInvalid:
                await app.edit_message_text(chat_id, mess.id, "کد نامعتبر است!")
            except errors.PhoneCodeExpired:
                await app.edit_message_text(chat_id, mess.id, "کد منقضی شده است! لطفا عملیات ورود را دوباره تکرار کنید", reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(text="برگشت", callback_data="Back2", style="danger")
                        ]
                    ]
                ))
                update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
                async with lock:
                    await temp_Client[chat_id]["client"].disconnect()
                    if chat_id in temp_Client:
                        del temp_Client[chat_id]
                if os.path.isfile(f"sessions/{chat_id}.session"):
                    os.remove(f"sessions/{chat_id}.session")
            except Exception:
                async with lock:
                    await temp_Client[chat_id]["client"].disconnect()
                    if chat_id in temp_Client:
                        del temp_Client[chat_id]
                if os.path.isfile(f"sessions/{chat_id}.session"):
                    os.remove(f"sessions/{chat_id}.session")
        else:
            await app.send_message(chat_id, "فرمت نامعتبر است! لطفا کد را با فرمت ذکر شده وارد کنید:")

    elif user["step"].split("-")[0] == "login2":
        password = text.strip()
        expir_count = user["step"].split("-")[1]
        cost = user["step"].split("-")[2]
        mess = await app.send_message(chat_id, "در حال پردازش...")
        try:
            async with lock:
                await temp_Client[chat_id]["client"].check_password(password)
                await temp_Client[chat_id]["client"].disconnect()
                if chat_id in temp_Client:
                    del temp_Client[chat_id]
            mess = await app.edit_message_text(chat_id, mess.id, "لاگین با موفقیت انجام شد")
            mess = await app.edit_message_text(chat_id, mess.id, "در حال فعالسازی سلف...\n(ممکن است چند لحظه طول بکشد)")
            if not os.path.isdir(f"selfs/self-{m.chat.id}"):
                os.mkdir(f"selfs/self-{m.chat.id}")
                with zipfile.ZipFile("source/Self.zip", "r") as extract:
                    extract.extractall(f"selfs/self-{m.chat.id}")
            
            process = subprocess.Popen(
                ["python3", "self.py", str(m.chat.id), str(API_ID), API_HASH, Helper_ID],
                cwd=f"selfs/self-{m.chat.id}",
                preexec_fn=os.setsid
            )
            
            await asyncio.sleep(10)
            if process.poll() is None:
                await app.edit_message_text(chat_id, mess.id, f"سلف با موفقیت برای اکانت شما فعال شد\nمدت زمان اشتراک: {expir_count} ساعت", reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(text="برگشت", callback_data="Back", style="danger")
                        ]
                    ]
                ))
                upamount = int(amount) - int(cost)
                update_data(f"UPDATE user SET amount = '{upamount}' WHERE id = '{m.chat.id}' LIMIT 1")
                update_data(f"UPDATE user SET expir = '{expir_count}' WHERE id = '{m.chat.id}' LIMIT 1")
                update_data(f"UPDATE user SET self = 'active' WHERE id = '{m.chat.id}' LIMIT 1")
                update_data(f"UPDATE user SET pid = '{process.pid}' WHERE id = '{m.chat.id}' LIMIT 1")
                update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
                add_admin(m.chat.id)
                await setscheduler(m.chat.id)
                await app.send_message(Admin, f"#گزارش_خرید_اشتراک\n\nآیدی کاربر: `{m.chat.id}`\nشماره کاربر: {phone_number}\nقیمت اشتراک: {cost} تومان\nمدت زمان اشتراک: {expir_count} ساعت")
            else:
                await app.edit_message_text(chat_id, mess.id, "در فعالسازی سلف برای اکانت شما مشکلی رخ داد! هیچ مبلغی از حساب شما کسر نشد\nلطفا دوباره امتحان کنید و در صورتی که مشکل ادامه داشت با پشتیبانی تماس بگیرید", reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(text="برگشت", callback_data="Back", style="danger")
                        ]
                    ]
                ))
                update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
                if os.path.isfile(f"sessions/{chat_id}.session"):
                    os.remove(f"sessions/{chat_id}.session")
        except errors.BadRequest:
            await app.edit_message_text(chat_id, mess.id, "رمز نادرست است!\nرمز را وارد کنید:", reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="برگشت", callback_data="Back2", style="primary")
                    ]
                ]
            ))
        except Exception:
            async with lock:
                await temp_Client[chat_id]["client"].disconnect()
                if chat_id in temp_Client:
                    del temp_Client[chat_id]
            if os.path.isfile(f"sessions/{chat_id}.session"):
                os.remove(f"sessions/{chat_id}.session")

    elif user["step"] == "buyamount1":
        if text.isdigit():
            count = text.strip()
            if int(count) >= 10000:
                await app.send_message(chat_id, f"فاکتور افزایش موجودی به مبلغ {count} تومان ایجاد شد\n\nشماره کارت: `{bot_cfg['card_number']}`\nبه نام {bot_cfg['card_name']}\nمبلغ قابل پرداخت: {count} تومان\n\nبعد از پرداخت رسید تراکنش را در همین قسمت ارسال کنید", reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(text="برگشت", callback_data="Back3", style="danger")
                        ]
                    ]
                ))
                update_data(f"UPDATE user SET step = 'buyamount2-{count}' WHERE id = '{m.chat.id}' LIMIT 1")
            else:
                await app.send_message(chat_id, "حداقل موجودی قابل خرید 10000 تومان است!")
        else:
            await app.send_message(chat_id, "ورودی نامعتبر! فقط ارسال عدد مجاز است")

    elif user["step"].split("-")[0] == "buyamount2":
        if m.photo:
            count = int(user["step"].split("-")[1])
            mess = await app.forward_messages(from_chat_id=chat_id, chat_id=Admin, message_ids=m_id)
            await app.send_message(Admin, f"""
مدیر گرامی درخواست افزایش موجودی جدید دارید

نام کاربر: {html.escape(m.chat.first_name)}
آیدی کاربر: `{m.chat.id}`
یوزرنیم کاربر: {username}
مبلغ درخواستی کاربر: {count} تومان
""", reply_to_message_id=mess.id, reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("تایید", callback_data=f"AcceptAmount-{chat_id}-{count}", style="danger"),
                        InlineKeyboardButton("رد کردن", callback_data=f"RejectAmount-{chat_id}", style="success")
                    ]
                ]
            ))
            await app.send_message(chat_id, "✅ فیش دریافت شد. پس از بررسی نتیجه اعلام می‌شود.", reply_to_message_id=m_id)
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
        else:
            await app.send_message(chat_id, "ورودی نامعتبر! فقط ارسال عکس مجاز است")

    elif user["step"] == "transferam1":
        if text.isdigit():
            user_id = int(text.strip())
            if get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1") is not None:
                if user_id != m.chat.id:
                    await app.send_message(chat_id, "میزان موجودی مورد نظر خود را برای انتقال وارد کنید:\nحداقل موجودی قابل ارسال 10000 تومان است")
                    update_data(f"UPDATE user SET step = 'transferam2-{user_id}' WHERE id = '{m.chat.id}' LIMIT 1")
                else:
                    await app.send_message(chat_id, "شما نمی توانید به خودتان موجودی انتقال دهید!")
            else:
                await app.send_message(chat_id, "چنین کاربری در ربات یافت نشد!")
        else:
            await app.send_message(chat_id, "ورودی نامعتبر! فقط ارسال عدد مجاز است")

    elif user["step"].split("-")[0] == "transferam2":
        if text.isdigit():
            user_id = int(user["step"].split("-")[1])
            count = text.strip()
            if int(amount) >= int(count):
                if int(count) >= 10000:
                    user_amount = get_data(f"SELECT amount FROM user WHERE id = '{user_id}' LIMIT 1")
                    upamount = int(amount) - int(count)
                    user_upamount = int(user_amount["amount"]) + int(count)
                    update_data(f"UPDATE user SET amount = '{upamount}' WHERE id = '{m.chat.id}' LIMIT 1")
                    update_data(f"UPDATE user SET amount = '{user_upamount}' WHERE id = '{user_id}' LIMIT 1")
                    await app.send_message(chat_id, f"مبلغ {count} تومان از حساب شما کسر شد و به حساب کاربر [ {user_id} ] انتقال یافت\nموجودی جدید شما: {upamount} تومان", reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(text="برگشت", callback_data="Back3", style="success")
                            ]
                        ]
                    ))
                    await app.send_message(user_id, f"مبلغ {count} تومان از حساب کاربر [ {m.chat.id} ] به حساب شما انتقال یافت\nموجودی جدید شما: {user_upamount} تومان")
                    update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
                else:
                    await app.send_message(chat_id, "حداقل موجودی قابل ارسال 10000 تومان است!")
            else:
                await app.send_message(chat_id, "موجودی شما کافی نیست!")
        else:
            await app.send_message(chat_id, "ورودی نامعتبر! فقط ارسال عدد مجاز است")

    elif user["step"] == "buyexpir1":
        if text.isdigit():
            count = int(text.strip())
            if int(count) > 0:
                cost_per_day = 1000
                total_cost = (count // 24) * cost_per_day if count >= 24 else cost_per_day
                await app.send_message(chat_id, f"فاکتور افزایش انقضا به مدت {count} ساعت ایجاد شد\n\nشماره کارت: `{bot_cfg['card_number']}`\nبه نام {bot_cfg['card_name']}\nمبلغ قابل پرداخت: {total_cost} تومان\n\nبعد از پرداخت رسید تراکنش را در همین قسمت ارسال کنید", reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(text="برگشت", callback_data="Back4", style="danger")
                        ]
                    ]
                ))
                update_data(f"UPDATE user SET step = 'buyexpir2-{count}' WHERE id = '{m.chat.id}' LIMIT 1")
            else:
                await app.send_message(chat_id, "حداقل انقضای قابل خرید 1 ساعت است!")
        else:
            await app.send_message(chat_id, "ورودی نامعتبر! فقط ارسال عدد مجاز است")

    elif user["step"].split("-")[0] == "buyexpir2":
        if m.photo:
            count = int(user["step"].split("-")[1])
            mess = await app.forward_messages(from_chat_id=chat_id, chat_id=Admin, message_ids=m_id)
            await app.send_message(Admin, f"""
مدیر گرامی درخواست افزایش انقضای جدید دارید

نام کاربر: {html.escape(m.chat.first_name)}
آیدی کاربر: `{m.chat.id}`
یوزرنیم کاربر: {username}
تعداد ساعت های درخواستی کاربر: {count} ساعت
""", reply_to_message_id=mess.id, reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("تایید", callback_data=f"AcceptExpir-{chat_id}-{count}", style="primary"),
                        InlineKeyboardButton("رد کردن", callback_data=f"RejectExpir-{chat_id}", style="primary")
                    ]
                ]
            ))
            await app.send_message(chat_id, "رسید تراکنش شما ارسال شد. لطفا منتظر تایید توسط مدیر باشید", reply_to_message_id=m_id)
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
        else:
            await app.send_message(chat_id, "ورودی نامعتبر! فقط ارسال عکس مجاز است")

    elif user["step"] == "transferex1":
        if text.isdigit():
            user_id = int(text.strip())
            if get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1") is not None:
                if user_id != m.chat.id:
                    if os.path.isfile(f"sessions/{user_id}.session-journal"):
                        await app.send_message(chat_id, "میزان انقضای مورد نظر خود را برای انتقال وارد کنید (ساعت):\nحداقل باید 10 ساعت انقضا برای شما باقی بماند!")
                        update_data(f"UPDATE user SET step = 'transferex2-{user_id}' WHERE id = '{m.chat.id}' LIMIT 1")
                    else:
                        await app.send_message(chat_id, "اشتراک سلف برای این کاربر فعال نیست!")
                else:
                    await app.send_message(chat_id, "شما نمی توانید به خودتان انقضا انتقال دهید!")
            else:
                await app.send_message(chat_id, "چنین کاربری در ربات یافت نشد!")
        else:
            await app.send_message(chat_id, "ورودی نامعتبر! فقط ارسال عدد مجاز است")

    elif user["step"].split("-")[0] == "transferex2":
        if text.isdigit():
            user_id = int(user["step"].split("-")[1])
            count = text.strip()
            user_hours = expir
            if int(user_hours) >= int(count):
                if int(user_hours) - int(count) >= 10:
                    user_expir = get_data(f"SELECT expir FROM user WHERE id = '{user_id}' LIMIT 1")
                    user_expir_hours = int(user_expir["expir"])
                    
                    sender_new_hours = user_hours - int(count)
                    update_data(f"UPDATE user SET expir = '{sender_new_hours}' WHERE id = '{m.chat.id}' LIMIT 1")
                    
                    receiver_new_hours = user_expir_hours + int(count)
                    update_data(f"UPDATE user SET expir = '{receiver_new_hours}' WHERE id = '{user_id}' LIMIT 1")
                    
                    sender_user = await app.get_users(m.chat.id)
                    receiver_user = await app.get_users(user_id)
                    
                    sender_name = html.escape(sender_user.first_name) if sender_user.first_name else "کاربر"
                    receiver_name = html.escape(receiver_user.first_name) if receiver_user.first_name else "کاربر"
                    
                    receiver_msg = await app.send_message(user_id, f"""👤 کاربر {receiver_name} عزیز

**✅ از سمت [{sender_name}](tg://user?id={m.chat.id}) مقدار {count} ساعت انقضا برای شما ارسال شد**

**⏰ انقضای جدید شما: {receiver_new_hours} ساعت**""", 
                        reply_to_message_id=m.reply_to_message_id if m.reply_to_message_id else None,
                        disable_web_page_preview=True
                    )
                    
                    await app.send_message(chat_id, f"{count} ساعت از انقضای شما کسر شد و به کاربر [{receiver_name}](tg://user?id={user_id}) انتقال یافت\nانقضای جدید شما: {sender_new_hours} ساعت", 
                        reply_markup=InlineKeyboardMarkup(
                            [
                                [
                                    InlineKeyboardButton(text="برگشت", callback_data="Back4", style="success")
                                ]
                            ]
                        ),
                        disable_web_page_preview=True
                    )
                    
                    update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
                else:
                    await app.send_message(chat_id, "حداقل باید 10 ساعت انقضا برای شما باقی بماند!")
            else:
                await app.send_message(chat_id, "انقضای شما کافی نیست!")
        else:
            await app.send_message(chat_id, "ورودی نامعتبر! فقط ارسال عدد مجاز است")

    elif user["step"] == "support":
        mess = await app.forward_messages(from_chat_id=chat_id, chat_id=Admin, message_ids=m_id)
        await app.send_message(Admin, f"""
مدیر گرامی پیام ارسال شده جدید دارید

نام کاربر: {html.escape(m.chat.first_name)}
آیدی کاربر: `{m.chat.id}`
یوزرنیم کاربر: {username}
""", reply_to_message_id=mess.id, reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("پاسخ", callback_data=f"Reply-{chat_id}", style="primary"),
                    InlineKeyboardButton("بلاک", callback_data=f"Block-{chat_id}", style="danger")
                ]
            ]
        ))
        await app.send_message(chat_id, "پیام شما ارسال شد و در اسرع وقت به آن پاسخ داده خواهد شد", reply_to_message_id=m_id)

    elif user["step"].split("-")[0] == "ureply":
        if not check_is_admin(chat_id): return
        exit = user["step"].split("-")[1]
        mess = await app.copy_message(from_chat_id=chat_id, chat_id=int(exit), message_id=m_id)
        await app.send_message(exit, "کاربر گرامی پیام ارسال شده جدید از پشتیبانی دارید", reply_to_message_id=mess.id)
        await app.send_message(chat_id, "پیام شما ارسال شد پیام دیگری ارسال یا روی یکی از گزینه های زیر کلیک کنید:", reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="صفحه اصلی", callback_data="Back", style="danger"),
                    InlineKeyboardButton(text="پنل مدیریت", callback_data="Panel", style="primary")
                ]
            ]
        ))

    elif text and (text.startswith("انتقال انقضا") or text.startswith("انتقال ساعت")):
        try:
            parts = text.split()
            if len(parts) >= 3:
                hours = int(parts[2])
                receiver = None
                
                if len(parts) >= 4:
                    username_input = parts[3].replace("@", "")
                    try:
                        receiver_user = await app.get_users(username_input)
                        receiver = receiver_user.id
                    except:
                        pass
                
                if not receiver and len(parts) >= 4 and parts[3].isdigit():
                    receiver = int(parts[3])
                
                if not receiver and m.reply_to_message:
                    receiver = m.reply_to_message.from_user.id
                
                if receiver:
                    user_hours = expir
                    if user_hours >= hours:
                        if user_hours - hours >= 10:
                            user_expir = get_data(f"SELECT expir FROM user WHERE id = '{receiver}' LIMIT 1")
                            if user_expir:
                                user_expir_hours = int(user_expir["expir"])
                                
                                sender_new_hours = user_hours - hours
                                update_data(f"UPDATE user SET expir = '{sender_new_hours}' WHERE id = '{m.chat.id}' LIMIT 1")
                                
                                receiver_new_hours = user_expir_hours + hours
                                update_data(f"UPDATE user SET expir = '{receiver_new_hours}' WHERE id = '{receiver}' LIMIT 1")
                                
                                sender_user = await app.get_users(m.chat.id)
                                receiver_user = await app.get_users(receiver)
                                
                                sender_name = html.escape(sender_user.first_name) if sender_user.first_name else "کاربر"
                                receiver_name = html.escape(receiver_user.first_name) if receiver_user.first_name else "کاربر"
                                
                                receiver_msg = await app.send_message(receiver, f"""👤 کاربر {receiver_name} عزیز

**✅ از سمت [{sender_name}](tg://user?id={m.chat.id}) مقدار {hours} ساعت انقضا برای شما ارسال شد**

**⏰ انقضای جدید شما: {receiver_new_hours} ساعت**""", 
                                    reply_to_message_id=m.reply_to_message_id if m.reply_to_message_id else None,
                                    disable_web_page_preview=True
                                )
                                
                                await app.send_message(chat_id, f"{hours} ساعت از انقضای شما کسر شد و به کاربر [{receiver_name}](tg://user?id={receiver}) انتقال یافت\nانقضای جدید شما: {sender_new_hours} ساعت", 
                                    disable_web_page_preview=True
                                )
                            else:
                                await app.send_message(chat_id, "کاربر گیرنده در ربات یافت نشد!")
                        else:
                            await app.send_message(chat_id, "حداقل باید 10 ساعت انقضا برای شما باقی بماند!")
                    else:
                        await app.send_message(chat_id, "انقضای شما کافی نیست!")
                else:
                    await app.send_message(chat_id, "لطفاً کاربر گیرنده را مشخص کنید:\n- با یوزرنیم: @username\n- با آیدی عددی: 123456789\n- با ریپلای روی پیام کاربر")
            else:
                await app.send_message(chat_id, "فرمت صحیح:\n`انتقال انقضا [مقدار ساعت] [یوزرنیم/آیدی/ریپلای]`")
        except ValueError:
            await app.send_message(chat_id, "مقدار ساعت باید عدد باشد!")
        except Exception as e:
            await app.send_message(chat_id, f"خطا: {str(e)}")

    elif check_is_admin(chat_id) and text and (text.startswith("افزایش") or text.startswith("کسر")):
        try:
            parts = text.split()
            if len(parts) >= 3:
                action = parts[0]
                hours = int(parts[1])
                target = None
                
                if len(parts) >= 3:
                    username_input = parts[2].replace("@", "")
                    try:
                        target_user = await app.get_users(username_input)
                        target = target_user.id
                    except:
                        pass
                
                if not target and len(parts) >= 3 and parts[2].isdigit():
                    target = int(parts[2])
                
                if not target and m.reply_to_message:
                    target = m.reply_to_message.from_user.id
                
                if target:
                    user_expir = get_data(f"SELECT expir FROM user WHERE id = '{target}' LIMIT 1")
                    if user_expir:
                        user_hours = int(user_expir["expir"])
                        
                        if action == "افزایش":
                            new_hours = user_hours + hours
                            update_data(f"UPDATE user SET expir = '{new_hours}' WHERE id = '{target}' LIMIT 1")
                            
                            target_user = await app.get_users(target)
                            target_name = html.escape(target_user.first_name) if target_user.first_name else "کاربر"
                            
                            await app.send_message(chat_id, f"✅ با موفقیت {hours} ساعت انقضا به کاربر {target_name} افزوده شد ✓", 
                                disable_web_page_preview=True)
                            
                            if target != Admin:
                                await app.send_message(target, f"مدیر گرامی {hours} ساعت به انقضای شما افزود.\nانقضای جدید شما: {new_hours} ساعت")
                            
                        elif action == "کسر":
                            if user_hours >= hours:
                                if user_hours - hours >= 1:
                                    new_hours = user_hours - hours
                                    update_data(f"UPDATE user SET expir = '{new_hours}' WHERE id = '{target}' LIMIT 1")
                                    
                                    target_user = await app.get_users(target)
                                    target_name = html.escape(target_user.first_name) if target_user.first_name else "کاربر"
                                    
                                    await app.send_message(chat_id, f"✅ با موفقیت {hours} ساعت انقضا از کاربر {target_name} کسر شد ✓", 
                                        disable_web_page_preview=True)
                                    
                                    if target != Admin:
                                        await app.send_message(target, f"مدیر گرامی {hours} ساعت از انقضای شما کسر کرد.\nانقضای جدید شما: {new_hours} ساعت")
                                else:
                                    await app.send_message(chat_id, "❌ حداقل باید 1 ساعت انقضا برای کاربر باقی بماند!")
                            else:
                                await app.send_message(chat_id, "❌ انقضای کاربر کافی نیست!")
                        
                        await setscheduler(target)
                    else:
                        await app.send_message(chat_id, "❌ کاربر مورد نظر در ربات یافت نشد!")
                else:
                    await app.send_message(chat_id, "❌ لطفاً کاربر مورد نظر را مشخص کنید:\n- با یوزرنیم: @username\n- با آیدی عددی: 123456789\n- با ریپلای روی پیام کاربر")
            else:
                await app.send_message(chat_id, "فرمت صحیح:\n`افزایش [مقدار ساعت] [یوزرنیم/آیدی/ریپلای]`\n`کسر [مقدار ساعت] [یوزرنیم/آیدی/ریپلای]`")
        except ValueError:
            await app.send_message(chat_id, "❌ مقدار ساعت باید عدد باشد!")
        except Exception as e:
            await app.send_message(chat_id, f"❌ خطا: {str(e)}")

    #===================== Advanced Core Administration Steps =====================#
    if check_is_admin(chat_id):
        if user["step"] == "sendall":
            mess = await app.send_message(chat_id, "در حال ارسال به همه کاربران...")
            users = get_datas(f"SELECT id FROM user")
            for u in users:
                try:
                    await app.copy_message(from_chat_id=chat_id, chat_id=u[0], message_id=m_id)
                    await asyncio.sleep(0.1)
                except: pass
            await app.edit_message_text(chat_id, mess.id, "پیام شما برای همه کاربران ارسال شد")
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

        elif user["step"] == "forall":
            mess = await app.send_message(chat_id, "در حال فوروارد به همه کاربران...")
            users = get_datas(f"SELECT id FROM user")
            for u in users:
                try:
                    await app.forward_messages(from_chat_id=chat_id, chat_id=u[0], message_ids=m_id)
                    await asyncio.sleep(0.1)
                except: pass
            await app.edit_message_text(chat_id, mess.id, "پیام شما برای همه کاربران فوروارد شد")
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

        elif user["step"] == "userblock":
            if text.isdigit():
                user_id = int(text.strip())
                if get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1") is not None:
                    block = get_data(f"SELECT * FROM block WHERE id = '{user_id}' LIMIT 1")
                    if block is None:
                        try: await app.send_message(user_id, "کاربر محترم شما به دلیل نقض قوانین از ربات مسدود شدید")
                        except: pass
                        await app.send_message(chat_id, f"کاربر [ {user_id} ] از ربات بلاک شد")
                        update_data(f"INSERT INTO block(id) VALUES({user_id})")
                    else:
                        await app.send_message(chat_id, "این کاربر از قبل بلاک است")
                else:
                    await app.send_message(chat_id, "چنین کاربری در ربات یافت نشد!")
            else:
                await app.send_message(chat_id, "ورودی نامعتبر! فقط ارسال عدد مجاز است")
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

        elif user["step"] == "userunblock":
            if text.isdigit():
                user_id = int(text.strip())
                if get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1") is not None:
                    block = get_data(f"SELECT * FROM block WHERE id = '{user_id}' LIMIT 1")
                    if block is not None:
                        try: await app.send_message(user_id, "کاربر عزیز شما آنبلاک شدید و اکنون می توانید از ربات استفاده کنید")
                        except: pass
                        await app.send_message(chat_id, f"کاربر [ {user_id} ] از ربات آنبلاک شد")
                        update_data(f"DELETE FROM block WHERE id = '{user_id}' LIMIT 1")
                    else:
                        await app.send_message(chat_id, "این کاربر از ربات بلاک نیست!")
                else:
                    await app.send_message(chat_id, "چنین کاربری در ربات یافت نشد!")
            else:
                await app.send_message(chat_id, "ورودی نامعتبر! فقط ارسال عدد مجاز است")
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

        elif user["step"] == "amountinc":
            if text.isdigit():
                user_id = int(text.strip())
                if get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1") is not None:
                    await app.send_message(chat_id, "میزان موجودی مورد نظر خود را برای افزایش وارد کنید:")
                    update_data(f"UPDATE user SET step = 'amountinc2-{user_id}' WHERE id = '{chat_id}' LIMIT 1")
                else:
                    await app.send_message(chat_id, "چنین کاربری در ربات یافت نشد!")
                    update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")
            else:
                await app.send_message(chat_id, "ورودی نامعتبر! فقط ارسال عدد مجاز است")
                update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

        elif user["step"].split("-")[0] == "amountinc2":
            if text.isdigit():
                user_id = int(user["step"].split("-")[1])
                count = int(text.strip())
                user_amount = get_data(f"SELECT amount FROM user WHERE id = '{user_id}' LIMIT 1")
                user_upamount = int(user_amount["amount"]) + int(count)
                update_data(f"UPDATE user SET amount = '{user_upamount}' WHERE id = '{user_id}' LIMIT 1")
                await app.send_message(chat_id, f"مبلغ {count} تومان به حساب کاربر [ {user_id} ] افزوده شد\nموجودی جدید کاربر: {user_upamount} تومان")
                try: await app.send_message(user_id, f"مبلغ {count} تومان از طرف مدیر به حساب شما افزوده شد\nموجودی جدید شما: {user_upamount} تومان")
                except: pass
            else:
                await app.send_message(chat_id, "ورودی نامعتبر! فقط عدد مجاز است")
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

        elif user["step"] == "amountdec":
            if text.isdigit():
                user_id = int(text.strip())
                if get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1") is not None:
                    await app.send_message(chat_id, "میزان موجودی مورد نظر خود را برای کسر وارد کنید:")
                    update_data(f"UPDATE user SET step = 'amountdec2-{user_id}' WHERE id = '{chat_id}' LIMIT 1")
                else:
                    await app.send_message(chat_id, "چنین کاربری در ربات یافت نشد!")
                    update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")
            else:
                await app.send_message(chat_id, "ورودی نامعتبر! فقط ارسال عدد مجاز است")
                update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

        elif user["step"].split("-")[0] == "amountdec2":
            if text.isdigit():
                user_id = int(user["step"].split("-")[1])
                count = int(text.strip())
                user_amount = get_data(f"SELECT amount FROM user WHERE id = '{user_id}' LIMIT 1")
                if int(user_amount["amount"]) >= int(count):
                    user_upamount = int(user_amount["amount"]) - int(count)
                    update_data(f"UPDATE user SET amount = '{user_upamount}' WHERE id = '{user_id}' LIMIT 1")
                    await app.send_message(chat_id, f"مبلغ {count} تومان از حساب کاربر [ {user_id} ] کسر شد\nموجودی جدید کاربر: {user_upamount} تومان")
                    try: await app.send_message(user_id, f"مبلغ {count} تومان از طرف مدیر از حساب شما کسر شد\nموجودی جدید شما: {user_upamount} تومان")
                    except: pass
                else:
                    await app.send_message(chat_id, "موجودی کاربر کافی نیست!")
            else:
                await app.send_message(chat_id, "ورودی نامعتبر!")
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

        elif user["step"] == "expirinc":
            if text.isdigit():
                user_id = int(text.strip())
                if get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1") is not None:
                    await app.send_message(chat_id, "میزان زمان اشتراک مورد نظر خود را برای افزایش وارد کنید (ساعت):")
                    update_data(f"UPDATE user SET step = 'expirinc2-{user_id}' WHERE id = '{chat_id}' LIMIT 1")
                else:
                    await app.send_message(chat_id, "چنین کاربری در ربات یافت نشد!")
                    update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")
            else:
                await app.send_message(chat_id, "ورودی نامعتبر!")
                update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

        elif user["step"].split("-")[0] == "expirinc2":
            if text.isdigit():
                user_id = int(user["step"].split("-")[1])
                count = int(text.strip())
                user_expir = get_data(f"SELECT expir FROM user WHERE id = '{user_id}' LIMIT 1")
                user_expir_hours = int(user_expir["expir"]) + count
                update_data(f"UPDATE user SET expir = '{user_expir_hours}' WHERE id = '{user_id}' LIMIT 1")
                await app.send_message(chat_id, f"{count} ساعت به انقضای کاربر [ {user_id} ] افزوده شد\nانقضای جدید کاربر: {user_expir_hours} ساعت")
                try: await app.send_message(user_id, f"{count} ساعت از طرف مدیر به انقضای شما افزوده شد\nانقضای جدید شما: {user_expir_hours} ساعت")
                except: pass
                await setscheduler(user_id)
            else:
                await app.send_message(chat_id, "ورودی نامعتبر!")
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

        elif user["step"] == "expirdec_step":
            if text.isdigit():
                user_id = int(text.strip())
                if get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1") is not None:
                    await app.send_message(chat_id, "میزان زمان اشتراک مورد نظر خود را برای کسر وارد کنید (ساعت):")
                    update_data(f"UPDATE user SET step = 'expirdec2-{user_id}' WHERE id = '{chat_id}' LIMIT 1")
                else:
                    await app.send_message(chat_id, "چنین کاربری در ربات یافت نشد!")
                    update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")
            else:
                await app.send_message(chat_id, "ورودی نامعتبر!")
                update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

        elif user["step"].split("-")[0] == "expirdec2":
            if text.isdigit():
                user_id = int(user["step"].split("-")[1])
                count = int(text.strip())
                user_expir = get_data(f"SELECT expir FROM user WHERE id = '{user_id}' LIMIT 1")
                user_expir_hours = int(user_expir["expir"])
                if user_expir_hours >= count:
                    user_expir_hours -= count
                    update_data(f"UPDATE user SET expir = '{user_expir_hours}' WHERE id = '{user_id}' LIMIT 1")
                    await app.send_message(chat_id, f"{count} ساعت از انقضای کاربر [ {user_id} ] کسر شد\nانقضای جدید کاربر: {user_expir_hours} ساعت")
                    try: await app.send_message(user_id, f"{count} ساعت از طرف مدیر از انقضای شما کسر شد\nانقضای جدید شما: {user_expir_hours} ساعت")
                    except: pass
                    await setscheduler(user_id)
                else:
                    await app.send_message(chat_id, "انقضای کاربر کافی نیست!")
            else:
                await app.send_message(chat_id, "ورودی نامعتبر!")
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

        elif user["step"] == "selfon":
            if text.isdigit():
                user_id = int(text.strip())
                user_info = get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1")
                if user_info is not None:
                    if user_info["self"] == "inactive":
                        if user_info["phone"] is not None:
                            if not os.path.isfile(f"sessions/{user_id}.session-journal"):
                                async with lock:
                                    temp_Client[user_id] = {}
                                    temp_Client[user_id]["client"] = Client(f"sessions/{user_id}", api_id=API_ID, api_hash=API_HASH, device_model="Tabchi-Land", system_version="Linux")
                                    temp_Client[user_id]["number"] = user_info["phone"]
                                    await temp_Client[user_id]["client"].connect()
                                try:
                                    await app.send_message(chat_id, "در حال پردازش...")
                                    async with lock:
                                        temp_Client[user_id]["response"] = await temp_Client[user_id]["client"].send_code(temp_Client[user_id]["number"])
                                    await app.send_message(chat_id, "کد تایید 5 رقمی را با فرمت زیر ارسال کنید:\n1.2.3.4.5")
                                    update_data(f"UPDATE user SET step = 'selfon2-{user_id}' WHERE id = '{chat_id}' LIMIT 1")
                                except Exception as e:
                                    await app.send_message(chat_id, f"اتصال ناموفق بود: {e}")
                                    async with lock:
                                        try: await temp_Client[user_id]["client"].disconnect()
                                        except: pass
                                        if user_id in temp_Client: del temp_Client[user_id]
                                    update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")
                            else:
                                await app.send_message(chat_id, "اشتراک سلف برای این کاربر از قبل فعال است!")
                                update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")
                        else:
                            await app.send_message(chat_id, "این کاربر شماره تلفن ثبت شده ندارد!")
                            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")
                    else:
                        await app.send_message(chat_id, "سلف این کاربر از قبل فعال است!")
                        update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")
                else:
                    await app.send_message(chat_id, "چنین کاربری در ربات یافت نشد!")
                    update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")
            else:
                await app.send_message(chat_id, "ورودی نامعتبر!")
                update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

        elif user["step"].split("-")[0] == "selfon2":
            if re.match(r'^\d\.\d\.\d\.\d\.\d$', text):
                user_id = int(user["step"].split("-")[1])
                code = ''.join(re.findall(r'\d', text))
                mess = await app.send_message(chat_id, "در حال پردازش...")
                try:
                    async with lock:
                        await temp_Client[user_id]["client"].sign_in(temp_Client[user_id]["number"], temp_Client[user_id]["response"].phone_code_hash, code)
                        await temp_Client[user_id]["client"].disconnect()
                        if user_id in temp_Client: del temp_Client[user_id]
                    mess = await app.edit_message_text(chat_id, mess.id, "لاگین با موفقیت انجام شد\nدر حال فعالسازی سلف...")
                    if not os.path.isdir(f"selfs/self-{user_id}"):
                        os.mkdir(f"selfs/self-{user_id}")
                        with zipfile.ZipFile("source/Self.zip", "r") as extract:
                            extract.extractall(f"selfs/self-{user_id}")
                    process = subprocess.Popen(
                        ["python3", "self.py", str(user_id), str(API_ID), API_HASH, Helper_ID],
                        cwd=f"selfs/self-{user_id}", preexec_fn=os.setsid
                    )
                    await asyncio.sleep(10)
                    if process.poll() is None:
                        await app.edit_message_text(chat_id, mess.id, f"سلف با موفقیت برای کاربر [ {user_id} ] فعال شد")
                        try: await app.send_message(user_id, "اشتراک سلف شما توسط مدیر فعال شد")
                        except: pass
                        update_data(f"UPDATE user SET self = 'active', pid = '{process.pid}' WHERE id = '{user_id}' LIMIT 1")
                        add_admin(user_id)
                        await setscheduler(user_id)
                    else:
                        await app.edit_message_text(chat_id, mess.id, "در فعالسازی سلف مشکلی رخ داد!")
                except errors.SessionPasswordNeeded:
                    await app.edit_message_text(chat_id, mess.id, "رمز تایید دو مرحله ای فعال است. رمز را وارد کنید:")
                    update_data(f"UPDATE user SET step = 'selfon3-{user_id}' WHERE id = '{chat_id}' LIMIT 1")
                    return
                except Exception as e:
                    await app.edit_message_text(chat_id, mess.id, f"خطا: {e}")
            else:
                await app.send_message(chat_id, "فرمت کد نامعتبر است.")
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

        elif user["step"].split("-")[0] == "selfon3":
            user_id = int(user["step"].split("-")[1])
            password = text.strip()
            mess = await app.send_message(chat_id, "در حال پردازش...")
            try:
                async with lock:
                    await temp_Client[user_id]["client"].check_password(password)
                    await temp_Client[user_id]["client"].disconnect()
                    if user_id in temp_Client: del temp_Client[user_id]
                if not os.path.isdir(f"selfs/self-{user_id}"):
                    os.mkdir(f"selfs/self-{user_id}")
                    with zipfile.ZipFile("source/Self.zip", "r") as extract:
                        extract.extractall(f"selfs/self-{user_id}")
                process = subprocess.Popen(
                    ["python3", "self.py", str(user_id), str(API_ID), API_HASH, Helper_ID],
                    cwd=f"selfs/self-{user_id}", preexec_fn=os.setsid
                )
                await asyncio.sleep(10)
                if process.poll() is None:
                    await app.send_message(chat_id, f"سلف با موفقیت برای کاربر [ {user_id} ] فعال شد")
                    update_data(f"UPDATE user SET self = 'active', pid = '{process.pid}' WHERE id = '{user_id}' LIMIT 1")
                    add_admin(user_id)
                    await setscheduler(user_id)
                else:
                    await app.send_message(chat_id, "خطا در اجرای پایتون سلف.")
            except Exception as e:
                await app.send_message(chat_id, f"خطا در پسورد یا ورود: {e}")
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

        elif user["step"] == "selfoff":
            if text.isdigit():
                user_id = int(text.strip())
                user_info = get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1")
                if user_info is not None and user_info["self"] == "active":
                    await app.send_message(chat_id, f"درخواست حذف اشتراک کاربر {user_id}", reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text="تایید نهایی کسر و لغو", callback_data=f"DeleteSub-{user_id}", style="primary")]]
                    ))
                else:
                    await app.send_message(chat_id, "این کاربر سلف فعال ندارد.")
            else:
                await app.send_message(chat_id, "ورودی نامعتبر!")
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

        # پردازش استپ‌های اختصاصی قابلیت‌های پیشرفته جدید
        elif user["step"] == "set_card_num":
            update_data(f"UPDATE bot SET card_number = '{text.strip()}'")
            await m.reply_text("✅ شماره کارت جدید ثبت شد. اکنون نام صاحب حساب را ارسال کنید:")
            update_data(f"UPDATE user SET step = 'set_card_name' WHERE id = '{chat_id}' LIMIT 1")

        elif user["step"] == "set_card_name":
            update_data(f"UPDATE bot SET card_name = '{text.strip()}'")
            await m.reply_text("✅ اطلاعات کارت و دارنده آن با موفقیت بروزرسانی شد.")
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

        elif user["step"] == "add_fjoin_chan":
            chan_id = text.replace("@", "").strip()
            update_data(f"INSERT IGNORE INTO fjoin_channels(username) VALUES('{chan_id}')")
            await m.reply_text(f"✅ کانال @{chan_id} با موفقیت به لیست جوین اجباری اضافه شد.\nمطمئن شوید ربات در این کانال ادمین است.")
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

        elif user["step"] == "del_fjoin_chan":
            chan_id = text.replace("@", "").strip()
            # بررسی اینکه حداقل یک کانال همیشه وجود داشته باشد تا ربات ارور دیتابیس ندهد
            total_chans = get_datas("SELECT COUNT(*) FROM fjoin_channels")[0][0]
            if total_chans <= 1:
                await m.reply_text("❌ خطا! ربات باید حداقل دارای ۱ کانال جوین اجباری باشد. ابتدا کانال جدید اضافه کنید و سپس قبلی را حذف کنید.")
            else:
                update_data(f"DELETE FROM fjoin_channels WHERE username = '{chan_id}'")
                await m.reply_text(f"✅ کانال @{chan_id} با موفقیت از لیست جوین اجباری حذف شد.")
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

        elif user["step"] == "set_plans_price":
            try:
                p = text.split("-")
                update_data(f"UPDATE bot SET p1={int(p[0])}, p2={int(p[1])}, p3={int(p[2])}, p4={int(p[3])}, p5={int(p[4])}")
                await m.reply_text("✅ قیمت تمامی پلن‌ها با موفقیت اصلاح شد.")
            except: await m.reply_text("❌ فرمت نامعتبر.")
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

        elif user["step"] == "add_subadmin" and text.isdigit():
            helper_updata(f"INSERT IGNORE INTO adminlist(id) VALUES({int(text)})")
            await m.reply_text("✅ کاربر با موفقیت به ادمین‌های فرعی ربات ملحق شد.")
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

        elif user["step"] == "del_subadmin" and text.isdigit():
            helper_updata(f"DELETE FROM adminlist WHERE id = {int(text)}")
            await m.reply_text("✅ کاربر با موفقیت عزل شد.")
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

        elif user["step"] == "manage_user_id":
            u = get_data(f"SELECT * FROM user WHERE id = '{text.strip()}' LIMIT 1")
            if u:
                await m.reply_text(f"👤 اطلاعات کامل کاربر `{u['id']}`:\n\n📱 شماره: {u['phone']}\n💰 موجودی: {u['amount']} تومان\n⏳ انقضا: {u['expir']} ساعت\n🤖 وضعیت سلف: {u['self']}\n\nجهت تغییر سریع از فرامین زیر استفاده کنید:\n`شارژ {u['id']} [مبلغ]`\n`انقضا {u['id']} [ساعت]`")
            else: await m.reply_text("❌ کاربر در دیتابیس یافت نشد.")
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

        elif user["step"] == "send_direct_uid" and text.isdigit():
            await m.reply_text("پیام خود را جهت ارسال مستقیم بفرستید:")
            update_data(f"UPDATE user SET step = 'send_direct_msg-{text}' WHERE id = '{chat_id}' LIMIT 1")

        elif user["step"].split("-")[0] == "send_direct_msg":
            target = user["step"].split("-")[1]
            try:
                await app.copy_message(from_chat_id=chat_id, chat_id=int(target), message_id=m_id)
                await m.reply_text("✅ پیام مستقیم ارسال شد.")
            except Exception as e: await m.reply_text(f"❌ خطا: {e}")
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

        elif user["step"] == "set_start_txt":
            update_data("UPDATE bot SET start_text = %s", (text,))
            await m.reply_text("✅ متن استارت ربات با موفقیت تغییر کرد.")
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

        elif user["step"] == "set_help_text":
            update_data("UPDATE bot SET help_text = %s", (text,))
            await m.reply_text("✅ متن راهنما تغییر کرد.")
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

        elif user["step"] == "all_charge_step" and text.isdigit():
            update_data(f"UPDATE user SET amount = amount + {int(text)}")
            await m.reply_text(f"✅ شارژ همگانی اعمال شد و به حساب همه کاربران مبلغ {text} اضافه شد.")
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

        elif user["step"] == "all_expir_step" and text.isdigit():
            update_data(f"UPDATE user SET expir = expir + {int(text)}")
            await m.reply_text(f"✅ {text} ساعت به انقضای کلیه کاربران اضافه شد.")
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

        # دستورات متنی مدیریت کاربر چت‌مبنا
        elif text.startswith("شارژ ") or text.startswith("انقضا "):
            try:
                p = text.split()
                target_uid = int(p[1])
                val = int(p[2])
                if text.startswith("شارژ"):
                    update_data(f"UPDATE user SET amount = '{val}' WHERE id = '{target_uid}' LIMIT 1")
                    await m.reply_text(f"✅ موجودی کاربر {target_uid} به {val} تغییر کرد.")
                else:
                    update_data(f"UPDATE user SET expir = '{val}' WHERE id = '{target_uid}' LIMIT 1")
                    await m.reply_text(f"✅ انقضای کاربر {target_uid} به {val} ساعت تغییر کرد.")
                    await setscheduler(target_uid)
            except Exception as e: await m.reply_text(f"❌ خطا: {e}")

#===================== Panel Layout Setup =====================#
Panel = ReplyKeyboardMarkup(
    [
        ["آمار 📊", "ارسال همگانی ✉️", "فوروارد همگانی ✉️"],
        ["بلاک کاربر 🚫", "آنبلاک کاربر ✅️", "🔑 لیست مسدودی‌ها"],
        ["افزودن موجودی ➕", "کسر موجودی ➖", "افزودن زمان اشتراک ➕"],
        ["کسر زمان اشتراک ➖", "فعال کردن سلف 🔵", "غیرفعال کردن سلف 🔴"],
        ["💳 تنظیم کارت بانکی", "💰 تنظیم قیمت پلن‌ها", "📋 لیست مدیران"],
        ["➕ افزودن کانال قفل", "❌ حذف کانال قفل", "📋 لیست کانال‌های قفل"],
        ["👤 ارتقای ادمین", "👥 عزل ادمین", "💬 پیام مستقیم"],
        ["🔍 آمار و مدیریت کاربر", "🗄 بکاپ سریع دیتابیس", "🧹 پاکسازی فایل‌های موقت"],
        ["📝 تنظیم متن استارت", "ℹ️ تنظیم متن راهنما", "🧹 حذف کلیه سشن‌های مرده"],
        ["💰 شارژ همگانی", "⏳ تمدید همگانی", "روشن کردن ربات 🔵"],
        ["خاموش کردن ربات 🔴", "صفحه اصلی 🏠"]
    ], resize_keyboard=True
)

AdminBack = ReplyKeyboardMarkup(
    [[("برگشت")]], resize_keyboard=True
)

@app.on_message(filters.private&filters.user(Admin)&filters.command("panel"), group=1)
@checker
async def update(c, m):
    await app.send_message(Admin, "مدیر گرامی به پنل مدیریت فوق پیشرفته Tabchi Land خوش آمدید!", reply_markup=Panel)
    update_data(f"UPDATE user SET step = 'none' WHERE id = '{Admin}' LIMIT 1")
    async with lock:
        if Admin in temp_Client:
            del temp_Client[Admin]

@app.on_message(filters.private, group=2)
@checker
async def advanced_admin_buttons(c, m):
    if not check_is_admin(m.chat.id): return
    bot_cfg = get_data("SELECT * FROM bot")
    user = get_data(f"SELECT * FROM user WHERE id = '{m.chat.id}' LIMIT 1")
    text = m.text
    chat_id = m.chat.id

    if text == "برگشت":
        await app.send_message(chat_id, "مدیر گرامی به پنل مدیریت Tabchi Land خوش آمدید!", reply_markup=Panel)
        update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

    elif text == "آمار 📊":
        mess = await app.send_message(chat_id, "در حال دریافت اطلاعات...")
        botinfo = await app.get_me()
        allusers = get_datas("SELECT COUNT(id) FROM user")[0][0]
        allblocks = get_datas("SELECT COUNT(id) FROM block")[0][0]
        activeselfs = get_datas("SELECT COUNT(id) FROM user WHERE self='active'")[0][0]
        await app.edit_message_text(chat_id, mess.id, f"""
تعداد کاربران ربات: {allusers}
تعداد کاربران بلاک شده: {allblocks}
تعداد سلف های فعال لینوکس: {activeselfs}
--------------------------
نام ربات: {botinfo.first_name}
آیدی ربات: `{botinfo.id}`
یوزرنیم ربات: @{botinfo.username}
""")
        update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")

    elif text == "ارسال همگانی ✉️":
        await app.send_message(chat_id, "پیام خود را ارسال کنید:", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'sendall' WHERE id = '{chat_id}' LIMIT 1")

    elif text == "فوروارد همگانی ✉️":
        await app.send_message(chat_id, "پیام خود را ارسال کنید:", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'forall' WHERE id = '{chat_id}' LIMIT 1")

    elif text == "بلاک کاربر 🚫":
        await app.send_message(chat_id, "آیدی عددی کاربری را که می خواهید بلاک کنید ارسال کنید:", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'userblock' WHERE id = '{chat_id}' LIMIT 1")

    elif text == "آنبلاک کاربر ✅️":
        await app.send_message(chat_id, "آیدی عددی کاربری را که می خواهید آنبلاک کنید ارسال کنید:", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'userunblock' WHERE id = '{chat_id}' LIMIT 1")

    elif text == "🔑 لیست مسدودی‌ها":
        blist = get_datas("SELECT id FROM block")
        out = "🚫 لیست کاربران مسدود شده:\n\n" + "\n".join([f"`{row[0]}`" for row in blist]) if blist else "لیست مسدودی‌ها خالی است."
        await app.send_message(chat_id, out)

    elif text == "افزودن موجودی ➕":
        await app.send_message(chat_id, "آیدی عددی کاربر:", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'amountinc' WHERE id = '{chat_id}' LIMIT 1")

    elif text == "کسر موجودی ➖":
        await app.send_message(chat_id, "آیدی عددی کاربر:", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'amountdec' WHERE id = '{chat_id}' LIMIT 1")

    elif text == "افزودن زمان اشتراک ➕":
        await app.send_message(chat_id, "آیدی عددی کاربر:", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'expirinc' WHERE id = '{chat_id}' LIMIT 1")

    elif text == "کسر زمان اشتراک ➖":
        await app.send_message(chat_id, "آیدی عددی کاربر:", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'expirdec_step' WHERE id = '{chat_id}' LIMIT 1")

    elif text == "فعال کردن سلف 🔵":
        await app.send_message(chat_id, "آیدی عددی کاربر مورد نظر را وارد کنید:", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'selfon' WHERE id = '{chat_id}' LIMIT 1")

    elif text == "غیرفعال کردن سلف 🔴":
        await app.send_message(chat_id, "آیدی عددی کاربر مورد نظر را وارد کنید:", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'selfoff' WHERE id = '{chat_id}' LIMIT 1")

    elif text == "💳 تنظیم کارت بانکی":
        await app.send_message(chat_id, f"💳 مشخصات فعلی حساب:\n\n¼ شماره کارت: `{bot_cfg['card_number']}`\nصاحب حساب: {bot_cfg['card_name']}\n\nشماره کارت جدید را ارسال کنید:", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'set_card_num' WHERE id = '{chat_id}' LIMIT 1")

    # قابلیت جدید: افزودن بی نهایت کانال جوین اجباری به صورت مستقل
    elif text == "➕ افزودن کانال قفل":
        await app.send_message(chat_id, "آیدی کانال جدید را بدون @ ارسال کنید:", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'add_fjoin_chan' WHERE id = '{chat_id}' LIMIT 1")

    # قابلیت جدید: حذف داینامیک کانال جوین اجباری 
    elif text == "❌ حذف کانال قفل":
        await app.send_message(chat_id, "آیدی کانالی که قصد حذف قفل آن را دارید بدون @ بفرستید:", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'del_fjoin_chan' WHERE id = '{chat_id}' LIMIT 1")

    # قابلیت جدید: مشاهده لیست کامل تمام کانال های قفل شده ربات
    elif text == "📋 لیست کانال‌های قفل":
        chans = get_datas("SELECT username FROM fjoin_channels")
        out = "🔐 لیست کل کانال‌های جوین اجباری فعال:\n\n" + "\n".join([f"آیدی: @{row[0]}" for row in chans]) if chans else "هیچ کانالی قفل نیست."
        await app.send_message(chat_id, out)

    elif text == "💰 تنظیم قیمت پلن‌ها":
        await app.send_message(chat_id, f"💰 قیمت فعلی پلن‌ها به ترتیب:\nپلن ۱: {bot_cfg['p1']}\nپلن ۲: {bot_cfg['p2']}\nپلن ۳: {bot_cfg['p3']}\nپلن ۴: {bot_cfg['p4']}\nپلن ۵: {bot_cfg['p5']}\n\nهر ۵ قیمت جدید را با فرمت زیر با خط فاصله بفرستید:\n`70000-140000-210000-280000-350000`", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'set_plans_price' WHERE id = '{chat_id}' LIMIT 1")

    elif text == "👤 ارتقای ادمین" and chat_id == Admin:
        await app.send_message(chat_id, "آیدی عددی کاربر جهت ارتقا به مدیریت فرعی:", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'add_subadmin' WHERE id = '{chat_id}' LIMIT 1")

    elif text == "👥 عزل ادمین" and chat_id == Admin:
        await app.send_message(chat_id, "آیدی عددی ادمین فرعی جهت عزل:", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'del_subadmin' WHERE id = '{chat_id}' LIMIT 1")

    elif text == "📋 لیست مدیران":
        sub_admins = get_datas("SELECT id FROM adminlist")
        await app.send_message(chat_id, f"👑 مالک: `{Admin}`\n\n👥 ادمین‌های فرعی:\n" + "\n".join([f"`{r[0]}`" for r in sub_admins]))

    elif text == "🔍 آمار و مدیریت کاربر":
        await app.send_message(chat_id, "آیدی عددی کاربر مورد نظر را بفرستید:", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'manage_user_id' WHERE id = '{chat_id}' LIMIT 1")

    elif text == "💬 پیام مستقیم":
        await app.send_message(chat_id, "آیدی عددی کاربر مورد نظر:", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'send_direct_uid' WHERE id = '{chat_id}' LIMIT 1")

    elif text == "🗄 بکاپ سریع دیتابیس":
        try:
            raw = get_datas("SELECT * FROM user")
            with open("backup.txt", "w", encoding="utf-8") as f: f.write(str(raw))
            await app.send_document(chat_id, "backup.txt", caption="🗄 بکاپ فوری کاربران.")
            os.remove("backup.txt")
        except Exception as e: await app.send_message(chat_id, f"خطا: {e}")

    elif text == "🧹 پاکسازی فایل‌های موقت":
        cleared = 0
        for f in os.listdir("sessions"):
            if f.endswith("-journal"): os.remove(f"sessions/{f}"); cleared += 1
        await app.send_message(chat_id, f"🧹 تعداد {cleared} فایل موقت حذف شد.")

    elif text == "📝 تنظیم متن استارت":
        await app.send_message(chat_id, "متن جدید دستور /start را بفرستید:", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'set_start_txt' WHERE id = '{chat_id}' LIMIT 1")

    elif text == "ℹ️ تنظیم متن راهنما":
        await app.send_message(chat_id, "متن جدید برای بخش 'سلف چیست؟' را ارسال کنید:", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'set_help_text' WHERE id = '{chat_id}' LIMIT 1")

    elif text == "💰 شارژ همگانی":
        await app.send_message(chat_id, "مبلغ هدیه (به تومان) را جهت شارژ همگانی ارسال کنید:", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'all_charge_step' WHERE id = '{chat_id}' LIMIT 1")

    elif text == "⏳ تمدید همگانی":
        await app.send_message(chat_id, "میزان ساعت افزایشی به انقضای همه را ارسال کنید:", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'all_expir_step' WHERE id = '{chat_id}' LIMIT 1")

    elif text == "🧹 حذف کلیه سشن‌های مرده":
        dead_count = 0
        for f in os.listdir("sessions"):
            if f.endswith(".session"):
                uid = f.replace(".session", "")
                if uid.isdigit():
                    chk = get_data(f"SELECT self FROM user WHERE id = '{uid}' LIMIT 1")
                    if not chk or chk["self"] == "inactive":
                        if not os.path.isfile(f"sessions/{uid}.session-journal"):
                            try: os.remove(f"sessions/{f}"); dead_count += 1
                            except: pass
        await app.send_message(chat_id, f"🧹 تعداد {dead_count} فایل سشن مرده کاربران غیرفعال حذف شد.")

    elif text == "روشن کردن ربات 🔵":
        bot_status = get_data("SELECT * FROM bot")
        if bot_status["status"] == "OFF":
            update_data("UPDATE bot SET status = 'ON'")
            await app.send_message(chat_id, "ربات روشن شد")
        else:
            await app.send_message(chat_id, "ربات از قبل روشن است!")

    elif text == "خاموش کردن ربات 🔴":
        bot_status = get_data("SELECT * FROM bot")
        if bot_status["status"] == "ON":
            update_data("UPDATE bot SET status = 'OFF'")
            await app.send_message(chat_id, "ربات خاموش شد")
        else:
            await app.send_message(chat_id, "ربات از قبل خاموش است!")

    elif text == "صفحه اصلی 🏠":
        bot_cfg = get_data("SELECT * FROM bot")
        welcome = bot_cfg["start_text"] if bot_cfg["start_text"] else f"**🫡 سلام {html.escape(m.chat.first_name)} عزیز\n\n• به ربات خرید , پشتیبانی و مدیریت ورتکس سلف خوش آمدید\n\n• این ربات جهت اتوماتیک بودن خرید , تمدید و مدیریت سلف شما کاربران عزیز طراحی شده است\n\n• جهت ادامه کار یکی از گزینه های زیر را انتخاب کنید :**"
        await app.send_message(chat_id, welcome, reply_markup=Main)
        update_data(f"UPDATE user SET step = 'none' WHERE id = '{chat_id}' LIMIT 1")
        async with lock:
            if chat_id in temp_Client:
                del temp_Client[chat_id]

#===================== Start ======================#
print(Fore.GREEN + "Bot is running with Advanced Multi-Channel قفل جوین اجباری...")
app.run()
