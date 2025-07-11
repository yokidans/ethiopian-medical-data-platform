import os
import json
from datetime import datetime
from loguru import logger
from telethon.sync import TelegramClient
from telethon.tl.types import MessageMediaPhoto

# Configure logger
logger.add("scraper.log", rotation="10 MB")

class TelegramScraper:
    def __init__(self):
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.client = TelegramClient('med_scraper', self.api_id, self.api_hash)
        
        # Target channels
        self.channels = [
            'CheMed123',
            'lobelia4cosmetics',
            'tikvahpharma'
        ]
        
        # Create data directory if not exists
        os.makedirs('data/raw/telegram_messages', exist_ok=True)
    
    async def scrape_channel(self, channel_name):
        try:
            entity = await self.client.get_entity(channel_name)
            today = datetime.now().strftime('%Y-%m-%d')
            output_dir = f'data/raw/telegram_messages/{today}'
            os.makedirs(output_dir, exist_ok=True)
            
            messages = []
            async for message in self.client.iter_messages(entity, limit=100):
                msg_data = {
                    'id': message.id,
                    'date': message.date.isoformat(),
                    'message': message.message,
                    'views': message.views,
                    'has_media': bool(message.media),
                    'channel': channel_name
                }
                
                if isinstance(message.media, MessageMediaPhoto):
                    # Save image path if available
                    image_path = f"data/processed/images/{channel_name}_{message.id}.jpg"
                    msg_data['image_path'] = image_path
                    await self.client.download_media(message, file=image_path)
                
                messages.append(msg_data)
            
            # Save to JSON
            output_file = f"{output_dir}/{channel_name}.json"
            with open(output_file, 'w') as f:
                json.dump(messages, f, indent=2)
            
            logger.success(f"Scraped {len(messages)} messages from {channel_name}")
            return True
        
        except Exception as e:
            logger.error(f"Error scraping {channel_name}: {str(e)}")
            return False
    
    async def run(self):
        async with self.client:
            for channel in self.channels:
                await self.scrape_channel(channel)

if __name__ == '__main__':
    scraper = TelegramScraper()
    import asyncio
    asyncio.run(scraper.run())