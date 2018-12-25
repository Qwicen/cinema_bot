import os
import logging
import time
import json
import telebot
import pandas as pd

import config
import chatbot.DialogueManagement as dm
import chatbot.NaturalLanguageGeneration as nlg
import chatbot.NaturalLanguageUnderstanding as nlu
logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)
bot = telebot.TeleBot(config.TG_API_TOKEN)

# Начало диалога
@bot.message_handler(commands=["start"])
def cmd_start(message):
    Slots[message.chat.id] = {}
    bot.send_message(message.chat.id, "Hello, " + message.from_user.first_name)
    bot.send_message(message.chat.id, "Please describe the movie you would like me to find")

@bot.message_handler(commands=['help'])
def cmd_help(message):
    bot.send_message(message, "TODO")

@bot.message_handler(func=lambda message: True)
def user_entering_description(message):
    logger.info(message.from_user.first_name)
    logger.info(message.text)
    decision, message_counter = pipeline(message)
    print("decision on message: " + message.text, decision)
    if decision == dm.States.R_OK.value:
        Slots[message.chat.id] = {}
        films = json.loads(dm.get_request(message.chat.id, message.message_id + message_counter))
        response = nlg.generateMarkdownMessage(films['results'][0], page=1)
        bot.send_message(message.chat.id, "I found something for you, hope you'll like it")
        bot.send_message(message.chat.id, response, 
                    disable_notification=True, reply_markup=get_markup(), parse_mode='Markdown')
    elif decision == dm.States.R_CLARIFY_GENRE.value:
        bot.send_message(message.chat.id, nlg.specifyGenre())
    elif decision == dm.States.R_CLARIFY_ACTOR.value:
        bot.send_message(message.chat.id, nlg.specifyActor())
    elif decision == dm.States.R_CLARIFY_ALL.value:
        bot.send_message(message.chat.id, "Sorry, I don’t understand")
        bot.send_message(message.chat.id, "Please be more specific with the description")
    elif decision == dm.States.R_DONE.value:
        pass
    elif decision == dm.States.R_NONE.value:
        Slots[message.chat.id] = {}
        bot.send_message(message.chat.id, "I can not find anything for you.")

def pipeline(message):
    # NER
    message_counter = 2
    slots = nlu.NER.NamedEntityRecognition(message.text)
    if message.chat.id in Slots:
        for slot in slots:
            if slot in Slots[message.chat.id]:
                Slots[message.chat.id][slot] = set.union(slots[slot], Slots[message.chat.id][slot])
            else:
                Slots[message.chat.id][slot] = slots[slot]
    else:
        Slots[message.chat.id] = slots
    logger.info("###SLOTS###")
    logger.info(Slots)
    # Clarifyings
    if len(Slots[message.chat.id]) == 0:
        return dm.States.R_CLARIFY_ALL.value, message_counter
    if len(Slots[message.chat.id]) == 1:
        if 'ACTOR' in Slots[message.chat.id]:
            return dm.States.R_CLARIFY_GENRE.value, message_counter
    # Processing Plot
    keywords_id = set()
    if 'PLOT' in Slots[message.chat.id]:
        n_matches = 5
        plot = " ".join(Slots[message.chat.id]['PLOT'])
        df = nlu.MoviePlot.plot2movie(plot, n_matches=n_matches)
        max_page = n_matches if df.shape[0] >= n_matches else df.shape[0]
        if max_page != 0:
            films = dm.api_movie(config.DB_API_TOKEN, df['tmdbId'].iloc[:max_page].values)
            dm.save_request(message.chat.id, message.message_id + message_counter, films)
            dm.save_page(message.chat.id, message.message_id + message_counter, page=1)
            return dm.States.R_OK.value, message_counter
        else:
            for word in plot.split()[:5]:
                if add_keywords(message.chat.id, word):
                    keywords_id = Slots[message.chat.id]['KEYWORDS']

    # If plot gives no result
    actors_id = []; genres_id = []; director_id = []; year=None
    if 'GENRE' in Slots[message.chat.id]:
        for genre in Slots[message.chat.id]['GENRE']:
            closest = dm.find_levenshtein_closest(genre, list(dm.ApiDicts.genre_to_id.keys()))
            if closest == False:
                if add_keywords(message.chat.id, genre):
                    keywords_id = Slots[message.chat.id]['KEYWORDS']
            else:
                genres_id.append(dm.ApiDicts.genre_to_id[closest])
        if len(genres_id) == 0 and len(list(keywords_id)) == 0:
            return dm.States.R_CLARIFY_GENRE.value, message_counter
    if 'ACTOR' in Slots[message.chat.id]:
        for actor in Slots[message.chat.id]['ACTOR'].copy():
            if actor.lower() in dm.ApiDicts.person_to_id:
                actors_id.append(dm.ApiDicts.person_to_id[actor.lower()][0])
            else:
                message_counter += 1
                bot.send_message(message.chat.id, "I don’t know who is " + actor + ". Please, check spelling.")
                Slots[message.chat.id]['ACTOR'].remove(actor)
        if len(actors_id) == 0:        
            return dm.States.R_CLARIFY_ACTOR.value, message_counter

    if 'DIRECTOR' in Slots[message.chat.id]:
        for director in Slots[message.chat.id]['DIRECTOR'].copy():
            if director.lower() in dm.ApiDicts.person_to_id:
                director_id.append(dm.ApiDicts.person_to_id[director.lower()][0])
            else:
                message_counter += 1
                bot.send_message(message.chat.id, "I don’t know who is " + director + ". Please, check spelling.")
                Slots[message.chat.id]['DIRECTOR'].remove(director)

    if 'YEAR' in Slots[message.chat.id]:
        year = str(nlu.extract_year(Slots[message.chat.id]['YEAR'].pop()))
        print("parsed year: ", year)
    if len(genres_id + actors_id + director_id + list(keywords_id)) != 0 or year != None:
        print("Call API with genres=", genres_id, " and actors=", actors_id, " and directors=", director_id)
        films = dm.api_discover(config.DB_API_TOKEN, genres=genres_id, actors=actors_id, crew=director_id, keywords=keywords_id, year=year)
        if json.loads(films)["total_results"] == 0:
            return dm.States.R_NONE.value, message_counter
        else:
            dm.save_request(message.chat.id, message.message_id + message_counter, films)
            dm.save_page(message.chat.id, message.message_id + message_counter, page=1)
            return dm.States.R_OK.value, message_counter
    else:
        return dm.States.R_NONE.value, message_counter

    
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    current_page = dm.get_page(call.message.chat.id, call.message.message_id)
    films = json.loads(dm.get_request(call.message.chat.id, call.message.message_id))
    max_page = 5 if films["total_results"] > 5 else films["total_results"]
    new_page = current_page
    if call.data == "back":
        if current_page != 1:
            response = nlg.generateMarkdownMessage(films['results'][current_page - 2], page=current_page - 1)
            edit_message(response, call.message.chat.id, call.message.message_id, current_page - 1)
    elif call.data == "next":
        if current_page != max_page:
            response = nlg.generateMarkdownMessage(films['results'][current_page], page=current_page + 1)
            edit_message(response, call.message.chat.id, call.message.message_id, current_page + 1)
    bot.answer_callback_query(callback_query_id=call.id)
        
def edit_message(response, chat, message, page):
    dm.save_page(chat, message, page)
    bot.edit_message_text(response, chat, message, reply_markup=get_markup(), parse_mode='Markdown')

def get_markup():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(telebot.types.InlineKeyboardButton("Back", callback_data=f"back"),
               telebot.types.InlineKeyboardButton("Next", callback_data=f"next"))
    return markup

def add_keywords(chat, keyword):
    keywords = dm.api_search_keyword(config.DB_API_TOKEN, keyword)
    if keywords != None:
        if 'KEYWORDS' in Slots[chat]:
            if len(Slots[chat]['KEYWORDS']) < 10:
                Slots[chat]['KEYWORDS'] = set.union(keywords, Slots[chat]['KEYWORDS'])
        else:
            Slots[chat]['KEYWORDS'] = keywords
        return True
    else:
        return False


if __name__ == "__main__":
    Slots = {}
    bot.polling(none_stop=True)
