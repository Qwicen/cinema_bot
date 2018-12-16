from deeppavlov import configs, build_model
from deeppavlov import train_model
import pandas as pd
import numpy as np
import nltk
from nltk.corpus import stopwords
from gensim.models import Doc2Vec
import pickle

class MoviePlot:
    
    root_path = "models/plot2movie"
    
    # keep movies's plots
    df = pd.read_csv(root_path + 'wiki_movie_plots_deduped.csv')
    df['Title'] = df['Title'] + ' - ' + df['Release Year'].astype(str) + ' - ' + df['Director']
    df = df[['Title', 'Plot']]
    
    # load models
    model_long = Doc2Vec.load(root_path + 'doc2vec_movie_long')
    model_short = Doc2Vec.load(root_path + 'doc2vec_movie_short')
    
    @staticmethod
    def _tokenize_text_long(text):
        """ Tokenizing text to list of words
        """
        
        tokens = []
        for sent in nltk.sent_tokenize(text, language='english'):
            for word in nltk.word_tokenize(sent, language='english'):
                if len(word) <= 2:
                    continue
                if word in stopwords.words('english'):
                    continue
                tokens.append(word)
        return tokens
    
    @staticmethod
    def _tokenize_text_short(text):
        """ Tokenizing text to list of words for modified plot
        """
        
        with open(root_path + 'dict_not_used_words.pkl', 'rb') as fin:
            dict_ = pickle.load(fin)
            
        tokens = []
        for sent in nltk.sent_tokenize(text, language='english'):
            for word in nltk.word_tokenize(sent, language='english'):
                if len(word) <= 2:
                    continue
                if word in stopwords.words('english') or word in dict_:
                    continue
                tokens.append(word)
        return tokens
    
    
    def plot2movie(text, n_matches=10, long=True):
        """ Find movies based on doc2vec model which are close
        (using cosine similarity) to the given discription.
        
        Parameters
        ----------
        text : str
            A given plot for which we want to find similar movies.
        n_matches : int
            The quantity of matched movies which we want to review for given
            plot descripiton.
        long : bool
            Specify which model to apply, if:
            True - model trained on all words from data, neither words of plots
                nor movies were removed for trained data.
            False - model have been trained on modified data; words which were met
                rarelier than 3 times in all plots were removed, movies which have
                plots discription less than 500 symbols have been removed.
                
        Returns
        -------
        df : pd.DataFrame
            DataFrame of movies with shape (n_matches, [Title, Year, Director, Plot])
        """
        print(long)
        if long:
            text_tok = MoviePlot._tokenize_text_long(text)
            pred = model_long.infer_vector(text_tok)
            movies = model_long.docvecs.most_similar([pred], topn = n_matches)
    
        else:
            text_tok = MoviePlot._tokenize_text_short(text)
            pred = model_short.infer_vector(text_tok)
            movies = model_short.docvecs.most_similar([pred], topn = n_matches)
                    
        titles = [t for t, _ in movies]
        
        plots = []
        for title in titles:
            plots.append(df['Plot'][df.Title == title].values[0])
        
        plots = np.array(plots)[:,None]
        
        
        sim_doc = [doc.split(' - ') for doc, _ in movies]
        sim_doc = np.hstack((sim_doc, plots))
        data = pd.DataFrame(sim_doc, columns=['Title', 'Year', 'Director', 'Plot'])
            
        return data
      
class NER:

    ner_model = build_model("./deeppavlov/ner_config.json", download=True)

    def train():
        train_model("./deeppavlov/ner_config.json", download=True)
        NER.ner_model = build_model("./deeppavlov/ner_config.json", download=True)

    def NamedEntityRecognition(message):
        ner = NER.ner_model([message])
        return ner[0][0], ner[1][0]
