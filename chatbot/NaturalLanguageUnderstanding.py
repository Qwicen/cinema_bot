from deeppavlov import configs, build_model
from deeppavlov import train_model
from deeppavlov.models.slotfill.slotfill import DstcSlotFillingNetwork
import pandas as pd
from gensim.models import Doc2Vec
import pickle


class MoviePlot:
    
    root_path = "models/plot2movie/"
    
    model = Doc2Vec.load(root_path + 'doc2vec_tags_50')
    df = pd.read_csv('data/df_tags.csv')
        
    with open(root_path + 'set_of_tags.pkl', 'rb') as fin:
        tags = pickle.load(fin)
    
    
    def _tokenizer(self, text):
        """ Leave only words key words in description which among set_of_tags
        """
        
        tokens = []
        
        for w in text.split():
            if w in self.tags:
                tokens.append(w)
                
        return tokens
    
    
    def _to_df(self, movies):
        """ Convert list of movies' titles to pf.DataFrame
        """
        
        titles = [t for t, _ in movies]
    
        data = pd.DataFrame()
        for title in titles:
            data = pd.concat([data, self.df[self.df['title'] == title]])
        
        print(data.columns.tolist())
        return data[['title', 'imdbId', 'tmdbId']]
    
    
    def plot2movie(self, text, n_matches=10):
        """ Find movies based on doc2vec model which are close
        (using cosine similarity) to the given discription.
        
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
        
        text_tok = self._tokenizer(text)
        
        pred = self.model.infer_vector(text_tok)
        movies = self.model.docvecs.most_similar([pred], topn = n_matches)
        
        return self._to_df(movies)   

class NER:
    config = "./models/ner_config.json"
    ner_model = build_model(config, download=True)

    def train():
        train_model(NER.config, download=True)
        NER.ner_model = build_model(NER.config, download=True)

    def NamedEntityRecognition(message):
        ner = NER.ner_model([message])
        sentence, labels = ner[0][0], ner[1][0]
        entities, slots = DstcSlotFillingNetwork._chunk_finder(sentence, labels)
        s = {}
        for i, slot in enumerate(slots):
            if slot not in s:
                s[slot] = []
            s[slot].append(entities[i])
        return s 
