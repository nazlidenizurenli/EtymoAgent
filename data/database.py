import wikipediaapi
import sqlite3
import requests
import string
import nltk
from bs4 import BeautifulSoup
DATABASE_PATH = 'etymoagent.db'

nltk.data.path.append("/opt/anaconda3/envs/etymoagent/nltk_data")

def connect_db():
    conn = sqlite3.connect(DATABASE_PATH)
    return conn

def create_table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY,
            word TEXT NOT NULL,
            origin_language TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def insert_word(word, origin_language):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO words (word, origin_language)
        VALUES (?, ?)
    ''', (word, origin_language))
    conn.commit()
    conn.close()

def get_words(url, lang, letter):
    # Specify a user agent compliant with Wikimedia's User-Agent policy
    response = requests.get(url)
    words = []
    if response.status_code == 200:
        print(f"Found page: {url}")
        # Parse HTML content using BeautifulSoup
        html_content = response.text

        # Parse the HTML content
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find all links ('a' tags) in the page
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and (href.startswith(f'/wiki/{letter}') or href.startswith(f'/wiki/{letter.lower()}')):
                # words.append(href.split('/')[-1])
                word = href.split('/')[-1]
                if 'Category' not in word and word.isalpha():
                    insert_word(word, lang)
    else:
        print(f"Failed to fetch URL: {url}, Status Code: {response.status_code}")
    return words

def initialize_database():
    create_table()
    languages = ['French', 'German', 'Latin', 'Spanish']
    user_agent = "EtymoAgent/1.0 (https://github.com/nazlidenizurenli/etymoagent)"
    wiki_wiki = wikipediaapi.Wikipedia(user_agent=user_agent)
    for lang in languages:
        for letter in list(string.ascii_uppercase):
            url = f'https://en.wiktionary.org/w/index.php?title=Category:English_terms_derived_from_{lang}&from={letter}'
            words = get_words(url, lang, letter)
            
if __name__ == '__main__':
    initialize_database()
    print("Database initialized successfully")
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM words')
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    conn.close()
