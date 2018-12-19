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