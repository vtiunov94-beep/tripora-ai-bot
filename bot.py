# bot.py — Tripora AI (fixed buttons + robust keyword handling + affiliate links)
import os
import time
import re
import telebot
from urllib.parse import quote

# ========== ПАРАМЕТРЫ ПАРТНЁРКИ
MARKER = "685852"
TRS = "475152"
TP_REDIRECT = "https://tp.media/r"

AVIASALES_SEARCH_BASE = "https://www.aviasales.com/search"
AVIASALES_KZ_BASE = "https://www.aviasales.kz/search"

# Telegram token (Render env var)
TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN not set in environment variables")

bot = telebot.TeleBot(TOKEN)

# ---- простое хранение состояния (память в процессе)
user_states = {}  # {chat_id: {"step": "...", "data": {...}}}

# ---- вспомогательные функции
def affiliate_search_link(base_search_url):
    encoded = quote(base_search_url, safe='')
    return f"{TP_REDIRECT}?marker={MARKER}&trs={TRS}&u={encoded}"

# Нормализует вход (убирает эмодзи, лишние символы, приводит к lowercase)
def normalize_text(s):
    if not s:
        return ""
    # заменяем специальные кавычки/тире на обычные пробелы
    s = s.replace('\u2013', ' ').replace('\u2014',' ').replace('\u2019',' ')
    # удаляем URL-процент-коды, оставим буквы/цифры/пробелы (кириллица и латиница)
    # оставляем также знаки / и - (на случай IATA или форматов)
    s = re.sub(r'[^\w\s\-\/]', ' ', s, flags=re.UNICODE)
    # убрать подчёркивания и лишние пробелы
    s = s.replace('_',' ')
    s = re.sub(r'\s+', ' ', s).strip()
    return s.lower()

# Определение ключевых команд по вхождению слова
COMMAND_KEYWORDS = {
    "avia": ["avia","авиа","✈","самолет","билет","flight","flights"],
    "hotels": ["hotel","отел","🏨","отели","hotels"],
    "rail": ["жд","ржд","поезд","rail","train","🚄"],
    "buses": ["автобус","bus","🚌","автобусы"],
    "cars": ["аренд","машин","car","rent","🚗","аренда"],
    "transfer": ["трансфер","taxi","такси","🚕","transfer"],
    "tickets": ["мои билеты","ticket","tickets","билеты","🧾"],
    "tours": ["тур","туры","акц","tours","🧭"],
    "cruise": ["круз","круиз","cruise","🚢"],
    "support": ["поддержк","support","help","❓"]
}

def detect_command_from_text(txt):
    n = normalize_text(txt)
    # exact words and substrings
    for cmd, keywords in COMMAND_KEYWORDS.items():
        for kw in keywords:
            if kw in n:
                return cmd
    return None

# ---- клавиатура главное меню
def main_menu_keyboard():
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    kb.row("✈️ Авиабилеты", "🚄 ЖД билеты", "🚌 Автобусы")
    kb.row("🏨 Отели", "🚗 Аренда авто", "🚕 Трансферы")
    kb.row("🧾 Мои билеты", "🧭 Туры и акции", "🚢 Круизы")
    kb.row("❓ Поддержка")
    return kb

# ---- старт и меню
@bot.message_handler(commands=['start'])
def cmd_start(m):
    txt = ("Привет! Я *Tripora AI* — ваш персональный помощник по билетам, отелям и турам.\n\n"
           "Нажмите одну из кнопок ниже или напишите что нужно (например: «авиа», «отели», «аренда»).")
    bot.send_message(m.chat.id, txt, parse_mode="Markdown", reply_markup=main_menu_keyboard())

@bot.message_handler(commands=['menu','help'])
def cmd_menu(m):
    bot.send_message(m.chat.id, "Главное меню — выберите раздел или напишите запрос:", reply_markup=main_menu_keyboard())

# ---- AVIA: диалогный поиск (быстрая версия)
@bot.message_handler(commands=['avia'])
def cmd_avia_start(m):
    bot.send_message(m.chat.id, "Начнём поиск авиабилетов. Введите город отправления (IATA или название):")
    user_states[m.chat.id] = {"step":"avia_origin","data":{}}

# ---- HOTELS simple start
@bot.message_handler(commands=['hotels'])
def cmd_hotels_start(m):
    bot.send_message(m.chat.id, "Поиск отелей. Введите город (например: Almaty или Алматы):")
    user_states[m.chat.id] = {"step":"hotels_city","data":{}}

# ---- Обработка любых сообщений — в том числе кнопок
@bot.message_handler(func=lambda msg: True)
def all_messages(m):
    cid = m.chat.id
    text = (m.text or "").strip()
    if not text:
        bot.send_message(cid, "Пока я могу работать только с текстом. Нажмите /menu.", reply_markup=main_menu_keyboard())
        return

    # Сначала — попытка распознать команду по ключевым словам (работает с эмодзи/вариациями)
    detected = detect_command_from_text(text)
    if detected == "avia":
        cmd_avia_start(m); return
    if detected == "hotels":
        cmd_hotels_start(m); return
    if detected == "rail":
        bot.send_message(cid, "Запуск поиска ЖД билетов — пока что перенаправлю на общий поиск.", reply_markup=main_menu_keyboard()); return
    if detected == "buses":
        bot.send_message(cid, "Ищем автобусы — перенаправляю к поиску.", reply_markup=main_menu_keyboard()); return
    if detected == "cars":
        # простой ответ с виджетом / ссылкой аренды (можно подставить виджет)
        bot.send_message(cid, "Перейдите по ссылке для аренды авто:", reply_markup=main_menu_keyboard())
        return
    if detected == "transfer":
        bot.send_message(cid, "Трансферы — предлагаю открыть виджет такси/трансфера:", reply_markup=main_menu_keyboard())
        return
    if detected == "tours":
        bot.send_message(cid, "Туры и акции — вот раздел с предложениями:", reply_markup=main_menu_keyboard())
        return
    if detected == "cruise":
        bot.send_message(cid, "Круизы — открою раздел:", reply_markup=main_menu_keyboard())
        return
    if detected == "support":
        bot.send_message(cid, "Поддержка: опишите проблему, и наш менеджер свяжется с вами.", reply_markup=main_menu_keyboard())
        return

    # если не распознано по слову — проверяем состояние диалога
    state = user_states.get(cid)
    if state:
        step = state.get("step")
        # avia flow
        if step == "avia_origin":
            state["data"]["origin"] = text
            state["step"] = "avia_destination"
            bot.send_message(cid, "Куда летим? Введите город назначения (IATA или название):")
            return
        if step == "avia_destination":
            state["data"]["destination"] = text
            state["step"] = "avia_depart_date"
            bot.send_message(cid, "Дата вылета (YYYY-MM-DD) или 'any' для любого дня:")
            return
        if step == "avia_depart_date":
            state["data"]["depart_date"] = text
            state["step"] = "avia_return_date"
            bot.send_message(cid, "Дата возвращения (YYYY-MM-DD) или 'one' / 'без' для без возврата:")
            return
        if step == "avia_return_date":
            state["data"]["return_date"] = text
            state["step"] = "avia_passengers"
            bot.send_message(cid, "Сколько пассажиров? Введите число (например: 1):")
            return
        if step == "avia_passengers":
            try:
                p = int(re.sub(r'\D','', text) or "1")
            except:
                bot.send_message(cid, "Нужно число. Попробуйте ещё раз:")
                return
            state["data"]["passengers"] = p
            od = state["data"]
            params = []
            if od.get("origin"):
                params.append(f"origin={quote(od['origin'])}")
            if od.get("destination"):
                params.append(f"destination={quote(od['destination'])}")
            if od.get("depart_date") and od['depart_date'].lower() not in ("any","любой"):
                params.append(f"depart_date={quote(od['depart_date'])}")
            if od.get("return_date") and od['return_date'].lower() not in ("one","без","away","none"):
                params.append(f"return_date={quote(od['return_date'])}")
            base = AVIASALES_SEARCH_BASE + ("?" + "&".join(params) if params else "")
            affiliate = affiliate_search_link(base)
            kb = telebot.types.InlineKeyboardMarkup()
            kb.add(telebot.types.InlineKeyboardButton("Открыть лучшие рейсы", url=affiliate))
            bot.send_message(cid, "Готово — открывайте поиск по ссылке:", reply_markup=kb)
            user_states.pop(cid, None)
            return

        # hotels flow
        if step == "hotels_city":
            city = text
            search_url = f"https://www.aviasales.com/hotels?search={quote(city)}"
            affiliate = affiliate_search_link(search_url)
            kb = telebot.types.InlineKeyboardMarkup()
            kb.add(telebot.types.InlineKeyboardButton("Поиск отелей", url=affiliate))
            bot.send_message(cid, f"Вот ссылка на поиск отелей в {city}:", reply_markup=kb)
            user_states.pop(cid, None)
            return

    # если не в состоянии и не распознано — предложить меню и подсказку
    bot.send_message(cid, "Не понял. Нажмите /menu или выберите кнопку (можно просто написать: 'авиа', 'отели', 'аренда').", reply_markup=main_menu_keyboard())

# запуск
if __name__ == "__main__":
    user_states.clear()
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print("Polling error:", e)
            time.sleep(5)
