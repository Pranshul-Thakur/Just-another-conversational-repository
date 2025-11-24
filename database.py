# Filename: database.py
import sqlite3
import json
import uuid
import os
from datetime import datetime

DATA_FOLDER = "data"
DB_NAME = os.path.join(DATA_FOLDER, "chat_history.db")

def init_db():
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
        
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            title TEXT,
            created_at TIMESTAMP,
            history TEXT
        )
    ''')
    conn.commit()
    conn.close()

def create_session(first_message):
    session_id = str(uuid.uuid4())
    title = first_message[:30] + "..." 
    created_at = datetime.now()
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO sessions (id, title, created_at, history) VALUES (?, ?, ?, ?)',
              (session_id, title, created_at, json.dumps([])))
    conn.commit()
    conn.close()
    return session_id

def get_all_sessions():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT id, title FROM sessions ORDER BY created_at DESC')
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def load_session(session_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT history FROM sessions WHERE id = ?', (session_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return json.loads(row['history'])
    return None

def save_message(session_id, user_text, sentiment_data, bot_reply):
    current_history = load_session(session_id)
    if current_history is None:
        return 
        
    current_history.append({
        "role": "user",
        "text": user_text,
        "sentiment": sentiment_data
    })
    
    current_history.append({
        "role": "model",
        "text": bot_reply,
        "sentiment": None 
    })
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE sessions SET history = ? WHERE id = ?', 
              (json.dumps(current_history), session_id))
    conn.commit()
    conn.close()

def rename_session(session_id, new_title):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE sessions SET title = ? WHERE id = ?', (new_title, session_id))
    conn.commit()
    conn.close()