import wikipediaapi
import sqlite3
import requests
import string
import nltk
import re
import time
import os
from bs4 import BeautifulSoup

projdir = os.environ.get("ETYMOAGENT")
datadir = os.path.join(projdir, 'data')
DATABASE_PATH = os.path.join(datadir, 'etymoagent.db')
langlist = ['French', 'German', 'Latin', 'Greek', 'Turkish']


nltk.data.path.append("/opt/anaconda3/envs/etymoagent/nltk_data")

def connect_db():
    conn = sqlite3.connect(DATABASE_PATH)
    return conn

def create_tables():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY,
            word TEXT NOT NULL,
            origin_language TEXT NOT NULL,
            noun TEXT,
            adj TEXT,
            verb TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_word(word, origin_language, noun, adj, verb):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO words (word, origin_language, noun, adj, verb)
        VALUES (?, ?, ?, ?, ?)
    ''', (word, origin_language, noun, adj, verb))
    word_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return word_id
    
def extract_etymology_pairs(etymology_text):
    results = []
    for lang in langlist:
        # pattern = rf'[Ff]rom\s+(?:\w+\s+)?({lang})\s+([^\s,]+)'
        pattern = rf'(?:[Ff]rom\s+)?(?:\w+\s+)?({lang})\s+([^\s,]+)'
        matches = re.findall(pattern, etymology_text, re.IGNORECASE)
        if matches:
            results.append(matches[0])
    return results

def extract_etymology_text(soup, section):
    etymology_section = soup.find('h3', id=section)
    if etymology_section:
        etymology_content = ""
        for element in etymology_section.next_elements:
            if element.name == 'p':
                etymology_content += element.get_text() + " "
            elif element.name in ['h2', 'h3']:
                break
        pairs = extract_etymology_pairs(etymology_content)
    else:
        pairs = []
    return pairs

def extract_meaning_text(soup, section):
    meaning_dict = {}
    for s in section:
        meaning_dict[s] = ''
    for s in section:     
        meaning_section = soup.find('h3', id=s)
        if meaning_section:
            meaning_content = ""
            for element in meaning_section.next_elements:
                if element.name == 'ol':
                    meaning_dict[s] = element.get_text() + " "
                elif element.name in ['h2', 'h3']:
                    break
    return meaning_dict

def processlink(base_url, href):
    full_url = f"https://en.wiktionary.org{href}"
    response = requests.get(full_url)
    if response.status_code == 200:
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract "Etymology" section text
        pairs = extract_etymology_text(soup, 'Etymology')
        if not pairs:
            return
        # Extract "Meaning" section text
        meaning_dict = extract_meaning_text(soup, ['Noun', 'Adjective', 'Verb'])
        if not any(val for val in meaning_dict.values()):
            return []

        # Insert the word and get its ID
        for language, word in pairs:
            word_id = insert_word(word, language, meaning_dict['Noun'], meaning_dict['Adjective'], meaning_dict['Verb'])
    return

def get_words(url, lang, letter):
    # Specify a user agent compliant with Wikimedia's User-Agent policy
    response = requests.get(url)
    if response.status_code == 200:
        # Parse HTML content using BeautifulSoup
        html_content = response.text

        # Parse the HTML content
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find all links ('a' tags) in the page
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and (href.startswith(f'/wiki/{letter}') or href.startswith(f'/wiki/{letter.lower()}')):
                processlink(url, href)
    else:
        print(f"Failed to fetch URL: {url}, Status Code: {response.status_code}")
    return

def initialize_database():
    create_tables()
    languages = langlist
    user_agent = "EtymoAgent/1.0 (https://github.com/nazlidenizurenli/etymoagent)"
    wiki_wiki = wikipediaapi.Wikipedia(user_agent=user_agent)
    for lang in languages:
        for letter in list(string.ascii_uppercase):
            url = f'https://en.wiktionary.org/w/index.php?title=Category:English_terms_derived_from_{lang}&from={letter}'
            get_words(url, lang, letter)
            
if __name__ == '__main__':
    start_time = time.time()
    initialize_database()
    print("Database initialized successfully")
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM words')
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    conn.close()
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.2f} seconds")
