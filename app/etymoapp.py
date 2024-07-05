import os
import nltk
import subprocess
import sys
import ast
import click
from nltk.corpus import wordnet
from flask import Flask, render_template, request, jsonify
sys.path.append('/Users/nazlidenizurenli/ndu_code/EtymoAgent')


app = Flask(__name__)

# Ensure NLTK data path is correct
nltk.data.path.append("/opt/anaconda3/envs/etymoagent/nltk_data")

# Download WordNet corpus if not already downloaded
nltk.download('wordnet')

# Retrieve OUTPUT_DIR from ETYMOAGENT environment variable
OUTPUT_DIR = os.environ.get("ETYMOAGENT", "output")

def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def is_valid_word(word):
    try:
        # Check if the word exists in WordNet
        return len(wordnet.synsets(word)) > 0
    except nltk.corpus.reader.wordnet.WordNetError as e:
        print(f"Error checking validity of word '{word}': {e}")
        return False

def database_exists():
    project_path = os.environ.get("ETYMOAGENT")
    db_file = os.path.join(project_path, 'etymoagent.db')
    return os.path.exists(db_file)

def initialize_database():
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

def clean_data():
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
def index():
    return render_template('index.html')

@app.route('/get_etymology', methods=['POST'])
def get_etymology():
    word = request.form['word'].strip().lower()
    
    if not is_valid_word(word):
        return jsonify({'error': 'Please enter a valid English word.'})
    
    cosine_program_path = os.path.join(os.environ.get("ETYMOAGENT"), 'models', 'levenshtein.py')
    try:
        result = subprocess.run(['python3', cosine_program_path, word], capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        try:
            result_dict = ast.literal_eval(output)
            print(result_dict)
            return jsonify(result_dict)
        except ValueError as e:
            print(f"Error parsing subprocess output: {e}")
            return jsonify({'error': 'Error parsing subprocess output.'})
        
    except subprocess.CalledProcessError as e:
        print(f"Subprocess error: {e}")
        return jsonify({'error': 'Error running subprocess.'})
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({'error': 'Unexpected error occurred.'})
 
if __name__ == '__main__':
    ensure_output_dir()
    # initialize_database()
    clean_data()
    app.run(debug=True)
