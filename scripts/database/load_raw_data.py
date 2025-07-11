import os
import json
from datetime import datetime
import psycopg2
from psycopg2 import sql
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

class RawDataLoader:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=os.getenv('POSTGRES_DB'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT')
        )
        self.cur = self.conn.cursor()
        self.setup_database()
    
    def setup_database(self):
        """Create raw schema and tables if they don't exist"""
        self.cur.execute("""
            CREATE SCHEMA IF NOT EXISTS raw;
            
            CREATE TABLE IF NOT EXISTS raw.telegram_messages (
                id BIGINT PRIMARY KEY,
                date TIMESTAMP WITH TIME ZONE,
                message TEXT,
                views INTEGER,
                has_media BOOLEAN,
                channel VARCHAR(255),
                image_path VARCHAR(255),
                scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        self.conn.commit()
    
    def load_data(self, file_path):
        """Load JSON data from file into database"""
        try:
            with open(file_path) as f:
                data = json.load(f)
            
            channel = os.path.basename(file_path).replace('.json', '')
            
            for message in data:
                self.cur.execute("""
                    INSERT INTO raw.telegram_messages 
                    (id, date, message, views, has_media, channel, image_path)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING;
                """, (
                    message['id'],
                    message['date'],
                    message['message'],
                    message['views'],
                    message['has_media'],
                    message['channel'],
                    message.get('image_path')
                ))
            
            self.conn.commit()
            logger.success(f"Loaded {len(data)} messages from {file_path}")
            return True
        
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error loading {file_path}: {str(e)}")
            return False
    
    def process_directory(self, directory):
        """Process all JSON files in a directory"""
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    self.load_data(file_path)
    
    def close(self):
        self.cur.close()
        self.conn.close()

if __name__ == '__main__':
    loader = RawDataLoader()
    try:
        loader.process_directory('data/raw/telegram_messages')
    finally:
        loader.close()