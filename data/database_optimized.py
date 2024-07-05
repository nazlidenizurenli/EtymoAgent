import wikipediaapi
import sqlite3
import requests
import string
import nltk
import re
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

DATABASE_PATH = 'etymoagent_opt.db'
langlist = ['French', 'German', 'Latin', 'Greek', 'Turkish']

nltk.data.path.append("/opt/anaconda3/envs/etymoagent/nltk_data")

def connect_db():
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
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

def batch_insert_words(batch):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.executemany('''
        INSERT INTO words (word, origin_language, noun, adj, verb)
        VALUES (?, ?, ?, ?, ?)
    ''', batch)
    conn.commit()
    conn.close()

def extract_etymology_pairs(etymology_text):
    results = []
    for lang in langlist:
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
        
        pairs = extract_etymology_text(soup, 'Etymology')
        if not pairs:
            return []
        
        meaning_dict = extract_meaning_text(soup, ['Noun', 'Adjective', 'Verb'])
        if not any(val for val in meaning_dict.values()):
            return []
        
        word_data = []
        for language, word in pairs:
            word_data.append((word, language, meaning_dict['Noun'], meaning_dict['Adjective'], meaning_dict['Verb']))
        return word_data
    return []

def get_words(url, lang, letter):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        links = [link.get('href') for link in soup.find_all('a') if link.get('href') and (link.get('href').startswith(f'/wiki/{letter}') or link.get('href').startswith(f'/wiki/{letter.lower()}'))]
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(lambda href: processlink(url, href), links)
        
        word_data_batch = [item for sublist in results for item in sublist]
        if word_data_batch:
            batch_insert_words(word_data_batch)

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
    initialize_database()
    print("Database initialized successfully")
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM words')
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    conn.close()
