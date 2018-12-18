from vedis import Vedis

class States:
    S_START = "0"
    S_SEARCH = "1"
    S_RESULT = "2"

    db_state = "db_state.vdb"
    db_search = "db_search.vdb"

    # Пытаемся узнать из базы «состояние» пользователя
    @staticmethod
    def get_current_state(user_id):
        with Vedis(States.db_state) as db:
            try:
                return db[user_id]
            except KeyError:  # Если такого ключа почему-то не оказалось
                return States.S_START.value  # значение по умолчанию - начало диалога

    # Сохраняем текущее «состояние» пользователя в нашу базу
    @staticmethod
    def set_state(user_id, value):
        with Vedis(States.db_state) as db:
            try:
                db[user_id] = value
                return True
            except:
                # тут желательно как-то обработать ситуацию
                return False

    # Записываем запрос по пользователю
    @staticmethod
    def set_user_descr(user_id, description):
        with Vedis(States.db_search) as db:
            try:
                db[user_id] = description
                return True
            except:
                return False

    @staticmethod
    def get_user_descr(user_id, description):
        with Vedis(States.db_search) as db:
            try:
                return db[user_id]
            except KeyError:
                return None

    # Записываем фильм, который вернулся по запросу
    @staticmethod
    def set_descr_movie(description, movie):
        with Vedis(States.db_search) as db:
            try:
                db[description] = movie
                return True
            except:
                return False

    @staticmethod
    def get_descr_movie(description, movie):
        with Vedis(States.db_search) as db:
            try:
                return db[description]
            except KeyError:
                return None