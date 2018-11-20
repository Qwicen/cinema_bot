import logging
import time
import flask
import telebot

from config import API_TOKEN
from config import WEBHOOK_SSL_CERT
from config import WEBHOOK_URL_BASE
from config import WEBHOOK_URL_PATH

from chatbot import NaturalLanguageUnderstanding as NLU

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)
bot = telebot.TeleBot(API_TOKEN, threaded=False)
app = flask.Flask(__name__)

@app.route('/', methods=['GET', 'HEAD'])
def index():
    return ''

@app.route(WEBHOOK_URL_PATH, methods=['POST'])
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
    bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                    certificate=open(WEBHOOK_SSL_CERT, 'r'))
    return ''

@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message, "Hello, " + message.from_user.first_name)

@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
    msg_split, ner = NLU.NamedEntityRecognition(message.text)
    bot.send_message(message.chat.id, msg_split[0])

if __name__ == "__main__":
    app.run()
