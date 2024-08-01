"""
EtymoAgent: A Flask web application for retrieving etymology information of words.

EtymoAgent is a machine learning-powered linguist agent designed to analyze words, 
determine their linguistic roots, predict their meanings, and suggest related words. 
This project aims to blend the power of machine learning with linguistic analysis, 
creating a useful tool for language enthusiasts.

This script sets up a Flask web server, ensures necessary directories and NLTK data are available,
initializes the database if needed, and cleans the data. It provides an endpoint for querying the etymology
of a word using a pre-trained machine learning model.

Modules used:
- nltk: For natural language processing tasks.
- flask: For setting up the web server.

Author: Nazli Urenli
Date: 07/07/2024
"""

import os
import json
import nltk
import subprocess
import sys
import ast
import click
from nltk.corpus import wordnet
from flask import Flask, render_template, request, jsonify

# Append the project path to the system path
sys.path.append('/Users/nazlidenizurenli/ndu_code/EtymoAgent')

app = Flask(__name__)

# Ensure NLTK data path is correct
nltk.data.path.append("/opt/anaconda3/envs/etymoagent/nltk_data")

# Download WordNet corpus if not already downloaded
nltk.download('wordnet')

# Retrieve OUTPUT_DIR from ETYMOAGENT environment variable
OUTPUT_DIR = os.environ.get("ETYMOAGENT", "output")

def ensure_output_dir() -> None:
    """
    Ensure the output directory exists; create it if it doesn't.

    This function checks if the directory specified by OUTPUT_DIR exists,
    and creates it if it doesn't.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def is_valid_word(word: str) -> bool:
    """
    Check if the given word is valid using WordNet.

    Args:
        word (str): The word to check.

    Returns:
        bool: True if the word exists in WordNet, False otherwise.
    """
    try:
        # Check if the word exists in WordNet
        return len(wordnet.synsets(word)) > 0
    except nltk.corpus.reader.wordnet.WordNetError as e:
        print(f"Error checking validity of word '{word}': {e}")
        return False

def database_exists() -> bool:
    """
    Check if the database file exists.

    Returns:
        bool: True if the database file exists, False otherwise.
    """
    project_path = os.environ.get("ETYMOAGENT")
    db_file = os.path.join(project_path, 'etymoagent.db')
    return os.path.exists(db_file)

def initialize_database() -> None:
    """
    Initialize the database if it doesn't exist.

    This function runs the database initialization script if the database file doesn't exist.
    """
    project_path = os.environ.get("ETYMOAGENT")
    rundir = os.path.join(project_path, 'data')
    program_path = os.path.join(rundir, 'database.py')
    
    if not database_exists():
        try:
            subprocess.run(['python3', program_path], check=True)
            print("Database initialized successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error initializing database: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

def clean_data() -> None:
    """
    Clean the data in the database.

    This function runs the data cleaning script if the database file exists.
    """
    click.secho(f"Step 2: Data Cleaning", fg="yellow", bold=True)
    project_path = os.environ.get("ETYMOAGENT")
    rundir = os.path.join(project_path, 'data')
    program_path = os.path.join(rundir, 'clean_data.py')
    
    if database_exists():
        click.secho(f"Found Database. Starting data cleaning...", fg="blue", bold=True)
        try:
            subprocess.run(['python3', program_path], check=True)
            print("Database cleaned successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error cleaning database: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

@app.route('/')
def index() -> str:
    """
    Render the index page.

    Returns:
        str: The rendered index.html template.
    """
    return render_template('index.html')

@app.route('/get_etymology', methods=['POST'])
def get_etymology() -> jsonify:
    """
    Retrieve the etymology of a given word.

    This endpoint accepts a POST request with a word, checks its validity,
    and returns the etymology information.

    Returns:
        jsonify: The etymology information in JSON format.
    """
    word = request.form['word'].strip().lower()
    
    if not is_valid_word(word):
        return jsonify({'error': 'Please enter a valid English word.'})
    
    print(f"User word is: {word}")
    
    cosine_program_path = os.path.join(os.environ.get("ETYMOAGENT"), 'models', 'agent.py')
    print(f"Resolved program path: {cosine_program_path}")
    try:
        result = subprocess.run(['python3', cosine_program_path, word], capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        try:
            result_dict = json.loads(output)
            return jsonify(result_dict)
        except json.JSONDecodeError as e:
            print(f"Error parsing subprocess output: {e}")
            return jsonify({'error': 'Error parsing subprocess output.'}), 500
    except subprocess.CalledProcessError as e:
        print(f"Subprocess error: {e}")
        print(f"Subprocess stderr: {e.stderr}")
        return jsonify({'error': 'Error running subprocess.'}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({'error': 'Unexpected error occurred.'}), 500

if __name__ == '__main__':
    ensure_output_dir()
    initialize_database()
    clean_data()
    app.run(debug=True)
