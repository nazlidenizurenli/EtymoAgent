import os
import tkinter as tk
from tkinter import messagebox
import nltk

# Ensure NLTK data path is correct
nltk.data.path.append("/opt/anaconda3/envs/etymoagent/nltk_data")

# Download WordNet corpus if not already downloaded
nltk.download('wordnet')

from nltk.corpus import wordnet

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

def getuserinput():
    def process_word():
        input_word = word_entry.get().strip()
        
        if input_word:
            if is_valid_word(input_word):
                messagebox.showinfo("Valid Word", f"You entered a valid word: {input_word}")
                # Save result to a file
                result_file = os.path.join(OUTPUT_DIR, f"{input_word}.result")
                with open(result_file, 'w') as f:
                    f.write(f"Processing '{input_word}'...")
                root.destroy()  # Close the GUI window
            else:
                messagebox.showerror("Invalid Input", "Please enter a valid English word.")
        else:
            messagebox.showerror("Invalid Input", "Please enter a word.")

    # Create the main application window
    root = tk.Tk()
    root.title("EtymoAgent")

    # Create a label and an entry box for the word input
    word_label = tk.Label(root, text="Please enter a word to be analyzed:")
    word_label.pack(pady=10)

    word_entry = tk.Entry(root, width=30)
    word_entry.pack()

    # Create a button to process the input word
    process_button = tk.Button(root, text="Process Word", command=process_word)
    process_button.pack(pady=10)

    # Run the main loop
    root.mainloop()

if __name__ == '__main__':
    ensure_output_dir()  # Ensure the output directory exists
    getuserinput()
