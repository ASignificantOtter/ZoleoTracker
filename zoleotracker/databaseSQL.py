import sqlite3
import pandas as pd

def create_db_connection():
    connection = sqlite3.connect("zoleo.db")
    return connection

def create_table_if_not_exists(connection):
    
    connection.execute("""
        CREATE TABLE IF NOT EXISTS tracker (
            file TEXT,
            checkin TEXT NOT NULL,
            location TEXT NOT NULL,
            link TEXT NOT NULL
        )
    """)
    connection.close()

def table_exists(connection):
    
    result = connection.execute("SHOW TABLES LIKE tracker").fetchall()
    connection.close()
    return result
 

def read_last_row(connection):
    
    row = connection.execute("""
        SELECT *
        FROM tracker
        ORDER BY id DESC
        LIMIT 1
    """).fetchall()
    connection.close()
    return row


def insert_rows(connection, query_values):
   
    connection.executemany("""
    INSERT INTO tracker (
        file, 
        checkin, 
        location, 
        link)
    VALUES (?, ?, ?, ?)        
    """,
    query_values
    )
    
    connection.close()

def append_dataframe(connection, dataframe):
    
    dataframe.to_sql(name='tracker', con=connection, if_exists='append', index=False)
    connection.close()

def read_to_dataframe(connection):

    dataframe = pd.read_sql('SELECT * FROM tracker', connection, index_col='checkin', parse_dates=['checkin'])
    return dataframe