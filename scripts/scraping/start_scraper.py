#!/usr/bin/env python3
from pathlib import Path
from dotenv import load_dotenv
import scripts.scraping.telegram_scraper as scraper

def main():
    # Load environment from project root
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path)
    
    # Run scraper
    scraper = scraper.AdvancedTelegramScraper()
    scraper.run()

if __name__ == '__main__':
    main()