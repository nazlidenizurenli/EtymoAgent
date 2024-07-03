import wikipediaapi
import sqlite3
import requests
import string
import nltk
import re
from bs4 import BeautifulSoup
DATABASE_PATH = 'etymoagent.db'
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
            origin_language TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meanings (
            id INTEGER PRIMARY KEY,
            word_id INTEGER NOT NULL,
            part_of_speech TEXT NOT NULL,
            meaning TEXT NOT NULL,
            FOREIGN KEY (word_id) REFERENCES words(id)
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
    word_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return word_id

def insert_meaning(word_id, part_of_speech, meaning):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO meanings (word_id, part_of_speech, meaning)
        VALUES (?, ?, ?)
    ''', (word_id, part_of_speech, meaning))
    conn.commit()
    conn.close()
    
# def extract_etymology_pairs(etymology_text):
#     pattern = r'[Ff]rom\s+([A-Za-z\s]+)\s+([^\s,]+)(?=(?:,|\s+\w+\s|$))'
#     matches = re.findall(pattern, etymology_text)
#     if not matches:
#         print("NO MATCH")
#         return '', ''
#     return (matches[0][1], matches[0][0])
def extract_etymology_pairs(etymology_text):
    print("Etymology text should exist: ", etymology_text)
    print(etymology_text)
    results = []
    for lang in langlist:
        # pattern = rf'[Ff]rom\s+(?:\w+\s+)?({lang})\s+([^\s,]+)'
        pattern = rf'(?:[Ff]rom\s+)?(?:\w+\s+)?({lang})\s+([^\s,]+)'
        matches = re.findall(pattern, etymology_text, re.IGNORECASE)
        if matches:
            print("FOUND MATCH")
            results.append((matches[0][0], matches[0][1]))
    if not results:
        print("NO MATCH")
    else:
        print(results)
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
    print(f"Current link is: {full_url}")
    response = requests.get(full_url)
    if response.status_code == 200:
        print(f"Found page: {full_url}")
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract "Etymology" section text
        pairs = extract_etymology_text(soup, 'Etymology')
        if not pairs:
            print(f"Error finding the word or language")
            return
        # Insert the word and get its ID
        wordIDs = []
        for language, word in pairs:
            word_id = insert_word(word, language)
            wordIDs.append(word_id)
        
        # Extract "Meaning" section text
        # meaning_dict = extract_meaning_text(soup, ['Noun', 'Adjective', 'Verb'])
        # if not meaning_dict:
        #     print(f"Error finding the meaning.")
        #     return
        # for word_id in wordIDs:
        #     for part_of_speech, meaning in meaning_dict.items():
        #         print(f"Inserting to table: word_id={word_id}, part_of_speech={part_of_speech}, meaning={meaning}")
        #         insert_meaning(word_id, part_of_speech, meaning)
    else:
        print(f"ERROR finding the link: {full_url}")
    return

def get_words(url, lang, letter):
    # Specify a user agent compliant with Wikimedia's User-Agent policy
    response = requests.get(url)
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
                processlink(url, href)
    else:
        print(f"Failed to fetch URL: {url}, Status Code: {response.status_code}")
    return

def initialize_database():
    create_tables()
    # languages = langlist
    languages = ['French']
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
    cursor.execute('SELECT * FROM meanings')
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    conn.close()
