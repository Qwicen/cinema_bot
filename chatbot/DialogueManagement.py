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
            return db[user_id]
        except KeyError:
            print("KeyError. There is not user ", user_id, ", returning S_START")
            return States.S_START.value
# Сохраняем текущее «состояние» пользователя в нашу базу
def set_state(user_id, value):
    with Vedis(States.db_state) as db:
        try:
            db[user_id] = value
            return True
        except KeyError:
            print("KeyError. There is not user ", user_id, ", doing nothing")
            return False
# Записываем запрос по пользователю
def set_user_descr(user_id, description):
    with Vedis(States.db_search) as db:
        try:
            db[user_id] = description
            return True
        except KeyError:
            print("KeyError. There is not user ", user_id, ", doing nothing")
def get_user_descr(user_id, description):
    with Vedis(States.db_search) as db:
        try:
            return db[user_id]
        except KeyError:
            print("KeyError. There is not user ", user_id, ", doing nothing")
# Записываем фильм, который вернулся по запросу
def set_descr_movie(description, movie):
    with Vedis(States.db_search) as db:
        try:
            db[description] = movie
            return True
        except KeyError:
            print("KeyError. There is not description ", description, ", doing nothing")
            return False
def get_descr_movie(description, movie):
    with Vedis(States.db_search) as db:
        try:
            return db[description]
        except KeyError:
            print("KeyError. There is not description ", description, ", doing nothing")

if __name__ == "__main__":
    print(get_current_state(0))
    set_state(0, States.S_SEARCH.value)
    print(get_current_state(0))