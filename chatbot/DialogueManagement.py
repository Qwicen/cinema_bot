# -*- coding: utf-8 -*-

from vedis import Vedis
import telebot
import config
import dbworker

bot = telebot.TeleBot(config.token)

# Начало диалога
@bot.message_handler(commands=["start"])
def cmd_start(message):
    bot.send_message(message.chat.id, "Please desctribe the movie you would like me to find")
    dbworker.set_state(message.chat.id, config.States.S_SEARCH.value)


# По команде /reset будем сбрасывать состояния, возвращаясь к началу диалога
@bot.message_handler(commands=["reset"])
def cmd_reset(message):
    bot.send_message(message.chat.id, "Starting over. Please write the movie desctiption")
    dbworker.set_state(message.chat.id, config.States.S_ENTER_NAME.value)

@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_SEARCH.value)
def user_entering_descкiption(message):
    # Если не удалось найти фильм (или другое условие, по которому мы просим уточнить описание)
    if """ Nothing was found """:
        # Состояние не меняем, просим уточнить
        bot.send_message(message.chat.id, "Please be more spectific with the description")
        return
    else:
        # Если получили положительный результат
        bot.send_message(message.chat.id, "I found something for you, hope you'll like it")
        dbworker.set_state(message.chat.id, config.States.S_RESULT.value)


@bot.message_handler(func= lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_RESULT.value)
def user_sending_photo(message):
    # Здесь выводим результат
    bot.send_message(message.chat.id, "Here you go! **RESULT** If you want to try some other description, just type in /start")
    dbworker.set_state(message.chat.id, config.States.S_START.value)


if __name__ == "__main__":
    bot.polling(none_stop=True)