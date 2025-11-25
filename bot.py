# -*- coding: utf-8 -*-
"""
bot.py — Tripora AI unified simple bot
Поддерживает: авиабилеты, отели, аренду авто, трансферы, ЖД, автобусы, круизы, туры, мои билеты, поддержка.
Подставь BOT_TOKEN в переменные окружения на Render (BOT_TOKEN).
"""
import os
import time
import re
from urllib.parse import quote, urlencode

import telebot
from telebot import types

# ----------------- НАСТРОЙКИ ПАРТНЁРКИ -----------------
MARKER = "685852"        # твой shmarker/marker
TRS = "475152"           # твой trs
# редирект tp.media (если хочешь tpwgt виджет — можно переключить линки ниже)
TP_REDIRECT = "https://tp.media/r"
# tpwgt widget base (альтернатива для универсального виджета)
TPWGT_BASE = "https://tpwgt.com/content"

# Базовые поисковые сайты (можно менять)
AVIASALES_BASE = "https://www.aviasales.com/search"
AVIASALES_RU = "https://www.aviasales.ru/search"
HOTELS_BASE = "https://www.aviasales.com/hotels"
CARS_BASE = "https://www.rentalcars.com/SearchResults.do"  # пример (универсально)
TRAINS_BASE = "https://www.tutu.ru"  # пример для поездов
BUSES_BASE = "https://www.bus.com"   # пример
CRUISES_BASE = "https://www.cruise.example"  # пример-заглушка

# ----------------- TOKEN -----------------
TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN not set in environment variables")

bot = telebot.TeleBot(TOKEN)

# ----------------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ -----------------
EMOJI_PATTERN = re.compile("[\U00010000-\U0010ffff\U0001F300-\U0001F5FF"
                           "\U0001F600-\U0001F64F\U0001F680-\U0001F6FF"
                           "\u2600-\u26FF\u2700-\u27BF]", flags=re.UNICODE)

def normalize_text(s: str) -> str:
    """Убирает эмодзи, лишние пробелы, приводит к lower."""
    if not s:
        return ""
    s = EMOJI_PATTERN.sub("", s)  # удалить эмодзи/символы
    s = s.replace("\uFE0F", "")   # вариационные селекторы
    return re.sub(r"\s+", " ", s).strip().lower()

def affiliate_redirect_for_url(target_url: str) -> str:
    """Собирает tp.media редирект с marker и trs, target_url должен быть полный."""
    # Кодируем цель
    encoded = quote(target_url, safe='')
    return f"{TP_REDIRECT}?marker={MARKER}&trs={TRS}&u={encoded}"

def tpwgt_widget_url(default_tab="plane", extra_params=None):
    """Генерирует tpwgt виджет URL (встраиваемый вариант, можно открыть в браузере)."""
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
        # можно добавить promo_id/campaign_id
    }
    if extra_params:
        params.update(extra_params)
    return TPWGT_BASE + "?" + urlencode(params)

# ----------------- МЕНЮ -----------------
def main_menu_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    kb.add(
        "✈️ Авиабилеты", "🚄 ЖД билеты", "🚌 Автобусы",
        "🏨 Отели", "🚗 Аренда авто", "🚕 Трансферы",
        "🧾 Мои билеты", "🧭 Туры и акции", "🚢 Круизы",
        "❓ Поддержка"
    )
    return kb

# ----------------- СОСТОЯНИЕ ПОЛЬЗОВАТЕЛЯ -----------------
# простая память в процессе: {chat_id: {"step": "...", "data": {...}, "section": "..."}}
user_states = {}

# ----------------- ХЕНДЛЕРЫ КОМАНД -----------------
@bot.message_handler(commands=['start'])
def cmd_start(m):
    text = ("Привет! Я Tripora AI — твой помощник по путешествиям.\n\n"
            "Выбери нужный раздел в меню — я помогу с поиском и дам ссылку на лучшие предложения.")
    bot.send_message(m.chat.id, text, reply_markup=main_menu_keyboard())

@bot.message_handler(commands=['menu','help'])
def cmd_menu(m):
    bot.send_message(m.chat.id, "Главное меню:", reply_markup=main_menu_keyboard())

# Быстрый переход: если ввели "avia" или "авиабилеты" — запускаем старт диалога
def start_avia_flow(m):
    cid = m.chat.id
    user_states[cid] = {"step": "avia_origin", "section": "avia", "data": {}}
    bot.send_message(cid, "Начнём поиск авиабилетов. Введите город отправления (IATA или название):")

def start_hotels_flow(m):
    cid = m.chat.id
    user_states[cid] = {"step": "hotels_city", "section": "hotels", "data": {}}
    bot.send_message(cid, "Поиск отелей. Введите город (например: Almaty или Алматы):")

def start_cars_flow(m):
    cid = m.chat.id
    user_states[cid] = {"step": "cars_city", "section": "cars", "data": {}}
    bot.send_message(cid, "Аренда авто. Введите город (например: Almaty или Алматы):")

def start_transfers_flow(m):
    cid = m.chat.id
    # для трансферов предложим виджет
    url = tpwgt_widget_url(default_tab="plane")
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Открыть поиск трансферов и такси", url=url))
    bot.send_message(cid, "Переход к виджету поиска (трансферы/такси):", reply_markup=kb)

def start_trains_flow(m):
    cid = m.chat.id
    # простая редирект-ссылка на tutu (пример)
    target = TRAINS_BASE
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Поиск ЖД билетов", url=affiliate_redirect_for_url(target)))
    bot.send_message(cid, "Ищу ЖД — откройте ссылку:", reply_markup=kb)

def start_buses_flow(m):
    cid = m.chat.id
    target = BUSES_BASE
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Искать автобусы", url=affiliate_redirect_for_url(target)))
    bot.send_message(cid, "Переход к поиску автобусов:", reply_markup=kb)

def start_cruises_flow(m):
    cid = m.chat.id
    target = CRUISES_BASE
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Искать круизы", url=affiliate_redirect_for_url(target)))
    bot.send_message(cid, "Круизы — откройте ссылку:", reply_markup=kb)

def start_tours_flow(m):
    cid = m.chat.id
    # виджет или внешняя страница — используем tpwgt (вкладка tours не всегда есть, но виджет покажет тут всё)
    url = tpwgt_widget_url(default_tab="plane")
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Поиск туров и акций", url=url))
    bot.send_message(cid, "Туры и акции — откройте виджет:", reply_markup=kb)

def start_my_tickets_flow(m):
    cid = m.chat.id
    bot.send_message(cid, "Мои билеты — пока простой сервис: пришлите ваш номер брони, или воспользуйтесь виджетом.", reply_markup=main_menu_keyboard())

def support_flow(m):
    cid = m.chat.id
    bot.send_message(cid, "Поддержка: напиши свой вопрос, и мы свяжемся с тобой как можно скорее.", reply_markup=main_menu_keyboard())

# ----------------- УНИВЕРСАЛЬНЫЙ ОБРАБОТЧИК СООБЩЕНИЙ -----------------
@bot.message_handler(func=lambda msg: True)
def all_messages(m):
    cid = m.chat.id
    text = (m.text or "").strip()
    norm = normalize_text(text)

    # Если у пользователя уже открыт диалог — обрабатываем шаги
    state = user_states.get(cid)
    if state:
        section = state.get("section")
        step = state.get("step")
        data = state.get("data", {})

        # --- AVIA FLOW ---
        if section == "avia":
            if step == "avia_origin":
                data["origin"] = text
                state["step"] = "avia_destination"
                bot.send_message(cid, "Куда летим? Введите город назначения (IATA или название):")
                return
            if step == "avia_destination":
                data["destination"] = text
                state["step"] = "avia_depart_date"
                bot.send_message(cid, "Дата вылета (YYYY-MM-DD) или 'any' для любого дня:")
                return
            if step == "avia_depart_date":
                data["depart_date"] = text
                state["step"] = "avia_return_date"
                bot.send_message(cid, "Дата возвращения (YYYY-MM-DD) или 'one' / 'без' для без возврата:")
                return
            if step == "avia_return_date":
                data["return_date"] = text
                state["step"] = "avia_passengers"
                bot.send_message(cid, "Сколько пассажиров? Введите число (например: 1):")
                return
            if step == "avia_passengers":
                try:
                    p = int(re.sub(r"\D", "", text) or "1")
                except:
                    bot.send_message(cid, "Нужно число. Попробуйте ещё раз:")
                    return
                data["passengers"] = p
                # Формируем базовую ссылку Aviasales
                params = []
                if data.get("origin"):
                    params.append(data["origin"].replace(" ", ""))
                if data.get("destination"):
                    params.append(data["destination"].replace(" ", ""))
                # Aviasales часто использует path: /search/CityFromYYYYCityTo... но у нас минимум - даём search?q
                # Для совместимости используем query-параметры
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

                # Собираем базовый поисковый URL (используем aviasales.com)
                base_search = AVIASALES_BASE + ("?" + urlencode(query) if query else "")
                affiliate = affiliate_redirect_for_url(base_search)

                kb = types.InlineKeyboardMarkup()
                kb.add(types.InlineKeyboardButton("Открыть лучшие рейсы", url=affiliate))
                bot.send_message(cid, "Готово — откройте поиск по ссылке:", reply_markup=kb)
                user_states.pop(cid, None)
                return

        # --- HOTELS FLOW ---
        if section == "hotels":
            if step == "hotels_city":
                city = text
                # формируем простой URL поиска отелей
                search_url = HOTELS_BASE + ("?search=" + quote(city))
                affiliate = affiliate_redirect_for_url(search_url)
                kb = types.InlineKeyboardMarkup()
                kb.add(types.InlineKeyboardButton("Поиск отелей", url=affiliate))
                bot.send_message(cid, f"Вот ссылка на поиск отелей в «{city}»: ", reply_markup=kb)
                user_states.pop(cid, None)
                return

        # --- CARS FLOW ---
        if section == "cars":
            if step == "cars_city":
                city = text
                # простая редирект ссылка на rentalcars (пример)
                # мы формируем целевой URL с city как параметром поиска (предположение)
                target = CARS_BASE + "?city=" + quote(city)
                affiliate = affiliate_redirect_for_url(target)
                kb = types.InlineKeyboardMarkup()
                kb.add(types.InlineKeyboardButton("Поиск аренды авто", url=affiliate))
                bot.send_message(cid, f"Переход к поиску авто в {city}:", reply_markup=kb)
                user_states.pop(cid, None)
                return

        # Если диалог есть, но не распознали шаг — предложим меню
        bot.send_message(cid, "Не понял шаг. Вернись в меню:", reply_markup=main_menu_keyboard())
        return

    # Если не в состоянии — сопоставляем команды меню (нормализуем вход)
    # Обрабатывать эмодзи и разные варианты
    # Приоритет: точные совпадения по нормализации
    if norm in ("авиабилеты","avia","авиа","аvиа","aviа","авиа билеты","aviabilet"):
        start_avia_flow(m); return
    if norm in ("отели","hotels","отель"):
        start_hotels_flow(m); return
    if norm in ("аренда авто","аренда","cars","аренда автомобиль","арендамаш"):
        start_cars_flow(m); return
    if norm in ("трансферы","такси","transfers","transfer"):
        start_transfers_flow(m); return
    if norm in ("жд билеты","жд","поезд","trains","rail"):
        start_trains_flow(m); return
    if norm in ("автобусы","bus","buses"):
        start_buses_flow(m); return
    if norm in ("круизы","cruise","cruises"):
        start_cruises_flow(m); return
    if norm in ("туры","туры и акции","тур","tours"):
        start_tours_flow(m); return
    if norm in ("мои билеты","билеты","tickets","мой билет"):
        start_my_tickets_flow(m); return
    if norm in ("поддержка","support"):
        support_flow(m); return

    # Также если написали "меню" или незнакомая фраза — показываем меню (и дружелюбно приветствуем)
    if norm in ("menu","меню","start","привет","здравствуйте","hello"):
        bot.send_message(cid, "Привет — выбери пункт в меню, и я помогу.", reply_markup=main_menu_keyboard())
        return

    # Default: подсказка
    bot.send_message(cid, "Нажмите /menu или выберите одну из кнопок в меню.", reply_markup=main_menu_keyboard())

# ----------------- ЗАПУСК -----------------
if __name__ == "__main__":
    user_states.clear()
    # защищаем polling от падений
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print("Polling error:", e)
            time.sleep(5)
