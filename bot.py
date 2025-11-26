# -*- coding: utf-8 -*-
"""
Tripora AI — final unified bot (stable widget + fallback)
Instructions:
 - Set BOT_TOKEN in env (Render / host)
 - Optionally set ADMIN_CHAT to your chat_id to receive debug URLs
"""
import os, time, re
from urllib.parse import quote, urlencode
import telebot
from telebot import types

# ---------------- CONFIG ----------------
MARKER = "685852"
TRS = "475152"
TP_REDIRECT = "https://tp.media/r"
TPWGT_BASE = "https://tpwgt.com/content"

# promo_id mapping (из твоих сообщений)
PROMOS = {
    "avia": {"promo_id":"7879","campaign_id":"100"},
    "cars": {"promo_id":"7257","campaign_id":"459"},
    "hotels": {"promo_id":"4480","campaign_id":"10"},
    "transfers": {"promo_id":"9093","campaign_id":"45"},
}

# Base search URLs (fallbacks)
AVIASALES_BASE = "https://www.aviasales.com/search"
HOTELS_BASE = "https://www.aviasales.com/hotels"
CARS_BASE = "https://www.rentalcars.com/SearchResults.do"
TRAINS_BASE = "https://www.tutu.ru"
BUSES_BASE = "https://www.bus.com"

# ---------------- TOKEN ----------------
TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
ADMIN_CHAT = os.getenv("ADMIN_CHAT")  # optional: числовой chat_id
if not TOKEN:
    raise RuntimeError("BOT_TOKEN not set in environment variables")

bot = telebot.TeleBot(TOKEN)

# ---------------- helpers ----------------
def quote_safe(u: str) -> str:
    return quote(u, safe='')

def affiliate_redirect_for_url(target_url: str) -> str:
    return f"{TP_REDIRECT}?marker={MARKER}&trs={TRS}&u={quote_safe(target_url)}"

def tpwgt_widget_url(default_tab="plane", promo=None):
    params = {
        "trs": TRS,
        "shmarker": MARKER,
        "locale": "ru",
        "powered_by": "true",
        "plane": "true",
        "train": "true",
        "bus": "true",
        "hotel": "true",
        "defaultTab": default_tab,
        "fix_width": "false",
        "logo": "true",
        "menu_icon": "true"
    }
    if promo:
        params.update(promo)
    return TPWGT_BASE + "?" + urlencode(params)

def safe_send_admin(text: str):
    if ADMIN_CHAT:
        try:
            bot.send_message(int(ADMIN_CHAT), text)
        except Exception:
            pass

EMOJI_RE = re.compile("[\U00010000-\U0010ffff\U0001F300-\U0010F5FF"
                      "\U0001F600-\U0011F64F\U0001F680-\U0010F6FF"
                      "\u2600-\u26FF\u2700-\u27BF]", flags=re.UNICODE)
def normalize_text(s: str) -> str:
    if not s: return ""
    s = EMOJI_RE.sub("", s)
    s = s.replace("\uFE0F", "")
    return re.sub(r"\s+", " ", s).strip().lower()

def is_iata(s: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z]{3}", (s or "").strip()))

# ---------------- keyboard ----------------
def main_menu_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    kb.add(
        "✈️ Авиабилеты", "🚄 ЖД билеты", "🚌 Автобусы",
        "🏨 Отели", "🚗 Аренда авто", "🚕 Трансферы",
        "🧾 Мои билеты", "🧭 Туры и акции", "🚢 Круизы",
        "❓ Поддержка"
    )
    return kb

# ---------------- state ----------------
user_states = {}

# ---------------- flows ----------------
@bot.message_handler(commands=['start'])
def cmd_start(m):
    text = ("Привет! Я Tripora AI — твой помощник по путешествиям.\n\n"
            "Выбери раздел внизу. Если хочешь — введи IATA коды (3 буквы) для прямого поиска.")
    bot.send_message(m.chat.id, text, reply_markup=main_menu_keyboard())

@bot.message_handler(commands=['menu','help'])
def cmd_menu(m):
    bot.send_message(m.chat.id, "Главное меню:", reply_markup=main_menu_keyboard())

def start_flow(cid, section):
    user_states[cid] = {"step": f"{section}_step1", "section": section, "data": {}}
    if section == "avia":
        bot.send_message(cid, "Начнём поиск авиабилетов. Введите город отправления (IATA или название):")
    elif section == "hotels":
        bot.send_message(cid, "Поиск отелей. Введите город (например: Almaty или Алматы):")
    elif section == "cars":
        bot.send_message(cid, "Аренда авто. Введите город (например: Almaty или Алматы):")

def open_widget(cid, tab, promo_key):
    promo = PROMOS.get(promo_key)
    url = tpwgt_widget_url(default_tab=tab, promo=promo)
    kb = types.InlineKeyboardMarkup(); kb.add(types.InlineKeyboardButton("Открыть виджет", url=url))
    bot.send_message(cid, "Откройте виджет поиска:", reply_markup=kb)
    safe_send_admin(f"[WIDGET] user={cid} tab={tab} url={url}")
    return url

# ---------------- main handler ----------------
@bot.message_handler(func=lambda msg: True)
def all_messages(m):
    cid = m.chat.id
    text = (m.text or "").strip()
    norm = normalize_text(text)

    # если в диалоге
    state = user_states.get(cid)
    if state:
        section = state["section"]
        step = state["step"]
        data = state.get("data", {})

        # AVIA dialog steps
        if section == "avia":
            if step == "avia_step1":
                data["origin"] = text.strip()
                state["step"] = "avia_step2"
                bot.send_message(cid, "Куда летим? Введите город назначения (IATA или название):")
                return
            if step == "avia_step2":
                data["destination"] = text.strip()
                state["step"] = "avia_step3"
                bot.send_message(cid, "Дата вылета (YYYY-MM-DD) или 'any' для любого дня:")
                return
            if step == "avia_step3":
                data["depart_date"] = text.strip()
                state["step"] = "avia_step4"
                bot.send_message(cid, "Дата возвращения (YYYY-MM-DD) или 'one' / 'без' для без возврата:")
                return
            if step == "avia_step4":
                data["return_date"] = text.strip()
                state["step"] = "avia_step5"
                bot.send_message(cid, "Сколько пассажиров? Введите число (например: 1):")
                return
            if step == "avia_step5":
                try:
                    p = int(re.sub(r"\D","", text) or "1")
                except:
                    bot.send_message(cid, "Нужно число. Попробуйте ещё раз:")
                    return
                data["passengers"] = p

                origin = data.get("origin","")
                dest = data.get("destination","")
                depart = data.get("depart_date","")
                ret = data.get("return_date","")

                # если IATA — строим прямую aviasales ссылку и отдаём через tp.media
                if is_iata(origin) and is_iata(dest):
                    q = {"origin": origin.upper(), "destination": dest.upper()}
                    if depart and depart.lower() not in ("any","любой"): q["depart_date"]=depart
                    if ret and ret.lower() not in ("one","без","none"): q["return_date"]=ret
                    q["adults"]=str(p)
                    base = AVIASALES_BASE + "?" + urlencode(q)
                    affiliate = affiliate_redirect_for_url = f"{TP_REDIRECT}?marker={MARKER}&trs={TRS}&u={quote_safe(base)}"
                    kb = types.InlineKeyboardMarkup(); kb.add(types.InlineKeyboardButton("Открыть лучшие рейсы", url=affiliate))
                    bot.send_message(cid, "Готово — откройте поиск (Aviasales):", reply_markup=kb)
                    safe_send_admin(f"[AVIA DIRECT] user={cid} base={base} affiliate={affiliate}")
                    user_states.pop(cid, None)
                    return
                else:
                    # иначе — открываем виджет (надежнее для текстовых названий)
                    url = open_widget(cid, tab="plane", promo_key="avia")
                    bot.send_message(cid, "Я открыл виджет — он лучше обрабатывает названия городов. Откройте его и введите параметры.", reply_markup=None)
                    user_states.pop(cid, None)
                    return

        # HOTELS
        if section == "hotels" and step == "hotels_step1":
            city = text.strip()
            url = open_widget(cid, tab="hotel", promo_key="hotels")
            bot.send_message(cid, f"Открывайте виджет — поиск отелей в «{city}».", reply_markup=None)
            user_states.pop(cid, None)
            return

        # CARS
        if section == "cars" and step == "cars_step1":
            city = text.strip()
            url = open_widget(cid, tab="plane", promo_key="cars")
            bot.send_message(cid, f"Открывайте виджет — аренда авто в «{city}».", reply_markup=None)
            user_states.pop(cid, None)
            return

        # fallback
        bot.send_message(cid, "Не понял шаг — вернись в меню:", reply_markup=main_menu_keyboard())
        return

    # если не в состоянии — команды / кнопки
    if norm in ("авиабилеты","avia","авиа"):
        start_flow(cid, "avia"); return
    if norm in ("отели","hotels","отель"):
        start_flow(cid, "hotels"); return
    if norm in ("аренда авто","аренда","cars"):
        start_flow(cid, "cars"); return
    if norm in ("трансферы","такси","transfers"):
        url = open_widget(cid, tab="plane", promo_key="transfers"); return
    if norm in ("жд билеты","жд","поезд","trains"):
        url = open_widget(cid, tab="train", promo_key="avia"); return
    if norm in ("автобусы","bus","buses"):
        url = open_widget(cid, tab="bus", promo_key="avia"); return
    if norm in ("круизы","cruise","cruises"):
        url = open_widget(cid, tab="plane", promo_key="avia"); return
    if norm in ("мои билеты","билеты","tickets"):
        start_flow(cid, "my_tickets"); return
    if norm in ("поддержка","support"):
        bot.send_message(cid, "Поддержка: опишите проблему, мы ответим.", reply_markup=main_menu_keyboard()); return

    if norm in ("menu","меню","start","привет","здравствуйте"):
        bot.send_message(cid, "Привет — выбери пункт в меню.", reply_markup=main_menu_keyboard()); return

    bot.send_message(cid, "Нажмите /menu или выберите кнопку внизу.", reply_markup=main_menu_keyboard())

# ---------------- run ----------------
if __name__ == "__main__":
    user_states.clear()
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            safe_send_admin(f"Polling error: {e}")
            time.sleep(5)
