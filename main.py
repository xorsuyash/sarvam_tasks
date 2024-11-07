from scrape_bot import BibleScraperBot
import argparse

def start_scraping(url):
    bot = BibleScraperBot(url=url)
    bot.load_base_url()
    bot.scrape_data()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Scrape data from a given URL using BibleScraperBot.")
    parser.add_argument('url', type=str, help="The URL to start scraping data from")

    args = parser.parse_args()
    start_scraping(args.url)

