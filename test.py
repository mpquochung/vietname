import tensorflow as tf
print("TensorFlow version:", tf.__version__)
model = tf.keras.models.load_model("model/lstm_classifier.keras")