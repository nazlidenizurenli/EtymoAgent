import sqlite3
import os

# Function to connect to SQLite database
def connect_to_db(dbpath):
    try:
        conn = sqlite3.connect(dbpath)
        print("Connected to EtymoAgent SQLite database")
        return conn
    except sqlite3.Error as e:
        print(e)
        return None

# Function to clean data in SQLite database
def clean_data(conn):
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

def write_to_file(datapath, conn):
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
