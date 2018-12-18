# -*- coding: utf-8 -*-

# Пытаемся узнать из базы «состояние» пользователя
def get_current_state(user_id):
    with Vedis(config.db_state) as db:
        try:
            return db[user_id]
        except KeyError:  # Если такого ключа почему-то не оказалось
            return config.States.S_START.value  # значение по умолчанию - начало диалога

# Сохраняем текущее «состояние» пользователя в нашу базу
def set_state(user_id, value):
    with Vedis(config.db_state) as db:
        try:
            db[user_id] = value
            return True
        except:
            # тут желательно как-то обработать ситуацию
            return False

# Записываем запрос по пользователю
def set_user_descr(user_id, description):
    with Vedis(config.db_search) as db:
        try:
            db[user_id] = description
            return True
        except:
            return False

def get_user_descr(user_id, description):
    with Vedis(config.db_search) as db:
        try:
            return db[user_id]
        except KeyError:
            return None

# Записываем фильм, который вернулся по запросу
def set_descr_movie(description, movie):
    with Vedis(config.db_search) as db:
        try:
            db[description] = movie
            return True
        except:
            return False

def get_descr_movie(description, movie):
    with Vedis(config.db_search) as db:
        try:
            return db[description]
        except KeyError:
            return None