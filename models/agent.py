import sqlite3
import pandas as pd
import numpy as np
import sys, os
from gensim.models import Word2Vec
from gensim.models import KeyedVectors
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# Step 1: Data Preparation
def connect_db(db_name):
    data_path = os.path.join(os.environ.get("ETYMOAGENT"), 'data')
    db_path = os.path.join(data_path, db_name)
    conn = sqlite3.connect(db_path)
    return conn

def load_and_prepare_data(db_name):
    conn = connect_db(db_name)
    query = 'SELECT word, origin_language FROM words'
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Normalize the words
    df['word'] = df['word'].str.lower()
    return df

# Load pre-trained Word2Vec model
def load_pretrained_word2vec():
    models_path = os.path.join(os.environ.get("ETYMOAGENT"), 'models')
    path_to_pretrained = os.path.join(models_path, "GoogleNews-vectors-negative300.bin")
    model = KeyedVectors.load_word2vec_format(path_to_pretrained, binary=True)
    return model

# Extract semantic features using Word2Vec
def extract_semantic_features(df, word2vec_model):
    def get_word_vector(word):
        return word2vec_model[word] if word in word2vec_model else np.zeros(300)  # 300 is the vector size of the Word2Vec model

    df['word_vector'] = df['word'].apply(get_word_vector)
    return df['word_vector'].values.tolist()

# Extract orthographic features using character n-grams
def extract_orthographic_features(df):
    # Initialize CountVectorizer for character n-grams (1-grams, 2-grams, 3-grams)
    vectorizer = CountVectorizer(analyzer='char', ngram_range=(1, 3))
    
    # Fit and transform the 'word' column of your DataFrame
    X_char_ngrams = vectorizer.fit_transform(df['word']).toarray()
    
    # Count number of zero vectors (where all elements are zeros)
    num_zero_vectors = np.sum(np.all(X_char_ngrams == 0, axis=1))
    
    # Count number of non-zero vectors
    num_non_zero_vectors = X_char_ngrams.shape[0] - num_zero_vectors
    
    # Total number of vectors
    total_vectors = X_char_ngrams.shape[0]
    
    # Print results
    # print(f"Total vectors: {total_vectors}")
    # print(f"Number of zero vectors: {num_zero_vectors}")
    # print(f"Number of non-zero vectors: {num_non_zero_vectors}")

    return X_char_ngrams, vectorizer


# Combine semantic and orthographic features
def combine_features(df, word2vec_model):
    semantic_features = extract_semantic_features(df, word2vec_model)
    orthographic_features, vectorizer = extract_orthographic_features(df)
    X = np.hstack((semantic_features, orthographic_features))
    y = df['origin_language']
    return X, y, vectorizer

# Step 3: Model Selection
def initialize_model():
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    return clf

# Step 4: Training and Evaluation
def train_and_evaluate_model(clf, X, y):
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train the model
    clf.fit(X_train, y_train)

    # Predict and evaluate
    y_pred = clf.predict(X_test)
    print(f'Accuracy: {accuracy_score(y_test, y_pred)}')
    print(classification_report(y_test, y_pred))
    
    return clf

# Step 5: Prediction
def predict_origin(new_word, clf, word2vec_model, vectorizer):
    try:
        # Preprocess the new word
        processed_word = new_word.lower()
        
        # Get word vector for the input word
        word_vector = word2vec_model.get_vector(processed_word)
        
        # Prepare features
        word_vector = np.array(word_vector).reshape(1, -1)  # Reshape for compatibility
        
        # Orthographic features using character n-grams
        X_char_ngrams = vectorizer.transform([processed_word]).toarray()
        
        # Combine word vector with character n-grams
        X = np.hstack((word_vector, X_char_ngrams))
        
        # Predict origin
        predicted_origin = clf.predict(X)
        
        return predicted_origin[0]  # Assuming single prediction
        
    except KeyError:
        # Handle out-of-vocabulary words
        print(f'Warning: Word "{new_word}" not found in vocabulary.')
        return None

# Main Function
def main(db_name, new_word):
    # Step 1: Data Preparation
    df = load_and_prepare_data(db_name)
    
    # Step 2: Feature Extraction
    word2vec_model = load_pretrained_word2vec()
    
    # Extract and combine features
    X, y, vectorizer = combine_features(df, word2vec_model)
    
    # Step 3: Model Selection
    clf = initialize_model()
    
    # Step 4: Training and Evaluation
    clf = train_and_evaluate_model(clf, X, y)
    
    # Step 5: Prediction
    predicted_origin = predict_origin(new_word, clf, word2vec_model, vectorizer)
    if predicted_origin:
        print(f'The predicted origin of "{new_word}" is "{predicted_origin}".')

# Run the program
if __name__ == "__main__":
    # if len(sys.argv) != 2:
    #     print("Usage: python3 agent.py <user_word>")
    #     sys.exit(1)  
    user_word = sys.argv[1].strip().lower()
    db_name = 'etymoagent.db'  # Replace with your database name
    main(db_name, user_word)
