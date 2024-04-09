from sklearn import svm
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
import pandas as pd
from common.text_utils import normalized
from common.text_pattern import TITLE_PATTERN
from common.tf_idf import TfidfEmbeddingVectorizer
from tqdm import tqdm
from sklearn.model_selection import RandomizedSearchCV
import dill
import numpy as np
from sklearnex import patch_sklearn
patch_sklearn()


class NBClassifier():
    def __init__(self) -> None:
        self.train_data_path = "data/cleaned_data/training/train.csv"
        self.eval_data_path = "data/cleaned_data/testing/localch.csv"

    def read_data(self, train_path=None, eval_path = None):
        if not train_path:
            train_path = self.train_data_path 
        if not eval_path:
            eval_path = self.eval_data_path
        
        self.df_train = pd.read_csv(train_path,encoding='utf-8',usecols=[1,2])
        self.df_train.dropna(inplace=True)
        self.df_eval = pd.read_csv(eval_path,encoding='utf-8',usecols=[1,2])
        self.df_eval.dropna(inplace=True)

    
    # def check_coverage(self, text):
    #     length = len(text.split())
    #     count = 0
    #     for word in text.split():
    #         self.character.add(word)
    #         if word in self.w2v.keys():
    #             count+=1
    #             self.in_coverage.add(word)
    #     return length, count

    def train(self):
        print("Training")
        w2v = TfidfEmbeddingVectorizer(w2v_type="glove300")
        self.nb_pipeline  = Pipeline([
            ("word2vec_vectorizer", w2v),
            ("naive_bayes", svm.SVC())
        ])
        param_grid = {
            'logistic_regression__C': np.logspace(-2, 2, 5),  # Regularization strength
            'logistic_regression__solver': ['liblinear', 'saga']  # Optimization algorithm
        }
        #self.nb_search = RandomizedSearchCV(estimator=self.nb_pipeline, param_distributions=param_grid, n_iter=10, cv=5,n_jobs=-1)
        #self.w2v = w2v.w2v                   
        self.nb_pipeline.fit(self.df_train['name'],self.df_train['label'])
        #self.model = self.nb_search.best_estimator_
        print("Done Traning")
        
    def evaluate(self):
        prediction = self.nb_pipeline.predict(self.df_eval['name'])
        print("Accuracy",accuracy_score(prediction, self.df_eval['label']))
        print("Recall",recall_score(prediction, self.df_eval['label']))
        print("Precision",precision_score(prediction, self.df_eval['label']))
        print("f1",f1_score(prediction, self.df_eval['label']))
        
        df_compare = self.df_eval
        df_compare['predict'] = prediction
        df_compare.to_csv('predict/rf.csv')


    def save_model(self):
        with open("model/rf_model.pkl",'wb') as f:
            dill.dump(self.nb_pipeline,f)

        

if __name__ == '__main__':
    lr_clf = NBClassifier()
    lr_clf.read_data()
    lr_clf.train()
    lr_clf.evaluate()
    lr_clf.save_model()