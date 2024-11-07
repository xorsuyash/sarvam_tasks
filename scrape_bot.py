from dataclasses import dataclass, field,asdict
from typing import List, Dict, Optional, Any
import json
import asyncio
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from scraper_v1 import fetch_data_for_urls,fetch_data_nonasync
from tqdm import tqdm 
from urllib.parse import urljoin
import os 

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

@dataclass
class ChapterConfig:
    """Represents a chapter in the scripture with an ID and URL."""
    chapter_id: str
    chapter_url: str

@dataclass
class TestamentMetadata:
    """Represents a testament containing multiple chapters."""
    testament_name: str
    chapters: List[ChapterConfig]

class BibleScraperBot:
    """A web scraping bot to extract chapter metadata and text/audio content for each chapter."""
    
    def __init__(self, url: str, driver_path: str = "chromedriver") -> None:
        self.site_url=url
        self.base_url: str = url.split('/bible')[0]
        self.driver_path: str = driver_path
        self.driver: Optional[webdriver.Chrome] = None

    def _create_driver(self) -> webdriver.Chrome:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        service = Service(executable_path=self.driver_path)
        return webdriver.Chrome(service=service, options=chrome_options)

    def load_base_url(self) -> None:
        self.driver = self._create_driver()
        try:
            self.driver.get(self.site_url)
            logging.info(f"Loaded URL: {self.site_url}")

            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "chapter-dropdown-button"))
            ).click()
            logging.info("Clicked on chapter dropdown button.")

            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "book-container"))
            )
            logging.info("Book container loaded.")

            book_containers = self.driver.find_elements(By.CLASS_NAME, "book-container")
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of(book_containers[0])
            )

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            chapter_div = soup.find_all('div', class_="book-button")
            #testaments = soup.find_all('div', class_='testament-title')

            self.chapters_metadata=[]
            for chapter in chapter_div:
                self.chapters_metadata.append(self._parse_drop_down(chapter))
            
            #print(self.chapters_metadata[0].__dict__)
            #TODO:figure out way to json serialize our dataclases 
            """with open('testament_metadata.json','w') as f:
                print(json.dumps(asdict(self.chapters_metadata[0])))
                json_data=[json.dumps(asdict(chapter),indent=4) for chapter in self.chapters_metadata]
                print(type(json_data[0]))
                json.dump(json_data,f)"""
            logging.info('saved drop-down menu in testament_metadata.json')

            logging.info("Testament metadata successfully extracted.")

        except Exception as e:
            logging.error(f"Error loading base URL and extracting metadata: {str(e)}")
        finally:
            if self.driver:
                self.driver.quit()
                logging.info("WebDriver closed.")
    
    def _parse_drop_down(self,div_content:BeautifulSoup)->TestamentMetadata:

        testament_name=div_content.find('h4').get_text(strip=True)

        chapters=[]
        chapter_links=div_content.find_all('a',class_='chapter-box')
        for link in chapter_links:
            chapter_url=link.get('href')
            chapter_id=link.find('span').get_text(strip=True)
            chapters.append(ChapterConfig(chapter_id=chapter_id,
                                          chapter_url=urljoin(self.base_url,chapter_url)))
        
        chapters_metadata=TestamentMetadata(testament_name=testament_name,chapters=chapters)

        return chapters_metadata

    def scrape_data(self):
        
        global_metadata=[]
        #print(len(self.chapters_metadata))
        new_testaments=self.chapters_metadata[39:]
        #print(len(new_testaments))
        for i in tqdm(range(len(new_testaments))):
            logging.info(f"processing for {new_testaments[i].testament_name}")
            folder_name=f'testament_{i}'
            urls=self._gather_urls(new_testaments[i])
            #results=asyncio.run(fetch_data_for_urls(urls))
            #print(urls)
            results=fetch_data_nonasync(urls)
            print(type(results))
            #print(results[0])
            merged_data=self.merge_list_on_url(results,new_testaments[i].chapters)
            #print(merged_data)
            final_result=self.process_and_save_data(merged_data,folder_name)
            global_metadata.append({'testament_name':new_testaments[0].testament_name,
                                    'testament_folder_name':folder_name,
                                    'chapters':final_result})
        #save global metadata
        with open('global_metadata.json','w') as f:
            json.dump(global_metadata,f,indent=4)
        
        logging.info('scraping complete')
    
    def process_and_save_data(self,merged_data:List[Dict],folder_name:str):
        
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        
        local_metadata=[]
        for data in merged_data:
            chapter_folder_name=f"chapter_{data['chapter_id']}"
            folder_path=os.path.join(folder_name,chapter_folder_name)
            os.makedirs(folder_path,exist_ok=True)
            text_file_path=os.path.join(folder_path,'content.txt')
            audio_file_path=os.path.join(folder_path,'audio.mp3')

            with open(text_file_path,'w') as f:
                f.write(data['text'])
            
            with open(audio_file_path,'wb') as audio_file:
                    audio_file.write(data['audio'])
            
            local_metadata.append({'chapter_id':data['chapter_id'],
                                 'chapter_url':data['chapter_url'],
                                 'text_file_path':text_file_path,
                                 'audio_file_path':audio_file_path})
        
        return local_metadata

    
    @staticmethod
    def merge_list_on_url(dict_list:List[Dict], dataclass_list:List[ChapterConfig])->List[Dict]:
        merged_list = []
        
        chapter_map = {chapter.chapter_url: chapter for chapter in dataclass_list}
        
        #print(chapter_map)
        for entry in dict_list:
            chapter_url = entry.get('chapter_url')
            if 'error' in entry:
                print(entry)
            print(chapter_url)
            if chapter_url in chapter_map:
                merged_entry = {
                    **entry, 
                    'chapter_id': chapter_map[chapter_url].chapter_id  
                }
                merged_list.append(merged_entry)

        return merged_list
    
    def _gather_urls(self,configs:TestamentMetadata)->List:
        config_info=configs.chapters
        urls=[]
        for info in config_info:
            urls.append(info.chapter_url)
        return urls 

    def save_metadata_to_file(self, filepath: str) -> None:
        try:
            with open(filepath, 'w') as file:
                json.dump([testament.__dict__ for testament in self.testaments], file, indent=4)
            logging.info(f"Testament metadata saved to {filepath}")
        except IOError as e:
            logging.error(f"Error saving metadata to file {filepath}: {e}")

    def load_metadata_from_file(self, filepath: str) -> None:
        try:
            with open(filepath, 'r') as file:
                data = json.load(file)
                self.testaments = [TestamentMetadata(**testament) for testament in data]
            logging.info(f"Testament metadata loaded from {filepath}")
        except IOError as e:
            logging.error(f"Error loading metadata from file {filepath}: {e}")
        
if __name__=='__main__':
    url='https://live.bible.is/bible/HINDPI/GEN/1'
    bot=BibleScraperBot(url=url)
    bot.load_base_url()
    bot.scrape_data()
