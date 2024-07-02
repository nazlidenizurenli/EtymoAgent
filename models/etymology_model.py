import tensorflow as tf
import numpy as np
import sqlite3

DATABASE_PATH = 'etymoagent.db'
EMBEDDING_DIM = 300 

def connect_db():
    conn = sqlite3.connect(DATABASE_PATH)
    return conn

def fetch_word_embedding(word):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT embedding FROM words WHERE word=?', (word,))
    row = cursor.fetchone()
    if row:
        embedding = np.frombuffer(row[0], dtype=np.float32)
    else:
        embedding = None
    conn.close()
    return embedding

def load_model():
    # Initialize TensorFlow session
    tf.compat.v1.disable_eager_execution()
    session = tf.compat.v1.Session()

    # Placeholder for input word embeddings
    input_word_embedding = tf.compat.v1.placeholder(tf.float32, shape=[EMBEDDING_DIM])

    # Placeholder for target word embeddings
    target_word_embeddings = tf.compat.v1.placeholder(tf.float32, shape=[None, EMBEDDING_DIM])

    # Compute cosine similarity
    input_word_normalized = tf.nn.l2_normalize(input_word_embedding, axis=0)
    target_embeddings_normalized = tf.nn.l2_normalize(target_word_embeddings, axis=1)
    cosine_similarity = tf.reduce_sum(tf.multiply(input_word_normalized, target_embeddings_normalized), axis=1)

    # Save necessary components in a dictionary for prediction
    model = {
        'session': session,
        'input_word_embedding': input_word_embedding,
        'target_word_embeddings': target_word_embeddings,
        'cosine_similarity': cosine_similarity
    }
    return model

def predict_language(model, input_word):
    # Fetch embeddings for input word and target language words
    input_embedding = fetch_word_embedding(input_word)
    target_embeddings = []

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT embedding FROM words')
    rows = cursor.fetchall()
    for row in rows:
        target_embeddings.append(np.frombuffer(row[0], dtype=np.float32))
    conn.close()

    # Calculate similarity scores
    similarity_scores = model['session'].run(model['cosine_similarity'], feed_dict={
        model['input_word_embedding']: input_embedding,
        model['target_word_embeddings']: target_embeddings
    })

    # Find the index of the most similar word
    best_match_index = np.argmax(similarity_scores)
    best_similarity_score = similarity_scores[best_match_index]

    # Fetch the corresponding word
    cursor.execute('SELECT word FROM words')
    target_words = [row[0] for row in cursor.fetchall()]
    best_match_word = target_words[best_match_index]

    # Return predicted language and likelihood
    return best_match_word, best_similarity_score
