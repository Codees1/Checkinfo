from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from datetime import datetime
import phonenumbers
from phonenumbers import carrier, timezone, geocoder
import requests
import json
import re

def escape_markdown(text: str) -> str:
    escape_chars = r'\_*~`>#+-=|{}.!()[]'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)

def get_main_menu_text():
    return (
        "*⛓Правильный пойск*\n\n"
        "*✉️ Email*\n"
        "`Checkemail\\.com@gmail` \\- ❌\n"
        "`Checkemail@gmail\\.com` \\- ✅\n"
        "`Checkemail@mail\\.ru` \\- ✅\n\n"
        "*📍IP*\n"
        "`28828282882` \\- ❌\n"
        "`57\\.23\\.42\\.5` \\- ✅\n\n"
        "*📲 Номер телефона*\n"
        "`+$$\\-$$+##**` \\- ❌\n"
        "`+79001234567` \\- ✅\n\n"
        "*🔮 Я всегда готов*"
    )

def get_main_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🕵️Мой профиль", callback_data="profile")]
    ])

async def check_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if re.match(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$", text):
        await check_email(update, text)
        return

    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", text):
        await check_ip(update, text)
        return

    try:
        phone_number = text
        parsed_number = phonenumbers.parse(phone_number, None)
        if not phonenumbers.is_valid_number(parsed_number):
            await update.message.reply_text("*🕵️ Неверный формат*", parse_mode="MarkdownV2")
            return

        operator = carrier.name_for_number(parsed_number, "ru") or "Неизвестно"
        time_zone = timezone.time_zones_for_number(parsed_number)[0] or "Неизвестно"
        country = geocoder.description_for_number(parsed_number, "ru") or "Неизвестно"
        region = geocoder.description_for_number(parsed_number, "ru") or "Неизвестно"

        numverify_data = await check_with_numverify(phone_number)

        response = (
            f"*📲 Информация о номере* `{escape_markdown(phone_number)}`\n\n"
            f"  \\| \\- *Страна* \\- `{escape_markdown(country)}`\n"
            f"  \\| \\- *Регион* \\- `{escape_markdown(region)}`\n"
            f"  \\| \\- *Оператор* \\- `{escape_markdown(operator)}`\n"
            f"  \\| \\- *Часовой пояс* \\- `{escape_markdown(time_zone)}`\n"
            f"  \\| \\- *Статус* \\- `{escape_markdown(numverify_data.get('valid', 'Неизвестно'))}`\n"
            f"  \\| \\- *Тип* \\- `{escape_markdown(numverify_data.get('line_type', 'Неизвестно'))}`"
        )

        keyboard = [[InlineKeyboardButton(" <- Назад", callback_data="back")]]
        await update.message.reply_text(response, parse_mode="MarkdownV2", reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("*🕵️Ошибка при проверке номера*", parse_mode="MarkdownV2")

async def check_with_numverify(phone_number: str) -> dict:
    try:
        api_key = "bial3vg97k1owzf5"
        url = f"http://apilayer.net/api/validate?access_key={api_key}&number={phone_number}"
        response = requests.get(url)
        data = json.loads(response.text)

        return {
            'valid': "Активен" if data.get('valid') else "Неактивен",
            'line_type': data.get('line_type', 'Неизвестно')
        }
    except Exception as e:
        print(f"Numverify error: {e}")
        return {'valid': 'Неизвестно', 'line_type': 'Неизвестно'}

async def check_email(update: Update, email: str):
    try:
        token = "bial3vg97k1owzf5"
        url = f"https://api.2ip.io/email/{email}?token={token}"
        res = requests.get(url)
        data = res.json()

        msg = (
            f"*📧 Email:* `{escape_markdown(email)}`\n"
            f"  \\| \\- *Формат* \\- `{data.get('format_valid', False)}`\n"
            f"  \\| \\- *Домен* \\- `{data.get('domain_valid', False)}`\n"
            f"  \\| \\- *Существует* \\- `{data.get('mailbox_valid', False)}`\n"
            f"  \\| \\- *BlackList* \\- `{data.get('blacklisted', False)}`"
        )

        keyboard = [[InlineKeyboardButton(" <- Назад", callback_data="back")]]
        await update.message.reply_text(msg, parse_mode="MarkdownV2", reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        print(f"Email error: {e}")
        await update.message.reply_text("*🕵️Ошибка при проверке email*", parse_mode="MarkdownV2")

async def check_ip(update: Update, ip: str):
    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,message,query,country,regionName,city,isp"
        res = requests.get(url)
        data = res.json()

        if data.get("status") != "success":
            await update.message.reply_text(
                "*🕵️Ошибка Неверный IP*",
                parse_mode="MarkdownV2"
            )
            return

        msg = (
            f"*🔮 IP:* `{escape_markdown(data['query'])}`\n"
            f"  \\| \\- *Страна* \\- `{escape_markdown(data.get('country', 'Неизвестно'))}`\n"
            f"  \\| \\- *Регион* \\- `{escape_markdown(data.get('regionName', 'Неизвестно'))}`\n"
            f"  \\| \\- *Город* \\- `{escape_markdown(data.get('city', 'Неизвестно'))}`\n"
            f"  \\| \\- *Провайдер* \\- `{escape_markdown(data.get('isp', 'Неизвестно'))}`"
        )

        keyboard = [[InlineKeyboardButton(" <- Назад", callback_data="back")]]
        await update.message.reply_text(msg, parse_mode="MarkdownV2", reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        print(f"IP error: {e}")
        await update.message.reply_text(
    "*🕵️Ошибка при проверке IP*",
    parse_mode="MarkdownV2",
    reply_markup=InlineKeyboardMarkup(keyboard)
)

    except Exception as e:
        print(f"IP error: {e}")
        await update.message.reply_text("*🕵️Ошибка при проверке IP*", parse_mode="MarkdownV2")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link_message = await update.message.reply_text(
        "*🔮ВЕЧНАЯ ССЫЛКА НА CheckInfo*",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔮Ссылка", url="https://t.me/checkinfovalid")]
        ])
    )

    await context.bot.pin_chat_message(
        chat_id=update.effective_chat.id,
        message_id=link_message.message_id,
        disable_notification=True
    )

    context.user_data['start_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await update.message.reply_text(
        get_main_menu_text(),
        parse_mode="MarkdownV2",
        reply_markup=get_main_buttons()
    )

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "profile":
        user = query.from_user
        start_time = context.user_data.get('start_time', 'неизвестно')

        text = (
            "*🕵️Мой профиль*\n\n"
            f"*🆔* \\- `{user.id}`\n"
            f"*🔮Username* \\- @{escape_markdown(user.username) if user.username else 'нет'}\n"
            f"*🗓️Время регистрации* \\- `{escape_markdown(start_time)}`"
        )
        keyboard = [[InlineKeyboardButton("<- Назад", callback_data="back")]]
        await query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "back":
        await query.edit_message_text(
            get_main_menu_text(),
            parse_mode="MarkdownV2",
            reply_markup=get_main_buttons()
        )

if __name__ == "__main__":
    app = ApplicationBuilder().token("7476234090:AAEhV7PNvZmhcymyTNh6cjE-T0ulbcIhR9o").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_phone_number))

    print("Бот запущен!")
    app.run_polling()
