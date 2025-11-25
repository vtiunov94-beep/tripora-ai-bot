# bot.py — Tripora AI (полностью обновлённая версия)
import os
import time
import telebot
from urllib.parse import quote, urlencode

# ================== НАСТРОЙКИ (ставь свои переменные в Render) ==================
TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
MARKER = os.getenv("MARKER", "685852")
TRS = os.getenv("TRS", "475152")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in environment variables")

bot = telebot.TeleBot(TOKEN)

# Состояние диалогов
user_states = {}

# ================== ГЕНЕРАЦИЯ РАБОЧЕЙ ССЫЛКИ ==================
def build_aviasales_search(origin="", destination="", depart_date="", return_date="", passengers=1):
    """
    Формирует рабочую ссылку на Aviasales
    """
    base = "https://www.aviasales.com/search"
    params = {}

    if origin:
        params["origin"] = origin
    if destination:
        params["destination"] = destination
    if depart_date and depart_date.lower() not in ("any","любой"):
        params["depart_date"] = depart_date
    if return_date and return_date.lower() not in ("one","без","none","нет"):
        params["return_date"] = return_date
    params["passengers"] = passengers

    query = urlencode(params)
    return f"{base}?{query}&marker={MARKER}"

def build_hotels_search(city):
    return f"https://www.aviasales.com/hotels?search={quote(city)}&marker={MARKER}"

# ================== КЛАВИАТУРА ==================
def main_menu_keyboard():
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    kb.row("✈️ Авиабилеты", "🏨 Отели")
    kb.row("🚄 ЖД билеты", "🚌 Автобусы")
    kb.row("🚗 Аренда авто", "🚕 Трансферы")
    kb.row("🧭 Туры и акции", "🚢 Круизы")
    kb.row("❓ Поддержка")
    return kb

# ================== ПРИВЕТСТВИЕ ==================
@bot.message_handler(commands=['start'])
def cmd_start(m):
    welcome_text = (
        "Привет! 👋\n"
        "Я — Tripora AI, ваш личный помощник в путешествиях.\n"
        "Помогу подобрать авиабилеты, отели, туры, круизы и многое другое.\n\n"
        "Выберите нужный раздел ниже 👇"
    )
    bot.send_message(m.chat.id, welcome_text, reply_markup=main_menu_keyboard())

@bot.message_handler(commands=['menu','help'])
def cmd_menu(m):
    bot.send_message(m.chat.id, "Главное меню:", reply_markup=main_menu_keyboard())

# ================== АВИА ДИАЛОГ ==================
@bot.message_handler(commands=['avia'])
def cmd_avia_start(m):
    bot.send_message(m.chat.id, "Город отправления (IATA или название):")
    user_states[m.chat.id] = {"step": "avia_origin", "data": {}}

# ================== ОТЕЛИ ДИАЛОГ ==================
@bot.message_handler(commands=['hotels'])
def cmd_hotels_start(m):
    bot.send_message(m.chat.id, "Введите город, где хотите найти отель:")
    user_states[m.chat.id] = {"step": "hotels_city", "data": {}}

# ================== ОБРАБОТКА ВСЕХ СООБЩЕНИЙ ==================
@bot.message_handler(func=lambda msg: True)
def all_messages(m):
    cid = m.chat.id
    text = m.text.strip()
    t = text.lower()

    # КНОПКИ МЕНЮ
    if t in ("✈️ авиабилеты","авиабилеты"):
        cmd_avia_start(m); return
    if t in ("🏨 отели","отели"):
        cmd_hotels_start(m); return
    if t in ("❓ поддержка","поддержка"):
        bot.send_message(cid, "Напишите свой вопрос — и мы поможем!"); return
    if t in ("меню","/menu"):
        cmd_menu(m); return

    state = user_states.get(cid)
    if not state:
        bot.send_message(cid, "Выберите пункт меню 👇", reply_markup=main_menu_keyboard())
        return

    step = state["step"]

    # ----------- АВИА ПОШАГОВЫЙ ПОИСК ----------- 
    if step == "avia_origin":
        state["data"]["origin"] = text
        state["step"] = "avia_destination"
        bot.send_message(cid, "Город назначения:")
        return

    if step == "avia_destination":
        state["data"]["destination"] = text
        state["step"] = "avia_depart_date"
        bot.send_message(cid, "Дата вылета (YYYY-MM-DD) или 'any':")
        return

    if step == "avia_depart_date":
        state["data"]["depart_date"] = text
        state["step"] = "avia_return_date"
        bot.send_message(cid, "Дата возврата (YYYY-MM-DD) или 'one':")
        return

    if step == "avia_return_date":
        state["data"]["return_date"] = text
        state["step"] = "avia_passengers"
        bot.send_message(cid, "Количество пассажиров (1-9):")
        return

    if step == "avia_passengers":
        try:
            passengers = int(text)
        except:
            bot.send_message(cid, "Введите число (1–9):")
            return

        state["data"]["passengers"] = passengers
        d = state["data"]

        # Генерируем ссылку
        url = build_aviasales_search(
            origin=d["origin"],
            destination=d["destination"],
            depart_date=d["depart_date"],
            return_date=d["return_date"],
            passengers=d["passengers"]
        )

        kb = telebot.types.InlineKeyboardMarkup()
        kb.add(telebot.types.InlineKeyboardButton("Открыть результаты ✈️", url=url))

        bot.send_message(cid, "Готово! Вот лучшие варианты:", reply_markup=kb)
        user_states.pop(cid, None)
        return

    # ----------- ОТЕЛИ ----------- 
    if step == "hotels_city":
        city = text
        url = build_hotels_search(city)

        kb = telebot.types.InlineKeyboardMarkup()
        kb.add(telebot.types.InlineKeyboardButton("Найти отель 🏨", url=url))

        bot.send_message(cid, f"Поиск отелей в городе: {city}", reply_markup=kb)
        user_states.pop(cid, None)
        return

    # ----------- ОСТАЛЬНОЕ ----------- 
    bot.send_message(cid, "Пожалуйста, выберите пункт меню 👇", reply_markup=main_menu_keyboard())

# ================== ЗАПУСК ==================
def run():
    user_states.clear()
    while True:
        try:
            print("Tripora AI запущен...")
            bot.polling(non_stop=True)
        except Exception as e:
            print("Ошибка:", e)
            time.sleep(3)

if __name__ == "__main__":
    run()
