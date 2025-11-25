import telebot
import os

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет! Я Tripora AI бот :)")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "Я с тобой! Пиши :)")

bot.polling(non_stop=True)
