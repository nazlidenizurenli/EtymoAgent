"""
clean_data.py: A script to clean data in the EtymoAgent SQLite database.

This script connects to the SQLite database, removes duplicate entries, cleans up long or empty meaning fields.
This program is responsible for handling the data cleaning stage of the program.
Modules used:
- sqlite3: For interacting with the SQLite database.

Author: Nazli Urenli
Date: 07/07/2024
"""

import sqlite3
import os
from typing import Optional

def connect_to_db(dbpath: str) -> Optional[sqlite3.Connection]:
    """
    Connect to the SQLite database and return the connection object.

    Args:
        dbpath (str): The path to the SQLite database file.

    Returns:
        Optional[sqlite3.Connection]: The connection object if successful, None otherwise.
    """
    try:
        conn = sqlite3.connect(dbpath)
        print("Connected to EtymoAgent SQLite database")
        return conn
    except sqlite3.Error as e:
        print(e)
        return None

def clean_data(conn: sqlite3.Connection) -> None:
    """
    Clean the data in the SQLite database.

    This function removes duplicate entries, sets meaning fields to None if they are longer than 200 characters
    or empty, and removes entries where all meaning fields are null.

    Args:
        conn (sqlite3.Connection): The connection object to the SQLite database.
    """
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            # Remove duplicate entries
            cursor.execute("DELETE FROM words WHERE id NOT IN (SELECT MIN(id) FROM words GROUP BY word);")
            
            # Set meaning to None if longer than 200 characters or empty
            cursor.execute("UPDATE words SET noun = NULL WHERE LENGTH(noun) > 200 OR noun = '';")
            cursor.execute("UPDATE words SET adj = NULL WHERE LENGTH(adj) > 200 OR adj = '';")
            cursor.execute("UPDATE words SET verb = NULL WHERE LENGTH(verb) > 200 OR verb = '';")
            
            # Remove entries where all meanings are null
            cursor.execute("DELETE FROM words WHERE noun IS NULL AND adj IS NULL AND verb IS NULL;")
            
            conn.commit()
            print("Data cleaned successfully")
        
        except sqlite3.Error as e:
            print(e)
        
        finally:
            cursor.close()

def write_to_file(datapath: str, conn: sqlite3.Connection) -> None:
    """
    Write the cleaned data to a file.

    Args:
        datapath (str): The directory path to save the output file.
        conn (sqlite3.Connection): The connection object to the SQLite database.
    """
    try:
        cursor = conn.cursor()
        outfile = os.path.join(datapath, 'debugcleaned.out')
        with open(outfile, 'w', encoding='utf-8') as f:
            cursor.execute("SELECT * FROM words")
            rows = cursor.fetchall()
            for row in rows:
                f.write(f"{row}\n")
        print("Data written to debugcleaned.out successfully")
    except sqlite3.Error as e:
        print(e)

if __name__ == "__main__":
    datapath = os.path.join(os.environ.get("ETYMOAGENT"), 'data')
    db_path = os.path.join(datapath, 'etymoagent.db')
    connection = connect_to_db(db_path)
    if connection:
        clean_data(connection)
        write_to_file(datapath, connection)
        connection.close()
