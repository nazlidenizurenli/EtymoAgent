"""
EtymoAgent: This program is designed to predict the origin of an input word and find the most similar word
from a pre-defined database using a combination of semantic and orthographic features.

Modules used:
- sqlite3: For connecting to and querying the SQLite database.
- pandas: For data manipulation and analysis.
- numpy: For numerical operations.
- gensim.models.KeyedVectors: For loading and using pre-trained Word2Vec models.
- sklearn.feature_extraction.text.CountVectorizer: For extracting character n-grams.
- sklearn.ensemble.RandomForestClassifier: For creating and training the RandomForest classifier.
- sklearn.model_selection.train_test_split: For splitting the data into training and testing sets.
- sklearn.metrics: For evaluating the performance of the model.
"""

import sqlite3
import pandas as pd
import numpy as np
import sys
import json
import os
from typing import Tuple
import Levenshtein 
import scipy
from gensim.models import KeyedVectors
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from typing import Tuple, List

def calculate_accuracy(predictions: list, true_origins: list) -> float:
    """
    Calculate the accuracy of the predictions.

    Args:
        predictions (list): List of predicted origins.
        true_origins (list): List of true origins.

    Returns:
        float: Accuracy of the predictions.
    """
    correct = sum(p == t for p, t in zip(predictions, true_origins))
    return correct / len(true_origins)


def split_data(df: pd.DataFrame, test_size: float = 0.2):
    """
    Split the data into training and test sets.

    Args:
        df (pd.DataFrame): DataFrame containing the words and their origin languages.
        test_size (float): Proportion of the data to include in the test split.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: Training and test DataFrames.
    """
    train_df, test_df = train_test_split(df, test_size=test_size, random_state=42)
    return train_df, test_df


def evaluate_model(df: pd.DataFrame):
    """
    Evaluate the orthographic similarity model.

    Args:
        df (pd.DataFrame): DataFrame containing the words and their origin languages.

    Returns:
        None
    """
    # Split the data into training and test sets
    train_df, test_df = split_data(df)

    # Prepare lists to store true origins and predictions
    true_origins = test_df['origin_language'].tolist()
    predictions = []

    # Predict origins for the test set
    for _, row in test_df.iterrows():
        new_word = row['word']
        predicted_origin, _ = predict_origin(new_word, train_df)  # Use the training set for predictions
        predictions.append(predicted_origin)

    # Calculate accuracy
    accuracy = calculate_accuracy(predictions, true_origins)
    print(f"Model Accuracy: {accuracy:.2f}")


# Step 1: Data Preparation
def connect_db(db_name: str) -> sqlite3.Connection:
    """
    Connect to the SQLite database and return the connection object.
    
    Args:
        db_name (str): The name of the database file.
    
    Returns:
        sqlite3.Connection: SQLite connection object.
    """
    data_path = os.path.join(os.environ.get("ETYMOAGENT"), 'data')
    db_path = os.path.join(data_path, db_name)
    conn = sqlite3.connect(db_path)
    return conn

def load_and_prepare_data(db_name: str) -> pd.DataFrame:
    """
    Load and prepare data from the SQLite database.
    
    Args:
        db_name (str): The name of the database file.
    
    Returns:
        pd.DataFrame: DataFrame containing the words and their origin languages.
    """
    conn = connect_db(db_name)
    query = 'SELECT word, origin_language, noun, adj, verb FROM words'
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Normalize the words
    df['word'] = df['word'].str.lower()
    return df


# Load pre-trained Word2Vec model
def load_pretrained_word2vec() -> KeyedVectors:
    """
    Load the pre-trained Word2Vec model.

    Returns:
        KeyedVectors: Loaded Word2Vec model.
    
    Raises:
        FileNotFoundError: If the model file is not found at the specified path.
        Exception: For any other errors during model loading.
    """
    models_path = os.path.join(os.environ.get("ETYMOAGENT"), 'models')
    path_to_pretrained = os.path.join(models_path, "GoogleNews-vectors-negative300.bin")
    
    if not os.path.isfile(path_to_pretrained):
        raise FileNotFoundError(f"Pre-trained Word2Vec model not found at {path_to_pretrained}")

    try:
        print(f"Loading Word2Vec model from {path_to_pretrained}...")
        model = KeyedVectors.load_word2vec_format(path_to_pretrained, binary=True)
        print("Word2Vec model loaded successfully.")
        return model
    except Exception as e:
        print(f"An error occurred while loading the Word2Vec model: {e}")
        raise


# Extract semantic features using Word2Vec
def extract_semantic_features(df: pd.DataFrame, word2vec_model: KeyedVectors) -> List[np.ndarray]:
    """
    Extract semantic features using the Word2Vec model.
    
    Args:
        df (pd.DataFrame): DataFrame containing the words.
        word2vec_model (KeyedVectors): Pre-trained Word2Vec model.
    
    Returns:
        List[np.ndarray]: List of word vectors.
    """
    def get_word_vector(word: str) -> np.ndarray:
        return word2vec_model[word] if word in word2vec_model else np.zeros(300)  # 300 is the vector size of the Word2Vec model

    df['word_vector'] = df['word'].apply(get_word_vector)
    return df['word_vector'].values.tolist()


# Extract orthographic features using character n-grams
def extract_orthographic_features(df: pd.DataFrame) -> Tuple[np.ndarray, CountVectorizer]:
    """
    Extract orthographic features using character n-grams.
    
    Args:
        df (pd.DataFrame): DataFrame containing the words.
    
    Returns:
        Tuple[np.ndarray, CountVectorizer]: Array of orthographic features and the vectorizer.
    """
    vectorizer = CountVectorizer(analyzer='char', ngram_range=(1, 3))
    X_char_ngrams = vectorizer.fit_transform(df['word']).toarray()
    return X_char_ngrams, vectorizer


# Combine semantic and orthographic features
def combine_features(df: pd.DataFrame, word2vec_model: KeyedVectors) -> Tuple[np.ndarray, pd.Series, CountVectorizer]:
    """
    Combine semantic and orthographic features.
    
    Args:
        df (pd.DataFrame): DataFrame containing the words.
        word2vec_model (KeyedVectors): Pre-trained Word2Vec model.
    
    Returns:
        Tuple[np.ndarray, pd.Series, CountVectorizer]: Combined feature array, target labels, and the vectorizer.
    """
    semantic_features = extract_semantic_features(df, word2vec_model)
    orthographic_features, vectorizer = extract_orthographic_features(df)
    X = np.hstack((semantic_features, orthographic_features))
    y = df['origin_language']
    return X, y, vectorizer


# Step 3: Model Selection
def initialize_model() -> RandomForestClassifier:
    """
    Initialize the RandomForestClassifier model.
    
    Returns:
        RandomForestClassifier: Initialized RandomForestClassifier.
    """
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    return clf


def train_and_evaluate_model(clf: RandomForestClassifier, X: np.ndarray, y: pd.Series) -> RandomForestClassifier:
    """
    Train and evaluate the RandomForestClassifier model.
    
    Args:
        clf (RandomForestClassifier): RandomForestClassifier model.
        X (np.ndarray): Feature array.
        y (pd.Series): Target labels.
    
    Returns:
        RandomForestClassifier: Trained RandomForestClassifier model.
    """
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    print(f'Accuracy: {accuracy_score(y_test, y_pred)}')
    print(classification_report(y_test, y_pred))
    return clf


# Step 5: Prediction
def predict_origin(new_word: str, df: pd.DataFrame) -> Tuple[str, str]:
    """
    Predict the origin of the new word based on orthographic similarity.

    Args:
        new_word (str): The new word to predict.
        df (pd.DataFrame): DataFrame containing the words and their origin languages.

    Returns:
        Tuple[str, str]: The predicted origin and the most similar word.
    """
    # Initialize variables
    closest_word = None
    min_distance = float('inf')
    predicted_origin = None

    # Iterate over words in the DataFrame to find the closest match
    for index, row in df.iterrows():
        word = row['word']
        origin_language = row['origin_language']
        distance = Levenshtein.distance(new_word, word)
        
        if distance < min_distance:
            min_distance = distance
            closest_word = word
            predicted_origin = origin_language
            noun_meaning = row['noun']
            adj_meaning = row['adj']
            verb_meaning = row['verb']
            similarity_score = 1 - min_distance / max(len(new_word), len(closest_word)) 

    return closest_word, predicted_origin, similarity_score, noun_meaning, adj_meaning, verb_meaning


def main(db_name: str, new_word: str) -> None:
    """
    Main function to execute the workflow.
    
    Args:
        db_name (str): The name of the database file.
        new_word (str): The new word to predict.
    """
    df = load_and_prepare_data(db_name)
    assert isinstance(df, pd.DataFrame), "The result should be a Pandas DataFrame."
    assert 'word' in df.columns, "The DataFrame should contain a 'word' column."
    assert 'origin_language' in df.columns, "The DataFrame should contain an 'origin_language' column."
    assert 'noun' in df.columns, "The DataFrame should contain a 'noun' column."
    assert 'adj' in df.columns, "The DataFrame should contain an 'adj' column."
    assert 'verb' in df.columns, "The DataFrame should contain a 'verb' column."
    assert not df.empty, "The DataFrame should not be empty."
        
    closest_word, predicted_origin, similarity_score, noun_meaning, adj_meaning, verb_meaning = predict_origin(new_word, df)
    if predicted_origin and closest_word:
        output = {
            "most_similar_word": closest_word,
            "similarity_score": similarity_score,
            "origin_language": predicted_origin,
            "noun_meaning": noun_meaning,
            "adj_meaning": adj_meaning,
            "verb_meaning": verb_meaning
        }
        return json.dumps(output)
    else:
        print("Error getting values")
        
# Run the program
if __name__ == "__main__":
    try:
        user_word = sys.argv[1].strip().lower()
        db_name = 'etymoagent.db'
        result = main(db_name, user_word)
        print(result)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
