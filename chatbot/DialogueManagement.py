import requests
import pickle
from vedis import Vedis
from enum import Enum

class States(Enum):
    S_START = "0"
    S_SEARCH = "1"
    S_CLARIFY = "2"

    db_state = "data/db_state.vdb"
    db_search = "data/db_search.vdb"
    db_page = "data/db_page.vdb"

    R_OK = 0
    R_CLARIFY_GENRE = 1
    R_CLARIFY_ALL = 2

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
# Записываем результат пользовательского запроса
def save_request(user_id, message_id, films):
    with Vedis(States.db_search) as db:
        try:
            key = str(user_id) + str(message_id)
            db[key] = films
            return True
        except KeyError:
            print("KeyError. There is no user_id-message_id combination")
# Получаем результат пользовательского запроса
def get_request(user_id, message_id):
    with Vedis(States.db_search) as db:
        try:
            key = str(user_id) + str(message_id)
            return db[key].decode()
        except KeyError:
            print("KeyError. There is no user_id-message_id combination")

def save_page(user_id, message_id, page):
    with Vedis(States.db_page) as db:
        try:
            key = str(user_id) + str(message_id)
            db[key] = str(page)
            print("Saved page with key: " + key)
            return True
        except KeyError:
            print("KeyError in save_page. There is no user_id-message_id combination: " + key)

def get_page(user_id, message_id):
    with Vedis(States.db_page) as db:
        try:
            key = str(user_id) + str(message_id)
            return int(db[key].decode())
        except KeyError:
            print("KeyError in get_page. There is no user_id-message_id combination: " + key)

class ApiDicts:
    with open('data/api_dicts/genre_to_id.pickle', 'rb') as f:
        genre_to_id = pickle.load(f)

    with open('data/api_dicts/movie_to_id.pickle', 'rb') as f:
        movie_to_id = pickle.load(f)

    with open('data/api_dicts/person_to_id.pickle', 'rb') as f:
        movie_to_id = pickle.load(f)
    
def api_discover(api_key, genres=None, people=None, actors=None, crew=None, year=None):
    url = "https://api.themoviedb.org/3/discover/movie"
    payload = { 'api_key': api_key,
                'with_genres': genres,
                'with_people': people,
                'with_cast': actors,
                'with_crew': crew,
                'year': year,
                'sort_by': 'vote_average.desc'}
    response = requests.request('GET', url, data=payload)
    return response.text
