import logging
import time
import json
import flask
import telebot
import pandas as pd

import config
import chatbot.DialogueManagement as dm
import chatbot.NaturalLanguageGeneration as nlg
from chatbot.NaturalLanguageUnderstanding import MoviePlot
from chatbot.NaturalLanguageUnderstanding import NER

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)
bot = telebot.TeleBot(config.TG_API_TOKEN, threaded=False)
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
    bot.send_message(message.chat.id, "Please describe the movie you would like me to find")
    dm.set_state(message.chat.id, dm.States.S_SEARCH.value)

@bot.message_handler(commands=['help'])
def cmd_help(message):
    bot.send_message(message, "TODO")

@bot.message_handler(func=lambda message: dm.get_current_state(message.chat.id) == dm.States.S_SEARCH.value)
def user_entering_description(message):
    logger.debug("user_entering_description, message: " + message.text)
    decision = pipeline(message, clarifying=False)
    if decision == dm.States.R_OK:
        films = json.loads(dm.get_request(message.chat.id, message.message_id + 2))
        response = nlg.generateMarkdownMessage(films['results'][0], page=1)
        bot.send_message(message.chat.id, "I found something for you, hope you'll like it")
        bot.send_message(message.chat.id, response, 
                    disable_notification=True, reply_markup=get_markup(), parse_mode='Markdown')
    elif decision == dm.States.R_CLARIFY_GENRE:
        nlg.specifyGenre()
        dm.set_state(message.chat.id, dm.States.S_CLARIFY.value)
    elif decision == dm.States.R_CLARIFY_ALL:
        bot.send_message(message.chat.id, "Sorry, I don’t understand")
        bot.send_message(message.chat.id, "Please be more spectific with the description")
        dm.set_state(message.chat.id, dm.States.S_SEARCH.value)

@bot.message_handler(func= lambda message: dm.get_current_state(message.chat.id) == dm.States.S_CLARIFY.value)
def user_clarifying(message):
    logger.debug("user_clarifying, message: " + message.text)
    decision = pipeline(message, clarifying=True)
    logger.debug("decision on message: " + message.text)
    print(decision)
    if decision == dm.States.R_OK:
        films = json.loads(dm.get_request(message.chat.id, message.message_id + 2))
        response = nlg.generateMarkdownMessage(films['results'][0], page=1)
        bot.send_message(message.chat.id, "I found something for you, hope you'll like it")
        bot.send_message(message.chat.id, response, 
                    disable_notification=True, reply_markup=get_markup(), parse_mode='Markdown')
    elif decision == dm.States.R_CLARIFY_GENRE:
        nlg.specifyGenre()
        dm.set_state(message.chat.id, dm.States.S_CLARIFY.value)
    elif decision == dm.States.R_CLARIFY_ALL:
        bot.send_message(message.chat.id, "Sorry, I don’t understand")
        bot.send_message(message.chat.id, "Please be more spectific with the description")
        dm.set_state(message.chat.id, dm.States.S_SEARCH.value)

def pipeline(message, clarifying=False):
    slots = NER.NamedEntityRecognition(message.text)
    print("###SLOTS_BEFORE_UNITING###", slots)
    if clarifying:
        s = dm.get_current_slots(message.chat.id)
        for slot in s:
            if slot in slots:
                slots[slot] = set.union(slots[slot], s[slot])
    print("###SLOTS###", slots)
    if len(slots) == 0:
        return dm.States.R_CLARIFY_ALL
    if len(slots) == 1:
        if 'ACTOR' in slots:
            dm.set_slots(message.chat.id, slots)
            return dm.States.R_CLARIFY_GENRE


    if 'GENRE' in slots:
        genres_id = [dm.find_levenshtein_closest(genre, list(dm.ApiDicts.genre_to_id.keys())) for genre in slots['GENRE']]
        genres_id = [dm.ApiDicts.genre_to_id[genre] for genre in genres_id]

    if 'ACTOR' in slots:
        actors_id = [dm.find_levenshtein_closest(actor, list(dm.ApiDicts.person_to_id.keys())) for actor in slots['ACTOR']]
        actors_id = [dm.ApiDicts.person_to_id[actor] for actor in actors_id]

    # Все нашли
    if 'PLOT' in slots:
        plot = slots['PLOT']
        df = MoviePlot.plot2movie(plot, n_matches=10)
        print("!!!!!!!!!!!!", df['TITLE'][0])

    else:
        films = dm.api_discover(config.DB_API_TOKEN, genres=genres_id, actors=actors_id)
        # Target message will be shifted by two : user_msg, found_msg, target_msg
        dm.save_request(message.chat.id, message.message_id + 2, films)
        dm.save_page(message.chat.id, message.message_id + 2, page=1)
    return dm.States.R_OK
    

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    current_page = dm.get_page(call.message.chat.id, call.message.message_id)
    new_page = current_page
    if call.data == "back":
        if current_page != 1:
            new_page -= 1
    elif call.data == "next":
        if current_page != 3:
            new_page += 1

    if current_page != new_page:
        dm.save_page(call.message.chat.id, call.message.message_id, new_page)
        films = json.loads(dm.get_request(call.message.chat.id, call.message.message_id))
        response = nlg.generateMarkdownMessage(films['results'][new_page - 1], page=new_page)
        bot.edit_message_text(response, call.message.chat.id, call.message.message_id,
                              reply_markup=get_markup(), parse_mode='Markdown')

def get_markup():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(telebot.types.InlineKeyboardButton("Back", callback_data=f"back"),
               telebot.types.InlineKeyboardButton("Next", callback_data=f"next"))
    return markup

if __name__ == "__main__":
    app.run()
