from sklearn import linear_model
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
import pandas as pd
from common.text_utils import normalized
from common.text_pattern import TITLE_PATTERN
from common.tf_idf import TfidfEmbeddingVectorizer
from tqdm import tqdm
import dill

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

    
    def check_coverage(self, text):
        length = len(text.split())
        count = 0
        for word in text.split():
            self.character.add(word)
            if word in self.w2v.keys():
                count+=1
                self.in_coverage.add(word)
        return length, count

    

    def train(self):
        print("Training")
        w2v = TfidfEmbeddingVectorizer(w2v_type="glove")
        self.lr_pipeline  = Pipeline([
            ("word2vec_vectorizer", w2v),
            ("logistic_regression", linear_model.LogisticRegression())
        ])
        
        self.w2v = w2v.w2v

        total_length = 0
        coverage = 0
        self.character = set()
        self.in_coverage = set()

        for text in self.df_train['name'].values:
            length, count = self.check_coverage(text)
            total_length += length
            coverage +=count

        print("Coverage: ", coverage/total_length, ", num words: ", len(self.character),", Coverage word: ", len(self.in_coverage)/len(self.character))
                                                 
        self.lr_pipeline.fit(self.df_train['name'],self.df_train['label'])
        print("Done Traning")
        
    def evaluate(self):
        prediction = self.lr_pipeline.predict(self.df_eval['name'])
        print("Accuracy",accuracy_score(prediction, self.df_eval['label']))
        print("Recall",recall_score(prediction, self.df_eval['label']))
        print("Precision",precision_score(prediction, self.df_eval['label']))
        print("f1",f1_score(prediction, self.df_eval['label']))
        
        df_compare = self.df_eval
        df_compare['predict'] = prediction
        df_compare.to_csv('predict/lr.csv')


    def save_model(self):
        with open("model/lrc_model.pkl",'wb') as f:
            dill.dump(self.lr_pipeline,f)

        

if __name__ == '__main__':
    lr_clf = LogisticClassifier()
    lr_clf.read_data()
    lr_clf.train()
    lr_clf.evaluate()
    lr_clf.save_model()