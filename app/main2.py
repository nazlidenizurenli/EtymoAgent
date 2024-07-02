import os
import tkinter as tk
from tkinter import messagebox
import nltk
from nltk.corpus import wordnet
import sys
sys.path.append('/Users/nazlidenizurenli/ndu_code/EtymoAgent')
from models import etymology_model

# Ensure NLTK data path is correct
nltk.data.path.append("/opt/anaconda3/envs/etymoagent/nltk_data")

# Download WordNet corpus if not already downloaded
nltk.download('wordnet')

# Define the tkinter application
def runEtymoAgent():
    def process_word():
        input_word = word_entry.get().strip()
        if input_word:
            if is_valid_word(input_word):
                # Load the trained model
                model = etymology_model.load_model()

                # Perform prediction using the model
                predicted_language, likelihood = model.predict_language(input_word)

                if predicted_language:
                    messagebox.showinfo("Prediction Result", f"Word '{input_word}' is most likely related to {predicted_language} with {likelihood:.2%} likelihood.")
                else:
                    messagebox.showerror("Prediction Result", f"Sorry, we couldn't determine the origin of the word '{input_word}'.")
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

    # Function to check if the word exists in WordNet
    def is_valid_word(word):
        try:
            # Check if the word exists in WordNet
            return len(wordnet.synsets(word)) > 0
        except nltk.corpus.reader.wordnet.WordNetError as e:
            print(f"Error checking validity of word '{word}': {e}")
            return False

    # Run the main loop
    root.mainloop()

if __name__ == '__main__':
    runEtymoAgent()

