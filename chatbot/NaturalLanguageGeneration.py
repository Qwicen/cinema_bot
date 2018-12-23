from random import randint

initial_phrases = ['Could you please', 'Could you', 'Maybe, you could', 'Excuse me, could you', 'I would be thankful if you could', 'Please,']
verbs = ['say', 'determine', 'define', 'inform me about', 'let me know', 'tell me', 'write', 'enter']
first_part = [ip+' '+verb for ip in initial_phrases for verb in verbs]
first_part += ['I would like to know', 'I need to know', 'It would be helpful to know']
genre_part = ['its genre', 'the genre of the movie', 'the film genre']
actor_part = ['the name of one of the actors','one of the actors', 'any actor from the cast', 'any actor that played there']
year_part = ['the year in which the movie was released', 'the year when the film appeared']
name_part = ['the film name', 'the name of the movie', 'its name', 'what is its name', 'the information about how is it called']

def specifyGenre():
  return first_part[randint(0, len(first_part)-1)]+' '+genre_part[randint(0, len(genre_part)-1)]

def specifyActor():
  return first_part[randint(0, len(first_part)-1)]+' '+actor_part[randint(0, len(actor_part)-1)]

def specifyYear():
  return first_part[randint(0, len(first_part)-1)]+' '+year_part[randint(0, len(year_part)-1)]

def specifyName():
  return first_part[randint(0, len(first_part)-1)]+' '+name_part[randint(0, len(name_part)-1)]

def generateMarkdownMessage(film, page):
    response = \
"""*[{0}] {1}*
_rating_: {2}
_popularity_: {3}
_release_: {4}
[Look at The Movie DB]({5})""".format(
    page, 
    film['title'], 
    film['vote_average'], 
    round(film['popularity'],1), 
    film['release_date'], 
    "https://www.themoviedb.org/movie/" + str(film['id'])
    )
    return response