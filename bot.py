# bot.py — Tripora AI (avia + hotels встроены через tp.media)
import os
import time
import telebot
from urllib.parse import quote

# ========== ПАРАМЕТРЫ ПАРТНЁРКИ (взяты из твоего скрипта)
MARKER = "685852"
TRS = "475152"
TP_REDIRECT = "https://tp.media/r"
# Базовые поисковые URL (можно менять)
AVIASALES_SEARCH_BASE = "https://www.aviasales.com/search"
AVIASALES_KZ_BASE = "https://www.aviasales.kz/search"

# Telegram token (должен быть в переменных среды на Render)
TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN not set in environment variables")

bot = telebot.TeleBot(TOKEN)

# ---- вспомогательная функция — собрать партнерскую ссылку через tp.media
def affiliate_search_link(base_search_url):
    encoded = quote(base_search_url, safe='')
    return f"{TP_REDIRECT}?marker={MARKER}&trs={TRS}&u={encoded}"

# ---- клавиатура главное меню
def main_menu_keyboard():
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    kb.row("✈️ Авиабилеты", "🚄 ЖД билеты", "🚌 Автобусы")
    kb.row("🏨 Отели", "🚗 Аренда авто", "🚕 Трансферы")
    kb.row("🧾 Мои билеты", "🧭 Туры и акции", "🚢 Круизы")
    kb.row("❓ Поддержка")
    return kb

# ---- старт
@bot.message_handler(commands=['start'])
def cmd_start(m):
    bot.send_message(m.chat.id,
        "Привет! Я Tripora AI — помогу найти билеты, отели и туры. Нажми кнопку или /menu.",
        reply_markup=main_menu_keyboard()
    )

@bot.message_handler(commands=['menu','help'])
def cmd_menu(m):
    bot.send_message(m.chat.id, "Главное меню:", reply_markup=main_menu_keyboard())

# ---- AVIA: диалогный поиск (быстрая версия — соберём ссылку по простым параметрам)
@bot.message_handler(commands=['avia'])
def cmd_avia_start(m):
    bot.send_message(m.chat.id, "Начнём поиск авиабилетов. Введите город отправления (IATA или название):")
    user_states[m.chat.id] = {"step":"avia_origin","data":{}}

# ---- HOTELS simple start
@bot.message_handler(commands=['hotels'])
def cmd_hotels_start(m):
    bot.send_message(m.chat.id, "Поиск отелей. Введите город (например: Almaty или Алматы):")
    user_states[m.chat.id] = {"step":"hotels_city","data":{}}

# ---- простое хранение состояния (память в процессе)
user_states = {}  # {chat_id: {"step": "...", "data": {...}}}

# ---- обработка сообщений (диалог)
@bot.message_handler(func=lambda msg: True)
def all_messages(m):
    cid = m.chat.id
    text = (m.text or "").strip()

    # если пользователь нажал одну из кнопок меню — перенаправляем на команды
    t = text.lower()
    if t in ("✈️ авиабилеты", "авиабилеты", "avia", "/avia"):
        cmd_avia_start(m); return
    if t in ("🏨 отели", "отели", "hotels", "/hotels"):
        cmd_hotels_start(m); return
    if t in ("❓ поддержка", "поддержка", "/support"):
        bot.send_message(cid, "Поддержка: напиши свой вопрос и мы свяжемся.")
        return
    if t in ("/menu", "меню"):
        cmd_menu(m); return

    state = user_states.get(cid)
    if not state:
        bot.send_message(cid, "Нажмите /menu или выберите кнопку.", reply_markup=main_menu_keyboard())
        return

    step = state.get("step")
    # --- avia flow
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
        # собираем все данные и формируем ссылку (партнёрский редирект)
        try:
            p = int(text)
        except:
            bot.send_message(cid, "Нужно число. Попробуйте ещё раз:")
            return
        state["data"]["passengers"] = p
        # строим базовый aviasales поиск URL (минимально)
        od = state["data"]
        # формируем query — используем базовый сайт aviasales.com
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

    # --- hotels flow
    if step == "hotels_city":
        city = text
        # формируем ссылку на вид поиска отелей на aviasales (параметры у разных сайтов отличаются)
        # здесь даём простой редирект на главную поиска отелей с параметром city
        search_url = f"https://www.aviasales.com/hotels?search={quote(city)}"
        affiliate = affiliate_search_link(search_url)
        kb = telebot.types.InlineKeyboardMarkup()
        kb.add(telebot.types.InlineKeyboardButton("Поиск отелей", url=affiliate))
        bot.send_message(cid, f"Вот ссылка на поиск отелей в {city}:", reply_markup=kb)
        user_states.pop(cid, None)
        return

    # default
    bot.send_message(cid, "Не понял. Нажмите /menu или выберите кнопку.", reply_markup=main_menu_keyboard())

# запуск
if __name__ == "__main__":
    # при старте очищаем состояния (безопасно)
    user_states.clear()
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print("Polling error:", e)
            time.sleep(5)
