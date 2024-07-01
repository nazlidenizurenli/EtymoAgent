import requests
from bs4 import BeautifulSoup

def scrape_word_definition(word):
    url = f'https://www.exampledictionary.com/definition/{word}'
    headers = {'User-Agent': 'Mozilla/5.0'}  # Set a user-agent to mimic a browser
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        definition_element = soup.find('div', class_='definition')  # Adjust based on the HTML structure of the website
        if definition_element:
            return definition_element.text.strip()
        else:
            return f"No definition found for '{word}'"
    else:
        return f"Failed to fetch definition for '{word}'. Status code: {response.status_code}"

# Example usage
word = 'example'
definition = scrape_word_definition(word)
print(f'Definition of "{word}": {definition}')
