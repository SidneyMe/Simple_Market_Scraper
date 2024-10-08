from scrapers.base_scraper import Scraper
from web_driver import WebDriver
import time
import json

class FullSteamScrape(Scraper):
    """
    FullSteamScrape is a class that scrapes item data from the Steam Community Market for the game CS:GO.
    Methods:
        __init__(web_driver: WebDriver):
            Initializes the FullSteamScrape instance with a web driver and sets the initial URL and items list.
        get_json():
            Fetches the JSON data from the Steam Community Market using the web driver and returns it as a dictionary.
        name_to_ascii(item):
            Converts the name of an item to an ASCII-encoded string suitable for use in a URL.
        json_to_url(item):
            Constructs a URL for an item based on its ASCII-encoded name.
        page_loader(page_num, tries=5):
            Loads a specific page of results from the Steam Community Market, retrying up to a specified number of times if necessary.
        scrape():
            Iterates through pages of market data, extracting item information and appending it to the items list.
        extract_items_info(item):
            Extracts relevant information from an item and returns it as a dictionary with keys 'name', 'url', 'qty', and 'price'.
    """


    def __init__(self, web_driver: WebDriver):
        super().__init__(web_driver)
        self.items_list = []
        self.url = 'https://steamcommunity.com/market/search/render/?appid=730&norender=1'
        self.max_retries = 5
        self.retry_delay = 5


    def get_json(self):
        page = self.web_driver.get_page(self.url, 13)
        page_json = page.xpath('/html/body/pre/text()')[0]
        self.url = self.url.split('&start=')[0]
        return json.loads(page_json)


    def name_to_ascii(self, item):
        ascii_name = ''
        for char in item['name']:
            if char.isalnum() or ord(char) > 127:
                ascii_name += char
            else:
                ascii_name += f'%{hex(ord(char)).removeprefix('0x')}'
        return ascii_name


    def json_to_url(self, item):
        return f'https://steamcommunity.com/market/listings/730/{self.name_to_ascii(item)}'


    def page_loader(self, page_num):
        for attempt in range(self.max_retries):
            try:
                self.url = f'{self.url}&start={page_num}&count={page_num+100}'
                page_json = self.get_json()
                if 'results' in page_json and page_json['results']:
                    return page_json['results']
                else:
                    raise TypeError("Results key not found or empty. Reloading")
            except (TypeError, json.JSONDecodeError) as e:
                print(f"Error occurred (Attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    print(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    print(f"Max retries reached. Skipping this page.")
                    return None


    def scrape(self):
        try:
            num_pages = self.get_json()['total_count']
        except(KeyError, json.JSONDecodeError):
            num_pages = 20800
        for i in range(0, num_pages, 100):
            print(f'Working with page {(i+1)//100}')
            results = self.page_loader(i)
            if results is None:
                continue
            for item in results:
                self.items_list.append(self.extract_items_info(item))


    def extract_items_info(self, item):
        return {
                    'name' : item['name'],
                    'url' : self.json_to_url(item),
                    'qty' : item['sell_listings'],
                    'price' : item['sell_price_text'],
                }