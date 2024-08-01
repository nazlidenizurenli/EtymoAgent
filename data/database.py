"""
database.py: A script to extract etymology and meaning of words from Wiktionary and store them in a SQLite database.

This script connects to a SQLite database, creates necessary tables, extracts etymology and meaning of words from Wiktionary,
and inserts the extracted data into the database. It processes links to individual word pages, extracts relevant sections,
and saves the data. This is the data collection stage of the program.

Modules used:
- wikipediaapi: For interacting with Wikipedia/Wiktionary.
- sqlite3: For interacting with the SQLite database.
- requests: For making HTTP requests.
- nltk: Natural Language Toolkit for processing textual data.
- bs4 (BeautifulSoup): For parsing HTML content.

Author: Nazli Urenli
Date: 07/07/2024
"""

import wikipediaapi
import sqlite3
import requests
import string
import nltk
import re
import time
import os
from bs4 import BeautifulSoup
from typing import List, Tuple, Dict, Union

projdir = os.environ.get("ETYMOAGENT")
datadir = os.path.join(projdir, 'data')
DATABASE_PATH = os.path.join(datadir, 'etymoagent.db')
langlist = ['French', 'German', 'Latin', 'Greek', 'Turkish']

nltk.data.path.append("/opt/anaconda3/envs/etymoagent/nltk_data")

def connect_db() -> sqlite3.Connection:
    """
    Connect to the SQLite database and return the connection object.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    return conn

def create_tables() -> None:
    """
    Create the 'words' table in the SQLite database if it does not exist.
    """
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

def insert_word(word: str, origin_language: str, noun: str, adj: str, verb: str) -> int:
    """
    Insert a word into the 'words' table and return the inserted word's ID.

    Args:
        word (str): The word to insert.
        origin_language (str): The language of origin of the word.
        noun (str): The noun meaning of the word.
        adj (str): The adjective meaning of the word.
        verb (str): The verb meaning of the word.

    Returns:
        int: The ID of the inserted word.
    """
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

def extract_etymology_pairs(etymology_text: str) -> List[Tuple[str, str]]:
    """
    Extract etymology pairs from the given etymology text.

    Args:
        etymology_text (str): The etymology text to extract pairs from.

    Returns:
        List[Tuple[str, str]]: A list of tuples containing language and word pairs.
    """
    results = []
    for lang in langlist:
        pattern = rf'(?:[Ff]rom\s+)?(?:\w+\s+)?({lang})\s+([^\s,]+)'
        matches = re.findall(pattern, etymology_text, re.IGNORECASE)
        if matches:
            results.append(matches[0])
    return results

def extract_etymology_text(soup: BeautifulSoup, section: str) -> List[Tuple[str, str]]:
    """
    Extract etymology text from the specified section of the BeautifulSoup object.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object containing the HTML content.
        section (str): The section to extract etymology text from.

    Returns:
        List[Tuple[str, str]]: A list of tuples containing language and word pairs.
    """
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

def extract_meaning_text(soup: BeautifulSoup, sections: List[str]) -> Dict[str, str]:
    """
    Extract meaning text from the specified sections of the BeautifulSoup object.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object containing the HTML content.
        sections (List[str]): The sections to extract meaning text from.

    Returns:
        Dict[str, str]: A dictionary with sections as keys and their corresponding meanings as values.
    """
    meaning_dict = {s: '' for s in sections}
    for s in sections:
        meaning_section = soup.find('h3', id=s)
        if meaning_section:
            for element in meaning_section.next_elements:
                if element.name == 'ol':
                    meaning_dict[s] = element.get_text() + " "
                elif element.name in ['h2', 'h3']:
                    break
    return meaning_dict

def process_link(base_url: str, href: str) -> None:
    """
    Process a link to a word page, extract etymology and meaning, and insert them into the database.

    Args:
        base_url (str): The base URL of the Wiktionary page.
        href (str): The href of the link to process.
    """
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
            return

        # Insert the word and get its ID
        for language, word in pairs:
            insert_word(word, language, meaning_dict['Noun'], meaning_dict['Adjective'], meaning_dict['Verb'])

def get_words(url: str, lang: str, letter: str) -> None:
    """
    Get words from the specified URL, process each link, and extract data.

    Args:
        url (str): The URL to fetch words from.
        lang (str): The language of the words to fetch.
        letter (str): The starting letter of the words to fetch.
    """
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and (href.startswith(f'/wiki/{letter}') or href.startswith(f'/wiki/{letter.lower()}')):
                process_link(url, href)
    else:
        print(f"Failed to fetch URL: {url}, Status Code: {response.status_code}")

def initialize_database() -> None:
    """
    Initialize the database by creating tables and populating them with words from Wiktionary.
    """
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
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.2f} seconds")
