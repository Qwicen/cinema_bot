import logging
import time
import flask
import telebot
import pandas as pd

import config
import chatbot.DialogueManagement as dm
from chatbot.NaturalLanguageUnderstanding import MoviePlot

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)
bot = telebot.TeleBot(config.API_TOKEN, threaded=False)
app = flask.Flask(__name__)

@app.route('/', methods=['GET', 'HEAD'])
def index():
    return ''

@app.route(config.WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)

@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    bot.remove_webhook()
    time.sleep(0.1)
    bot.set_webhook(url=config.WEBHOOK_URL_BASE + config.WEBHOOK_URL_PATH,
                    certificate=open(config.WEBHOOK_SSL_CERT, 'r'))
    return ''

# Начало диалога
@bot.message_handler(commands=["start"])
def cmd_start(message):
    bot.send_message(message.chat.id, "Hello, " + message.from_user.first_name)
    bot.send_message(message.chat.id, "Please desctribe the movie you would like me to find")
    dm.set_state(message.chat.id, dm.States.S_SEARCH.value)

@bot.message_handler(commands=['help'])
def cmd_help(message):
    bot.send_message(message, "TODO")

@bot.message_handler(func=lambda message: dm.get_current_state(message.chat.id) == dm.States.S_SEARCH.value)
def user_entering_description(message):
    logger.debug("user_entering_description, message: " + message.text)
    if int(time.time()) % 2 == 0:
        # Если не удалось найти фильм (или другое условие, по которому мы просим уточнить описание)
        bot.send_message(message.chat.id, "Please be more spectific with the description")
        dm.set_state(message.chat.id, dm.States.S_CLARIFY.value)
    else:
        # Если получили положительный результат, состояние не меняем
        bot.send_message(message.chat.id, "I found something for you, hope you'll like it")

@bot.message_handler(func= lambda message: dm.get_current_state(message.chat.id) == dm.States.S_CLARIFY.value)
def user_clarifying(message):
    logger.debug("user_clarifying, message: " + message.txt)
    if int(time.time()) % 2 == 0:
        # если не получили уточнения, не меняем состояние
        bot.send_message(message.chat.id, "Please be more spectific with the description")
    else:
        # Если получили положительный результат
        bot.send_message(message.chat.id, "I found something for you, hope you'll like it")
        dm.set_state(message.chat.id, dm.States.S_SEARCH.value)

if __name__ == "__main__":
    app.run()
