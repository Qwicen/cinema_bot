from vedis import Vedis
from enum import Enum

class States(Enum):
    S_START = "0"
    S_SEARCH = "1"
    S_CLARIFY = "2"

    db_state = "db_state.vdb"
    db_search = "db_search.vdb"

# Пытаемся узнать из базы «состояние» пользователя
def get_current_state(user_id):
    with Vedis(States.db_state) as db:
        try:
            return db[user_id].decode()
        except KeyError:
            print("KeyError. There is no user ", user_id, ", returning S_START")
            return States.S_START.value
# Сохраняем текущее «состояние» пользователя в нашу базу
def set_state(user_id, value):
    with Vedis(States.db_state) as db:
        try:
            db[user_id] = value
            return True
        except KeyError:
            print("KeyError. There is no user ", user_id, ", doing nothing")
            return False
# Записываем запрос по пользователю
def save_request(user_id, message_id, films):
    with Vedis(States.db_search) as db:
        try:
            key = str(user_id) + str(message_id)
            db[key] = films
            return True
        except KeyError:
            print("KeyError. There is no user_id-message_id combination")
def get_request(user_id, message_id):
    with Vedis(States.db_search) as db:
        try:
            key = str(user_id) + str(message_id)
            return db[key].decode()
        except KeyError:
            print("KeyError. There is no user_id-message_id combination")