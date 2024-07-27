import sqlite3
import pandas as pd

def create_db_connection():
    connection = sqlite3.connect("zoleo.db")
    return connection

def close_db_connection(connection):
    connection.close()

def create_table_if_not_exists():
    connection = create_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS tracker (
            file TEXT,
            checkin TEXT NOT NULL,
            location TEXT NOT NULL,
            link TEXT NOT NULL
        )
    """)
    connection.close()

def table_exists():
    connection = create_db_connection()
    result = connection.execute("SHOW TABLES LIKE tracker").fetchall()
    connection.close()
    return result
 

def read_last_row():
    connection = create_db_connection()
    row = connection.execute("""
        SELECT *
        FROM tracker
        ORDER BY id DESC
        LIMIT 1
    """).fetchall()
    connection.close()
    return row


def insert_rows(query):
    connection = create_db_connection()
    connection.executemany("""
    INSERT OR IGNORE INTO tracker (
        file, 
        checkin, 
        location, 
        link)
    VALUES (?, ?, ?, ?)        
    """,
    query
    )
    
    connection.close()

def append_dataframe(dataframe):
    
    connection = create_db_connection()
    dataframe.to_sql(name='tracker', con=connection, if_exists='replace', index=False)
    connection.close()

def read_to_dataframe():
    connection = create_db_connection()
    dataframe = pd.read_sql('SELECT * FROM tracker', connection, parse_dates=['checkin'])
    return dataframe

def remove_dupes(dataframe):
    connection = create_db_connection()
    df_temp = read_to_dataframe()
    new_df = pd.concat([df_temp, dataframe]).drop_duplicates()
    connection.close()

    return new_df