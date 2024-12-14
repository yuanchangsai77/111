# database.py
import sqlite3
from typing import List, Tuple

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('pacman.db')
        self.cursor = self.conn.cursor()
        self.create_tables()
        
    def create_tables(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS maps (
            level INTEGER PRIMARY KEY,
            map_data TEXT,
            wall_color TEXT,
            power_pellets TEXT
        )''')
        
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            score INTEGER,
            completed_level INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        self.conn.commit()
        
    def save_map(self, level: int, map_data: List[List[int]], wall_color: str, power_pellets: dict):
        self.cursor.execute(
            'INSERT OR REPLACE INTO maps (level, map_data, wall_color, power_pellets) VALUES (?, ?, ?, ?)',
            (level, str(map_data), wall_color, str(power_pellets))
        )
        self.conn.commit()
        
    def get_map(self, level: int) -> Tuple[List[List[int]], str, dict]:
        self.cursor.execute('SELECT map_data, wall_color, power_pellets FROM maps WHERE level = ?', (level,))
        result = self.cursor.fetchone()
        if result:
            return eval(result[0]), result[1], eval(result[2])
        return None, None, None

    def save_score(self, score: int, level: int):
        self.cursor.execute(
            'INSERT INTO scores (score, completed_level) VALUES (?, ?)',
            (score, level)
        )
        self.conn.commit()

