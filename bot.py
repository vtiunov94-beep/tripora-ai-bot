# -*- coding: utf-8 -*-
"""
bot.py — Tripora AI unified simple bot (improved)
Просто вставь вместо старого: заменит старую логику, будет корректно работать с кнопками и виджетами.
Не забудь: BOT_TOKEN в окружении (Render / Heroku / прочие).
"""
import os
import time
import re
from urllib.parse import quote, urlencode

import telebot
from telebot import types

# ----------------- НАСТРОЙКИ ПАРТНЁРКИ -----------------
MARKER = "685852"        # shmarker/marker
TRS = "475152"           # trs
TP_REDIRECT = "https://tp.media/r"    # tp.media редирект
TPWGT_BASE = "https://tpwgt.com/content"  # виджет

# По умолчанию поисковые базовые URL (можешь заменить)
AVIASALES_BASE = "https://www.aviasales.com/search"
AVIASALES_RU = "https://www.aviasales.ru/search"
HOTELS_BASE = "https://www.aviasales.com/hotels"
CARS_BASE = "https://www.rentalcars.com/SearchResults.do"
TRAINS_BASE = "https://www.tutu.ru"
BUSES_BASE = "https://www.bus.com"
CRUISES_BASE = "https://www.cruise.example"

# ----------------- TOKEN -----------------
TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN not set in environment variables")

bot = telebot.TeleBot(TOKEN)

# ----------------- Утилиты -----------------
# шаблон для удаления эмодзи (и др. символов) - используется при сопоставлении кнопок
EMOJI_PATTERN = re.compile(
    "[\U00010000-\U0010ffff\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F\U0001F680-\U0001F6FF"
    "\u2600-\u26FF\u2700-\u27BF]", flags=re.UNICODE
)

def strip_emoji_and_normalize(s: str) -> str:
    if not s:
        return ""
    # удаляем emoji и вариационные селекторы, лишние пробелы, lower
    s = EMOJI_PATTERN.sub("", s)
    s = s.replace("\uFE0F", "")
    return re.sub(r"\s+", " ", s).strip().lower()

def affiliate_redirect_for_url(target_url: str) -> str:
    """Создаёт tp.media редирект для target_url"""
    encoded = quote(target_url, safe='')
    return f"{TP_REDIRECT}?marker={MARKER}&trs={TRS}&u={encoded}"

def tpwgt_widget_url(default_tab="plane", extra_params=None):
    """Генерирует tpwgt виджет ссылку, можно указать вкладку: plane/hotel/car/train/bus"""
    params = {
        "trs": TRS,
        "shmarker": MARKER,
        "powered_by": "true",
        "plane": "true",
        "train": "true",
        "bus": "true",
        "hotel": "true",
        "defaultTab": default_tab,
        "fix_width": "false",
        "logo": "true",
        "menu_icon": "true",
    }
    if extra_params:
        params.update(extra_params)
    return TPWGT_BASE + "?" + urlencode(params)

# ----------------- Клавиатура / Тексты -----------------
MENU_BUTTONS = [
    "✈️ Авиабилеты", "🚄 ЖД билеты", "🚌 Автобусы",
    "🏨 Отели", "🚗 Аренда авто", "🚕 Трансферы",
    "🧾 Мои билеты", "🧭 Туры и акции", "🚢 Круизы",
    "❓ Поддержка"
]

def main_menu_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    kb.add(*MENU_BUTTONS)
    return kb

# ----------------- State -----------------
# Простая память в процессе (не для продакшн, но для простого бота нормально)
user_states = {}  # {chat_id: {"section": "...", "step":"...", "data": {...}}}

# ----------------- START / MENU -----------------
@bot.message_handler(commands=['start'])
def cmd_start(m):
    text = ("Привет! Я Tripora AI — твой помощник по путешествиям.\n\n"
            "Выбери раздел в меню: авиабилеты, отели, аренда авто и т.д. — я пошагово помогу.")
    bot.send_message(m.chat.id, text, reply_markup=main_menu_keyboard())

@bot.message_handler(commands=['menu','help'])
def cmd_menu(m):
    bot.send_message(m.chat.id, "Главное меню:", reply_markup=main_menu_keyboard())

# ----------------- Flow starters -----------------
def start_avia_flow(cid):
    user_states[cid] = {"section": "avia", "step": "origin", "data": {}}
    bot.send_message(cid, "Начнём поиск авиабилетов. Введите город отправления (IATA или название):")

def start_hotels_flow(cid):
    user_states[cid] = {"section": "hotels", "step": "city", "data": {}}
    bot.send_message(cid, "Поиск отелей. Введите город (например: Almaty или Алматы):")

def start_cars_flow(cid):
    user_states[cid] = {"section": "cars", "step": "city", "data": {}}
    bot.send_message(cid, "Аренда авто. Введите город (например: Almaty или Алматы):")

def start_transfers_flow(cid):
    url = tpwgt_widget_url(default_tab="plane")  # виджет с вкладкой plane (в нём есть такси/transfer)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Открыть поиск трансферов/такси", url=url))
    bot.send_message(cid, "Открываю виджет для трансферов и такси:", reply_markup=kb)

def start_trains_flow(cid):
    target = TRAINS_BASE
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Поиск ЖД билетов", url=affiliate_redirect_for_url(target)))
    bot.send_message(cid, "Откройте поиск ЖД билетов:", reply_markup=kb)

def start_buses_flow(cid):
    target = BUSES_BASE
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Искать автобусы", url=affiliate_redirect_for_url(target)))
    bot.send_message(cid, "Переход к поиску автобусов:", reply_markup=kb)

def start_cruises_flow(cid):
    target = CRUISES_BASE
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Искать круизы", url=affiliate_redirect_for_url(target)))
    bot.send_message(cid, "Круизы — откройте ссылку:", reply_markup=kb)

def start_tours_flow(cid):
    url = tpwgt_widget_url(default_tab="plane")
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Поиск туров и акций", url=url))
    bot.send_message(cid, "Туры и акции — откройте виджет:", reply_markup=kb)

def start_my_tickets_flow(cid):
    bot.send_message(cid, "Мои билеты — пришлите номер брони или нажмите /menu для возврата.", reply_markup=main_menu_keyboard())

def support_flow(cid):
    bot.send_message(cid, "Поддержка: опишите проблему, и мы свяжемся с вами.", reply_markup=main_menu_keyboard())

# ----------------- Message handler -----------------
@bot.message_handler(func=lambda msg: True)
def all_messages(m):
    cid = m.chat.id
    raw = (m.text or "").strip()
    norm = strip_emoji_and_normalize(raw)

    # 1) Если пользователь в диалоге — обрабатываем шаги
    st = user_states.get(cid)
    if st:
        section = st.get("section")
        step = st.get("step")
        data = st.setdefault("data", {})

        # --- AVIA FLOW ---
        if section == "avia":
            if step == "origin":
                data["origin"] = raw
                st["step"] = "destination"
                bot.send_message(cid, "Куда летим? Введите город назначения (IATA или название):")
                return
            if step == "destination":
                data["destination"] = raw
                st["step"] = "depart_date"
                bot.send_message(cid, "Дата вылета (YYYY-MM-DD) или 'any' для любого дня:")
                return
            if step == "depart_date":
                data["depart_date"] = raw
                st["step"] = "return_date"
                bot.send_message(cid, "Дата возвращения (YYYY-MM-DD) или 'one' / 'без' для без возврата:")
                return
            if step == "return_date":
                data["return_date"] = raw
                st["step"] = "passengers"
                bot.send_message(cid, "Сколько пассажиров? Введите число (например: 1):")
                return
            if step == "passengers":
                # извлечь число
                nums = re.findall(r"\d+", raw)
                try:
                    p = int(nums[0]) if nums else 1
                except:
                    p = 1
                data["passengers"] = p
                # Формируем query и редирект
                query = {}
                if data.get("origin"):
                    query["origin"] = data["origin"]
                if data.get("destination"):
                    query["destination"] = data["destination"]
                if data.get("depart_date") and data["depart_date"].lower() not in ("any","любой"):
                    query["depart_date"] = data["depart_date"]
                if data.get("return_date") and data["return_date"].lower() not in ("one","без","none"):
                    query["return_date"] = data["return_date"]
                if data.get("passengers"):
                    query["adults"] = str(data["passengers"])

                base_search = AVIASALES_BASE + ("?" + urlencode(query) if query else "")
                affiliate = affiliate_redirect_for_url(base_search)
                kb = types.InlineKeyboardMarkup()
                kb.add(types.InlineKeyboardButton("Открыть лучшие рейсы", url=affiliate))
                bot.send_message(cid, "Готово — откройте поиск по ссылке:", reply_markup=kb)
                user_states.pop(cid, None)
                return

        # --- HOTELS FLOW ---
        if section == "hotels":
            if step == "city":
                city = raw
                search_url = HOTELS_BASE + ("?search=" + quote(city))
                affiliate = affiliate_redirect_for_url(search_url)
                kb = types.InlineKeyboardMarkup()
                kb.add(types.InlineKeyboardButton("Поиск отелей", url=affiliate))
                bot.send_message(cid, f"Вот ссылка на поиск отелей в «{city}»: ", reply_markup=kb)
                user_states.pop(cid, None)
                return

        # --- CARS FLOW ---
        if section == "cars":
            if step == "city":
                city = raw
                # формируем примерный target c city
                target = CARS_BASE + "?city=" + quote(city)
                affiliate = affiliate_redirect_for_url(target)
                kb = types.InlineKeyboardMarkup()
                kb.add(types.InlineKeyboardButton("Поиск аренды авто", url=affiliate))
                bot.send_message(cid, f"Переход к поиску авто в {city}:", reply_markup=kb)
                user_states.pop(cid, None)
                return

        # Если диалог есть, но шаг не распознан:
        bot.send_message(cid, "Не понял шаг. Вернись в меню:", reply_markup=main_menu_keyboard())
        return

    # 2) Если не в диалоге — смотрим текст и соответствие кнопкам
    # Сначала проверим точные нажатия одних из меню-кнопок (по "стрипнутому" тексту)
    # Создаём словарь соответствий "без emoji" -> handler
    mapping = {
        strip_emoji_and_normalize("✈️ Авиабилеты"): ("avia", start_avia_flow),
        strip_emoji_and_normalize("🏨 Отели"): ("hotels", start_hotels_flow),
        strip_emoji_and_normalize("🚗 Аренда авто"): ("cars", start_cars_flow),
        strip_emoji_and_normalize("🚕 Трансферы"): ("transfers", start_transfers_flow),
        strip_emoji_and_normalize("🚄 ЖД билеты"): ("trains", start_trains_flow),
        strip_emoji_and_normalize("🚌 Автобусы"): ("buses", start_buses_flow),
        strip_emoji_and_normalize("🚢 Круизы"): ("cruises", start_cruises_flow),
        strip_emoji_and_normalize("🧭 Туры и акции"): ("tours", start_tours_flow),
        strip_emoji_and_normalize("🧾 Мои билеты"): ("my_tickets", start_my_tickets_flow),
        strip_emoji_and_normalize("❓ Поддержка"): ("support", support_flow),
    }

    if norm in mapping:
        _, handler = mapping[norm]
        # handler может принимать chat_id либо объект message — все наши стартеры принимают chat_id
        # (за исключением некоторых, но в данном файле мы использовали chat_id)
        handler(cid)
        return

    # Дополнительные варианты текста (рус/eng)
    synonyms = {
        "авиабилеты": start_avia_flow,
        "авиа": start_avia_flow,
        "avia": start_avia_flow,
        "отели": start_hotels_flow,
        "hotels": start_hotels_flow,
        "аренда": start_cars_flow,
        "аренда авто": start_cars_flow,
        "cars": start_cars_flow,
        "такси": start_transfers_flow,
        "трансферы": start_transfers_flow,
        "жд билеты": start_trains_flow,
        "жд": start_trains_flow,
        "поезд": start_trains_flow,
        "автобусы": start_buses_flow,
        "buses": start_buses_flow,
        "круизы": start_cruises_flow,
        "туры": start_tours_flow,
        "билеты": start_my_tickets_flow,
        "поддержка": support_flow,
        "menu": lambda c: bot.send_message(c, "Главное меню:", reply_markup=main_menu_keyboard()),
        "меню": lambda c: bot.send_message(c, "Главное меню:", reply_markup=main_menu_keyboard()),
        "привет": lambda c: bot.send_message(c, "Привет — выбери раздел в меню:", reply_markup=main_menu_keyboard()),
        "start": lambda c: bot.send_message(c, "Привет — выбери раздел в меню:", reply_markup=main_menu_keyboard()),
    }

    if norm in synonyms:
        synonyms[norm](cid)
        return

    # Если ничего не распознали — даём подсказку и показываем меню
    bot.send_message(cid, "Нажмите /menu или выберите одну из кнопок в меню ниже.", reply_markup=main_menu_keyboard())

# ----------------- RUN -----------------
if __name__ == "__main__":
    user_states.clear()
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print("Polling error:", e)
            time.sleep(5)
