import sqlite3
import spacy
import numpy as np
import os, sys
import editdistance

# Load spaCy model
nlp = spacy.load('en_core_web_md')

def connect_db():
    data_path = os.path.join(os.environ.get("ETYMOAGENT"), 'data')
    db_path = os.path.join(data_path, 'etymoagent.db')
    conn = sqlite3.connect(db_path)
    return conn

def fetch_words_from_db():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, word, origin_language, noun, adj, verb FROM words")
    rows = cursor.fetchall()
    conn.close()
    return rows

def vectorize_words(words):
    return {word: nlp(word).vector for word in words if nlp(word).has_vector}

def find_most_similar(input_word, words):
    min_distance = float('inf')
    most_similar_word = None

    for word in words:
        distance = editdistance.eval(input_word, word)
        print(word, distance)
        if distance < min_distance:
            min_distance = distance
            most_similar_word = word

    return most_similar_word, min_distance

def get_word_info(word):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, word, origin_language, noun, adj, verb FROM words WHERE word = ?", (word,))
    row = cursor.fetchone()
    conn.close()
    return row

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 cosine_similarity.py <user_word>")
        sys.exit(1)
        
    user_word = sys.argv[1].strip().lower()
    rows = fetch_words_from_db()
    words = [row[1] for row in rows]
    word_vectors = vectorize_words(words)
    similar_word, similarity_score = find_most_similar(user_word, word_vectors)
    
    if similar_word:
        word_info = get_word_info(similar_word)
        if word_info:
            result = {
                'most_similar_word': similar_word,
                'similarity_score': similarity_score,
                'origin_language': word_info[2],
                'noun_meaning': word_info[3],
                'adj_meaning': word_info[4],
                'verb_meaning': word_info[5]
            }
            print(result)
        else:
            print("Most similar word not found in the database.")
    else:
        print("No similar word found in the model.")
