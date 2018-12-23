import requests
import pickle
import numpy as np
from vedis import Vedis
from enum import Enum
from deeppavlov.models.slotfill.slotfill_raw import SlotFillingComponent

class States(Enum):
    S_START = "0"
    S_SEARCH = "1"
    S_CLARIFY = "2"

    db_state = "data/db_state.vdb"
    db_search = "data/db_search.vdb"
    db_page = "data/db_page.vdb"

    R_OK = 0
    R_CLARIFY_GENRE = 1
    R_CLARIFY_ACTOR = 2
    R_CLARIFY_ALL = 3
    R_DONE = 4
    R_NONE = 5

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

    genre_to_id = pickle.load(open('data/api_dicts/genre_to_id.pickle', 'rb'))
    movie_to_id = pickle.load(open('data/api_dicts/movie_to_id.pickle', 'rb'))
    person_to_id = pickle.load(open('data/api_dicts/person_to_id.pickle', 'rb'))

def api_discover(api_key, genres=[], people=[], actors=[], crew=[], year=None, keywords=[]):
    url = "https://api.themoviedb.org/3/discover/movie"
    query = "?api_key={}&with_genres={}&with_people={}&with_cast={}&with_crew={}&primary_release_year={}&sort_by=vote_average.desc".format(
        api_key, ",".join(map(str, genres)), ",".join(map(str, people)), ",".join(map(str, actors)), ",".join(map(str, crew)), year
    )
    print(query)
    payload = { 'with_keywords': keywords }
    response = requests.request('GET', url + query, data=payload)
    return response.text

def api_movie(api_key, movie_ids):
    base_url = "https://api.themoviedb.org/3/movie/"
    payload = { 'api_key': api_key }
    descriptions = []
    for idx in movie_ids:
        url = base_url + str(idx)
        response = requests.request('GET', url, data=payload)
        descriptions.append(response.text)
    return "{ \"results\": [ " + ", ".join(descriptions) + " ], \"total_results\": {}}}".format(movie_ids.shape[0])

def api_search_keyword(api_key, keyword):
    url = "https://api.themoviedb.org/3/search/keyword"
    query = "?api_key={}&query={}".format(api_key, keyword)
    response = requests.request('GET', url + query)
    if response.json()['total_results'] == 0:
        return None
    else:
        result = set()
        for keyword in response.json()['results']:
            result.add(keyword['id'])
        return result
    
def find_levenshtein_closest(candidate, real):
    d = [SlotFillingComponent.fuzzy_substring_distance(candidate, x) for x in real]
    d = np.array(d)
    if np.min(d[:,0]) >= 4:
        return False
    else:
        closest = real[np.argmin(d[:,0])]
        print("Closest genre to ", candidate, " is ", closest, ". dist = ", np.min(d[:,0]))
        return closest