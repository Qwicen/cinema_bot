from deeppavlov import configs, build_model
from deeppavlov import train_model
from deeppavlov.models.slotfill.slotfill import DstcSlotFillingNetwork
from nltk.corpus import stopwords
from gensim.models import Doc2Vec
import pandas as pd
import difflib
import pickle
import re
import datetime

class MoviePlot:
    
    root_path = "models/plot2movie/"
    
    scores = pd.read_csv(root_path + 'df_scores.csv')
    tmdb = pd.read_csv(root_path + 'movieID.csv')
    
    with open(root_path + 'dict_tags.pkl', 'rb') as fin:
            dict_tags = pickle.load(fin)
    
    @staticmethod
    def _text_to_tags(text):
        """ Tranform text to tags. We choose closest tags from the list of
        all tags (if such tags exit).
        """
        all_tags = set()
        text = text.split()
        for word in text:
            match = difflib.get_close_matches(word, MoviePlot.dict_tags, cutoff=0.8)
            all_tags.update(match)
            
        bigramms = [' '.join(x) for x in zip(text[:-1], text[1:])]
        for bigramm in bigramms:
            match = difflib.get_close_matches(bigramm, MoviePlot.dict_tags, cutoff=0.8)
            all_tags.update(match)
        
        return list(all_tags)
    
    @staticmethod
    def _to_df(movies):
        """ Convert list of movies' titles to pf.DataFrame
        """
        
        titles = [t for t in movies]
    
        data = pd.DataFrame()
        for title in titles:
            data = pd.concat([data, MoviePlot.tmdb[MoviePlot.tmdb['title'] == title]])
        try:
            return data[['title', 'imdbId', 'tmdbId']]
        except:
            return data
    
    @staticmethod
    def plot2movie(text, n_matches=10):
        """ Find movies based on matched tags with highest total score.
        
        Parameters
        ----------
        text : str
            A given plot for which we want to find similar movies.
        n_matches : int
            The quantity of matched movies which we want to review for given
            plot descripiton.
                
        Returns
        -------
        df : pd.DataFrame
            DataFrame of movies with shape (n_matches, [title, imdbId, tmdbId])
        """

        tags = MoviePlot._text_to_tags(text)
        
        data = MoviePlot.scores[MoviePlot.scores.tagId.isin(tags)].groupby('movieId').sum()
        data = data[data.relevance > len(tags)*0.5].nlargest(n_matches, 'relevance')
        
        df = MoviePlot._to_df(data.index)
        
        return df

   
class NER:
    config = "./models/ner_config.json"
    ner_model = build_model(config, download=True)

    def train():
        train_model(NER.config, download=True)
        NER.ner_model = build_model(NER.config, download=True)

    def NamedEntityRecognition(message):
        ner = NER.ner_model([message])
        sentence, labels = ner[0][0], ner[1][0]
        print("###NER: ", sentence)
        print("###NER: ", labels)
        entities, slots = DstcSlotFillingNetwork._chunk_finder(sentence, labels)
        s = {}
        for i, slot in enumerate(slots):
            if slot not in s:
                s[slot] = set()
            s[slot].add(entities[i])
        if 'GENRE' in s:
            for genre in s['GENRE']:
                s['GENRE'] = set.union(set(word for word in genre.split() if word not in (stopwords.words('english'))), s['GENRE'])
        return s 

def extract_year(text):
    match = re.search(r'\d{4}', text)
    if match == None and re.search(r'\d{2}', text) != None:
      match = re.search(r'\d{2}', text)
      return '19'+match.group()
    if match == None:
      this_year = datetime.datetime.now().year
      word_dict = {'last': this_year-1, 'this': this_year, 'new': this_year+1}
      for word in word_dict.keys():
        if re.search(word, text) != None:
          return word_dict[word]
      return None
    return match.group()