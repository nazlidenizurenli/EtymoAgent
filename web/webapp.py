from flask import Flask, render_template, request, jsonify
import re
import nltk
from nltk.corpus import words

nltk.download('words')
english_words = set(words.words())

app = Flask(__name__)

def save_word(word):
    # Function to save the word for ML processing
    # For simplicity, we'll save it to a text file. You can modify this to save to a database.
    with open('words.txt', 'a') as f:
        f.write(word + '\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_etymology', methods=['POST'])
def get_etymology():
    word = request.form['word'].strip().lower()
    
    # Server-side validation
    if not re.match("^[a-zA-Z]+$", word):
        return jsonify({'error': 'Invalid input. Please enter an alphabetic English word.'})
    if word not in english_words:
        return jsonify({'error': 'The word is not recognized as an English word.'})

    # Save the word for further processing
    save_word(word)

    # Dummy response - replace with actual ML model integration
    response = {
        'word': word,
        'etymology': 'This is a dummy response for the etymology of the word.'
    }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
