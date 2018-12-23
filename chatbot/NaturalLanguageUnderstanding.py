from deeppavlov import configs, build_model
from deeppavlov import train_model
import pandas as pd
import difflib
import pickle


class MoviePlot:
    
    root_path = "models/plot2movie/"
    
    scores = pd.read_csv(root_path + 'weights/df_scores.csv')
    tmdb = pd.read_csv(root_path + 'movieID.csv')
    
    with open(root_path + 'dict_tags.pkl', 'rb') as fin:
            dict_tags = pickle.load(fin)
    
    
    def _text_to_tags(self, text):
        """ Tranform text to tags. We choose closest tags from the list of
        all tags (if such tags exit).
        """
        
        all_tags = set()
        
        text = text.split()
        for word in text:
            match = difflib.get_close_matches(word, self.dict_tags, cutoff=0.8)
            all_tags.update(match)
            
        bigramms = [' '.join(x) for x in zip(text[:-1], text[1:])]
        for bigramm in bigramms:
            match = difflib.get_close_matches(bigramm, self.dict_tags, cutoff=0.8)
            all_tags.update(match)
        
        return list(all_tags)
    
    
    def _to_df(self, movies):
        """ Convert list of movies' titles to pf.DataFrame
        """
        
        titles = [t for t in movies]
    
        data = pd.DataFrame()
        for title in titles:
            data = pd.concat([data, self.tmdb[self.tmdb['title'] == title]])
            
        return data[['title', 'imdbId', 'tmdbId']]
    
    
    def plot2movie(self, text, n_matches=10):
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
        
        tags = self._text_to_tags(text)
        
        data = self.scores[self.scores.tagId.isin(tags)].groupby('movieId').sum()
        data = data.nlargest(n_matches, 'relevance')
        
        df = self._to_df(data.index)
        
        return df
   
      
class NER:
    config = "./models/ner_config.json"
    ner_model = build_model(config, download=True)

    def train():
        train_model(NER.config, download=True)
        NER.ner_model = build_model(NER.config, download=True)

    def NamedEntityRecognition(message):
        ner = NER.ner_model([message])
        return ner[0][0], ner[1][0]
