# bot.py — Tripora AI (упрощённый, с вашими виджетами)
import os
import time
import telebot
from urllib.parse import quote

# ----------------- ПАРАМЕТРЫ (вставлены ваши widget URL из сообщений) -----------------
WIDGET_AVIA = "https://tpwgt.com/content?currency=rub&trs=475152&shmarker=685852&show_hotels=true&powered_by=true&locale=ru&searchUrl=www.aviasales.ru%2Fsearch&primary_override=%2332a8dd&color_button=%2332a8dd&color_icons=%2332a8dd&dark=%23262626&light=%23FFFFFF&secondary=%23FFFFFF&special=%23C4C4C4&color_focused=%2332a8dd&border_radius=0&plain=false&promo_id=7879&campaign_id=100"
WIDGET_SIMPLE = "https://tpwgt.com/content?trs=475152&shmarker=685852&locale=ru&powered_by=true&border_radius=0&plain=true&color_background=%23ffffff&color_border=%230f5de4&color_button=%2332a8dd&color_icons=%2332a8dd&promo_id=7257&campaign_id=459"
WIDGET_YELLOW = "https://tpwgt.com/content?trs=475152&shmarker=685852&locale=ru&powered_by=true&border_radius=5&plain=true&show_logo=true&color_background=%23ffca28&color_button=%2355a539&color_text=%23000000&color_input_text=%23000000&color_button_text=%23ffffff&promo_id=4480&campaign_id=10"

# tp.media redirect (если нужно — можно заменить маркер/params)
TP_REDIRECT = "https://tp.media/r"
MARKER = "685852"
TRS = "475152"

# Aviasales base (используем для прямого поиска в случае необходимости)
AVIASALES_BASE = "https://www.aviasales.com/search"

# ----------------- TELEGRAM TOKEN -----------------
TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN not set in environment variables")

bot = telebot.TeleBot(TOKEN)

# ---- простое состояние (для диалога)
user_states = {}  # chat_id -> {"step": ..., "data": {...}}

# ---- клавиатура главное меню (простая, удобная)
def main_menu_keyboard():
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    kb.row("✈️ Авиабилеты", "🚄 ЖД билеты", "🚌 Автобусы")
    kb.row("🏨 Отели", "🚗 Аренда авто", "🚕 Трансферы")
    kb.row("🧾 Мои билеты", "🧭 Туры и акции", "🚢 Круизы")
    kb.row("❓ Поддержка")
    return kb

# ---- помощник: создать tp.media редирект (для прямой ссылки)
def make_tp_redirect(target_url):
    encoded = quote(target_url, safe='')
    return f"{TP_REDIRECT}?marker={MARKER}&trs={TRS}&u={encoded}"

# ---- нормализация текста для простого определения команды
def norm(text):
    if not text:
        return ""
    return text.lower().strip()

# ---- старт
@bot.message_handler(commands=['start'])
def cmd_start(m):
    text = ("Привет! Я Tripora AI — ваш помощник по поиску билетов, отелей и туров.\n\n"
            "Нажмите кнопку внизу или напишите, что надо (например: 'авиабилеты').")
    bot.send_message(m.chat.id, text, reply_markup=main_menu_keyboard())

@bot.message_handler(commands=['menu', 'help'])
def cmd_menu(m):
    bot.send_message(m.chat.id, "Главное меню:", reply_markup=main_menu_keyboard())

# ---- начало авиа поиска
def start_avia_flow(m):
    user_states[m.chat.id] = {"step":"avia_origin","data":{}}
    bot.send_message(m.chat.id, "Начнём поиск авиабилетов. Введите город отправления (IATA или название):")

# ---- начало отелей
def start_hotels_flow(m):
    user_states[m.chat.id] = {"step":"hotels_city","data":{}}
    bot.send_message(m.chat.id, "Поиск отелей. Введите город (например: Almaty или Алматы):")

# ---- общий handler для кнопок/текста
@bot.message_handler(func=lambda msg: True)
def handler_all(m):
    cid = m.chat.id
    text = (m.text or "").strip()
    t = norm(text)

    # быстрые ключевые сопоставления (ключевые слова)
    if "ави" in t:
        start_avia_flow(m); return
    if "отел" in t or "hotel" in t:
        start_hotels_flow(m); return
    if "аренд" in t or "машин" in t or "авто" in t:
        # прямой переход: покажем виджет/ссылку на аренду (используем WIDGET_SIMPLE)
        kb = telebot.types.InlineKeyboardMarkup()
        kb.add(telebot.types.InlineKeyboardButton("Открыть виджет аренды (веб)", url=WIDGET_SIMPLE))
        bot.send_message(cid, "Перейдите по ссылке для аренды авто:", reply_markup=kb)
        return
    if "трансф" in t:
        kb = telebot.types.InlineKeyboardMarkup()
        kb.add(telebot.types.InlineKeyboardButton("Открыть трансферы (виджет)", url=WIDGET_YELLOW))
        bot.send_message(cid, "Перейдите по ссылке для трансферов:", reply_markup=kb)
        return
    if "круиз" in t or "круизы" in t:
        kb = telebot.types.InlineKeyboardMarkup()
        kb.add(telebot.types.InlineKeyboardButton("Открыть раздел круизов (виджет)", url=WIDGET_SIMPLE))
        bot.send_message(cid, "Круизы — открою раздел:", reply_markup=kb)
        return
    if "жд" in t or "поезд" in t:
        kb = telebot.types.InlineKeyboardMarkup()
        kb.add(telebot.types.InlineKeyboardButton("Открыть ЖД (виджет)", url=WIDGET_SIMPLE))
        bot.send_message(cid, "ЖД билеты — открываю виджет:", reply_markup=kb)
        return
    if "автобус" in t or "автобус" in t:
        kb = telebot.types.InlineKeyboardMarkup()
        kb.add(telebot.types.InlineKeyboardButton("Открыть автобусы (виджет)", url=WIDGET_SIMPLE))
        bot.send_message(cid, "Автобусы — открываю виджет:", reply_markup=kb)
        return
    if "поддерж" in t or "support" in t:
        bot.send_message(cid, "Поддержка: опишите проблему, и мы свяжемся с вами.")
        return
    if "меню" in t:
        cmd_menu(m); return

    # если есть активное состояние — продолжаем диалог
    state = user_states.get(cid)
    if not state:
        # нет состояния и не распознали команду
        bot.send_message(cid, "Нажмите /menu или выберите кнопку в меню.", reply_markup=main_menu_keyboard())
        return

    step = state.get("step")
    # авия flow
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
        state["step"] = "avia_passengers"
        bot.send_message(cid, "Сколько пассажиров? Введите число (например: 1):")
        return
    if step == "avia_passengers":
        # validate passengers
        try:
            p = int(text)
        except:
            bot.send_message(cid, "Нужно число. Попробуйте ещё раз:")
            return
        state["data"]["passengers"] = p

        od = state["data"]
        # строим простой aviasales поисковый URL (минимально, чтобы работал)
        params = []
        if od.get("origin"):
            params.append(f"origin={quote(od['origin'])}")
        if od.get("destination"):
            params.append(f"destination={quote(od['destination'])}")
        if od.get("depart_date") and od['depart_date'].lower() not in ("any","любой"):
            params.append(f"depart_date={quote(od['depart_date'])}")
        # return_date не используем в упрощённой версии (можно добавить)
        base = AVIASALES_BASE + ("?" + "&".join(params) if params else "")
        affiliate = make_tp_redirect(base)

        # Предлагаем 2 варианта: виджет (ваш script URL) и прямая редирект-ссылка
        kb = telebot.types.InlineKeyboardMarkup()
        kb.add(telebot.types.InlineKeyboardButton("Открыть в виджете (веб)", url=WIDGET_AVIA))
        kb.add(telebot.types.InlineKeyboardButton("Открыть прямой поиск (aviasales)", url=affiliate))

        bot.send_message(cid, "Готово — откройте удобный вариант:", reply_markup=kb)
        user_states.pop(cid, None)
        return

    # hotels flow
    if step == "hotels_city":
        city = text
        # делаем простой поисковый URL для отелей (и даём виджет + redirect)
        search_url = f"https://www.aviasales.com/hotels?search={quote(city)}"
        affiliate = make_tp_redirect(search_url)
        kb = telebot.types.InlineKeyboardMarkup()
        kb.add(telebot.types.InlineKeyboardButton("Открыть в виджете (отели)", url=WIDGET_AVIA))
        kb.add(telebot.types.InlineKeyboardButton("Открыть прямой поиск (hotels)", url=affiliate))
        bot.send_message(cid, f"Вот ссылки на поиск отелей в {city}:", reply_markup=kb)
        user_states.pop(cid, None)
        return

    # по умолчанию:
    bot.send_message(cid, "Не понял. Нажмите /menu или выберите кнопку.", reply_markup=main_menu_keyboard())

# запуск polling
if __name__ == "__main__":
    user_states.clear()
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print("Polling error:", e)
            time.sleep(5)
