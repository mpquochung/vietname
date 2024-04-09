import pandas as pd
import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
import numpy as np
from tensorflow.keras.layers import Embedding, LSTM, Dense, Bidirectional, Dropout
from keras.models import Sequential, load_model
from tensorflow.keras.callbacks import EarlyStopping, TensorBoard
from tensorflow.keras.metrics import F1Score, Precision, Recall


class LSTMClassifier:
    def __init__(self, embedding_dim =100 ,num_epoch=20,batch_size = 128) -> None:
        self.EMBEDDING_DIM = embedding_dim
        self.num_epoch = num_epoch
        self.batch_size = batch_size

    def load_data(self):
        #train_path = "data/cleaned_data/training/train.csv"
        train_path = "data/cleaned_data/testing/random_names_eval.csv"
        eval_path = "data/cleaned_data/testing/random_names_eval.csv"
        df_train = pd.read_csv(train_path,encoding='utf-8',usecols=[1,2])
        df_train.dropna()
        df_eval = pd.read_csv(eval_path,encoding='utf-8',usecols=[1,2])
        df_eval.dropna()
        df_train['name'].astype('str')
        df_eval['name'].astype('str')
        df_train['label'].astype('int')
        df_eval['label'].astype('int')
        self.X_train = df_train['name']
        self.y_train = df_train['label']
        self.X_test = df_eval['name']
        self.y_test = df_eval['label']

    def tokenize(self):
        max_vocab_size = 300000
        oov_token = "<OOV>"
        tokenizer = Tokenizer(num_words = max_vocab_size, oov_token=oov_token)
        tokenizer.fit_on_texts(self.X_train)

        self.word_index = tokenizer.word_index
        X_train_sequences = tokenizer.texts_to_sequences(self.X_train)
        X_test_sequences = tokenizer.texts_to_sequences(self.X_test)

        max_length = 8
        padding_type='post'
        truncation_type='post'

        self.X_test_padded = pad_sequences(X_test_sequences,maxlen=max_length, 
                                    padding=padding_type, truncating=truncation_type)
        self.X_train_padded = pad_sequences(X_train_sequences,maxlen=max_length, padding=padding_type, 
                            truncating=truncation_type)
        
    def word_embedding(self):
        embeddings_index = {}
        if self.EMBEDDING_DIM == 100:
            with open("data/glove.6B.100d.txt", 'r', encoding='utf-8') as f:
                for line in f:
                    values = line.split()
                    word = values[0]
                    coefs = np.asarray(values[1:], dtype='float32')
                    embeddings_index[word] = coefs
            f.close()
        elif self.EMBEDDING_DIM == 300:
            with open("data/glove.42B.300d.txt", 'r', encoding='utf-8') as f:
                for line in f:
                    values = line.split()
                    word = values[0]
                    coefs = np.asarray(values[1:], dtype='float32')
                    embeddings_index[word] = coefs
            f.close()

        self.embedding_matrix = np.zeros((len(self.word_index) + 1, self.EMBEDDING_DIM ))
        for word, i in self.word_index.items():
            embedding_vector = embeddings_index.get(word)
            if embedding_vector is not None:
                # words not found in embedding index will be all-zeros.
                self.embedding_matrix[i] = embedding_vector
        
    def build_model(self):
        embedding_layer = Embedding(
            len(self.word_index) +1,
            self.EMBEDDING_DIM,
            trainable=True,
        )
        embedding_layer.build((1,))
        embedding_layer.set_weights([self.embedding_matrix])

        self.model = Sequential([
            embedding_layer,
            Bidirectional(LSTM(32, return_sequences=True)), 
            Bidirectional(LSTM(16, return_sequences = True)),
            Bidirectional(LSTM(8)),
            Dropout(rate=0.3),
            Dense(16, activation='relu'),
            Dropout(rate=0.3),
            Dense(8, activation='relu'),
            Dropout(rate=0.3),
            Dense(1, activation='sigmoid')
        ])

    def fit(self):
        self.model.compile(loss='binary_crossentropy',optimizer='adam',metrics=['accuracy',Precision(),Recall(),F1Score()])
        log_folder = 'logs'
        callbacks = [
                    EarlyStopping(patience = 10),
                    TensorBoard(log_dir=log_folder)
                    ]
        self.model.fit(self.X_train_padded, self.y_train, batch_size = self.batch_size, epochs=self.num_epoch, validation_data=(self.X_test_padded, self.y_test),callbacks=callbacks)
        self.model.save("model/temp.keras",overwrite=True)

        

    def train(self):
        self.load_data()
        self.tokenize()
        self.word_embedding()
        self.build_model()
        self.fit()

    def eval(self):
        pass


if __name__ == "__main__":
    model = LSTMClassifier(embedding_dim=100,num_epoch=1,batch_size=128)
    model.train()
    model = load_model("model/temp.keras")
    print(model.summary())