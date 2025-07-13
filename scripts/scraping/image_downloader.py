import os
import asyncio
from datetime import datetime
from typing import List, Optional, Dict
from dataclasses import dataclass
from pathlib import Path
import hashlib
import aiofiles
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaPhoto
from loguru import logger
from PIL import Image
import imagehash
import cv2
import numpy as np
from dotenv import load_dotenv

# Configuration
load_dotenv()
IMAGE_QUALITY = 85  # JPEG quality (1-100)
DEDUPE_THRESHOLD = 5  # Hash difference threshold
MIN_WIDTH = 100  # Minimum image width in pixels
MIN_HEIGHT = 100  # Minimum image height in pixels

@dataclass
class DownloadedImage:
    message_id: int
    channel: str
    file_path: str
    phash: str
    created_at: str
    dimensions: str
    file_size: int

class AdvancedImageDownloader:
    def __init__(self):
        self.client = TelegramClient(
            'image_downloader',
            int(os.getenv('TELEGRAM_API_ID')),
            os.getenv('TELEGRAM_API_HASH'))
        self.download_dir = Path('data/processed/images')
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.processed_hashes = set()
        self._load_existing_hashes()

    def _load_existing_hashes(self):
        """Load existing image hashes to prevent duplicates"""
        hash_file = self.download_dir / 'image_hashes.txt'
        if hash_file.exists():
            with open(hash_file) as f:
                self.processed_hashes.update(line.strip() for line in f)

    def _save_hash(self, img_hash: str):
        """Save new image hash to prevent future duplicates"""
        with open(self.download_dir / 'image_hashes.txt', 'a') as f:
            f.write(f"{img_hash}\n")
        self.processed_hashes.add(img_hash)

    async def _download_image(self, message, channel: str) -> Optional[DownloadedImage]:
        """Download and process a single image"""
        try:
            file_path = self.download_dir / f"{channel}_{message.id}.jpg"
            
            # Download original image
            await message.download_media(file=str(file_path))
            
            # Image processing pipeline
            img = Image.open(file_path)
            
            # 1. Check minimum dimensions
            if img.width < MIN_WIDTH or img.height < MIN_HEIGHT:
                file_path.unlink()
                return None
            
            # 2. Deduplication with perceptual hashing
            phash = str(imagehash.phash(img))
            for existing_hash in self.processed_hashes:
                if abs(int(phash, 16) - int(existing_hash, 16)) < DEDUPE_THRESHOLD:
                    file_path.unlink()
                    return None
            
            # 3. Optimize image
            img = cv2.imread(str(file_path))
            img = self._enhance_image(img)
            cv2.imwrite(str(file_path), img, [int(cv2.IMWRITE_JPEG_QUALITY), IMAGE_QUALITY])
            
            # 4. Save metadata
            self._save_hash(phash)
            return DownloadedImage(
                message_id=message.id,
                channel=channel,
                file_path=str(file_path.relative_to('data')),
                phash=phash,
                created_at=datetime.utcnow().isoformat(),
                dimensions=f"{img.shape[1]}x{img.shape[0]}",  # width x height
                file_size=os.path.getsize(file_path)
            
        except Exception as e:
            logger.error(f"Failed processing image: {e}")
            if file_path.exists():
                file_path.unlink()
            return None

    def _enhance_image(self, img: np.ndarray) -> np.ndarray:
        """Apply basic image enhancement"""
        # Convert to LAB color space for better contrast enhancement
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        
        # Merge channels and convert back to BGR
        enhanced = cv2.merge((l,a,b))
        return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

    async def _process_channel(self, channel: str, limit: int = 200):
        """Process all images from a channel"""
        logger.info(f"Processing channel: {channel}")
        entity = await self.client.get_entity(channel)
        async for message in self.client.iter_messages(entity, limit=limit):
            if isinstance(message.media, MessageMediaPhoto):
                img_meta = await self._download_image(message, channel)
                if img_meta:
                    logger.success(f"Downloaded {img_meta.file_path}")
                    yield img_meta

    async def run(self, channels: List[str]):
        """Main execution flow"""
        async with self.client:
            tasks = [self._process_channel(ch) for ch in channels]
            async for result in asyncio.as_completed(tasks):
                async for img in await result:
                    # Here you could add database insertion
                    # or other post-processing
                    pass

if __name__ == '__main__':
    downloader = AdvancedImageDownloader()
    channels = [
        "CheMed123",
        "lobelia4cosmetics",
        "tikvahpharma"
    ]
    asyncio.run(downloader.run(channels))