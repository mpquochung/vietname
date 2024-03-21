from sklearn.feature_extraction.text import TfidfVectorizer
from collections import defaultdict
import numpy as np
from tqdm import tqdm

class TfidfEmbeddingVectorizer(object):
 
    def __init__(self, w2v_type="glove"):
        
        if w2v_type == "glove":
            self.dim = 300
            with open("./data/glove.42B.300d.txt", "r", encoding="utf-8") as lines:
                self.w2v = {line.split()[0]: np.array([float(i) for i in line.split()[-self.dim:]])
                for line in tqdm(lines)}
        else:
            self.dim = 300
            with open("./data/word2vec_vi_syllables_300dims.txt", "r", encoding="utf-8") as lines:
                self.w2v = {line.split()[0]: np.array([float(i) for i in line.split()[-self.dim:]])
                for line in tqdm(lines)}

        self.word2vec = self.w2v
        self.word2weight = None
        

    def fit(self, X, y):
        tfidf = TfidfVectorizer(analyzer=lambda x: x)
        tfidf.fit(X)
        # if a word was never seen - it must be at least as infrequent
        # as any of the known words - so the default idf is the max of 
        # known idf's
        max_idf = max(tfidf.idf_)
        self.word2weight = defaultdict(
            lambda: max_idf,
            [(w, tfidf.idf_[i]) for w, i in tqdm(tfidf.vocabulary_.items())])

        return self
    
    # def check_coverage(self, text):
    #     for word in text.split():


    def transform(self, X):
        
        return np.array([
                np.mean([self.word2vec[w] * self.word2weight[w]
                         for w in words.split() if w in self.word2vec] or
                        [np.zeros(self.dim)], axis=0)
                for words in X
            ])

if __name__ == "__main__":
    trans = TfidfEmbeddingVectorizer()

    print(len(trans.word2vec))
    trans.fit(['nguyen quang hung'], [1])
    print(trans.transform(['nguyen quang hung']))