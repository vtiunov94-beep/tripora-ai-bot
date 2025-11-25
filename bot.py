# ----------------- === Простая конфигурация кнопок с ссылками ===
# Вставь сюда свои партнерские ссылки/виджеты (tp.media / tpwgt / aviasales)
# Можно использовать готовые tpwgt ссылки или прямые affiliate tp.media ссылки.
LINKS = {
    "aviа": {  # ключи — произвольные; сделаны для удобства
        "title": "✈️ Авиабилеты",
        # пример: используем tpwgt (виджет) — открывает сразу вкладку plane
        "url": tpwgt_widget_url(default_tab="plane", extra_params={"promo_id":"7879","campaign_id":"100"})
        # либо: "url": affiliate_redirect_for_url("https://www.aviasales.com/search")
    },
    "hotels": {
        "title": "🏨 Отели",
        "url": tpwgt_widget_url(default_tab="hotel", extra_params={"promo_id":"7879","campaign_id":"100"})
    },
    "cars": {
        "title": "🚗 Аренда авто",
        "url": affiliate_redirect_for_url("https://www.rentalcars.com/")
    },
    "transfers": {
        "title": "🚕 Трансферы / Такси",
        "url": tpwgt_widget_url(default_tab="plane", extra_params={"defaultTab":"plane","promo_id":"9093","campaign_id":"45"})
    },
    "trains": {
        "title": "🚄 ЖД билеты",
        "url": affiliate_redirect_for_url("https://www.tutu.ru/")
    },
    "buses": {
        "title": "🚌 Автобусы",
        "url": affiliate_redirect_for_url("https://www.bus.com/")
    },
    "cruise": {
        "title": "🚢 Круизы",
        "url": affiliate_redirect_for_url("https://www.cruise.example/")
    },
    "tours": {
        "title": "🧭 Туры и акции",
        "url": tpwgt_widget_url(default_tab="plane")
    },
    "mytickets": {
        "title": "🧾 Мои билеты",
        "url": tpwgt_widget_url(default_tab="plane")
    },
    "support": {
        "title": "❓ Поддержка",
        "url": "https://t.me/your_support_chat"  # или почта/форма
    }
}

# ----------------- Утилита — клавиатура с кнопками (Inline) -----------------
def menu_links_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    # берем порядок через список ключей, можно настроить порядок вручную:
    order = ["aviа","trains","buses","hotels","cars","transfers","mytickets","tours","cruise","support"]
    for key in order:
        if key in LINKS:
            v = LINKS[key]
            # каждая кнопка открывает внешнюю ссылку
            buttons.append(types.InlineKeyboardButton(v["title"], url=v["url"]))
    # добавляем все кнопки в разметке (row_width задаёт кол-во в ряду)
    kb.add(*buttons)
    return kb

# ----------------- Хендлер: /menu либо когда нужно показать "кнопки-ссылки" -------------
@bot.message_handler(commands=['menu','links'])
def send_menu_links(m):
    cid = m.chat.id
    text = "Выбирай сервис — нажми кнопку, чтобы открыть поиск/виджет:"
    bot.send_message(cid, text, reply_markup=menu_links_keyboard())

# ----------------- Простой fallback для клавиш ReplyKeyboard (старое меню) -------------
# Если у тебя есть обычные ReplyKeyboard кнопки (как было), то при клике на них можно
# перенаправлять на соответствующую ссылку:
@bot.message_handler(func=lambda msg: normalize_text(msg.text) in ("✈️ авиабилеты","авиабилеты","avia","авиа"))
def reply_to_avia_button(m):
    v = LINKS.get("aviа")
    if v:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("Открыть поиск авиабилетов", url=v["url"]))
        bot.send_message(m.chat.id, "Открываю поиск авиабилетов:", reply_markup=kb)
    else:
        bot.send_message(m.chat.id, "Ссылка не настроена.")

# Аналогично можно добавить быстрые хендлеры для "Отели", "Аренда авто" и т.д.
