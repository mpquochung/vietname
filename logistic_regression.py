from sklearn import linear_model
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score
import pandas as pd
from common.text_utils import normalized
from common.text_pattern import TITLE_PATTERN
from common.tf_idf import TfidfEmbeddingVectorizer
from tqdm import tqdm


class LogisticClassifier():
    def __init__(self) -> None:
        self.train_data_path = "data/training/all_concat_name.tsv"
        self.eval_data_path = "data/eval/localch.tsv"

    def read_data(self, train_path=None, eval_path = None):
        if not train_path:
            train_path = self.train_data_path 
        if not eval_path:
            eval_path = self.eval_data_path
        
        self.df_train = pd.read_table(train_path,encoding='utf-8',usecols=[0, 1], names = ['name', 'label'])
        self.df_eval = pd.read_table(eval_path,encoding='utf-8',usecols=[0, 1], names = ['name', 'label'])

        #drop_duplicate
        self.df_train.drop_duplicates(inplace = True)
        
        #normalize
        self.df_train['name'] = [normalized(name,folding= True, blacklist_patterns= TITLE_PATTERN) for name in tqdm(self.df_train['name'])]
        self.df_eval['name'] = [normalized(name,folding= True, blacklist_patterns= TITLE_PATTERN) for name in tqdm(self.df_eval['name'])]


        #drop_duplicate_again
        self.df_train.drop_duplicates(inplace = True)
    

    def train(self):
        print("Training")
        self.lr_pipeline  = Pipeline([
            ("word2vec_vectorizer", TfidfEmbeddingVectorizer()),
            ("svm", linear_model.LogisticRegression())
        ])
        self.lr_pipeline.fit(self.df_train['name'],self.df_train['label'])
        print("Done Traning")
        
    def predict(self):
        predict = self.lr_pipeline.predict(self.df_eval['name'])
        acc = accuracy_score(predict, self.df_eval['label'])
        return predict,acc
        

if __name__ == '__main__':
    lr_clf = LogisticClassifier()
    lr_clf.read_data()
    lr_clf.train()
   