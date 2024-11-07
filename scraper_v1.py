import asyncio
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import aiohttp
import time
import requests
import random 

#Global request count 
request_count=0
request_lock=asyncio.Lock()

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    service = Service(executable_path="chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


async def extract_text_and_audio(url):
    global request_count

    driver = create_driver()
    logging.info(f"Starting to extract data from {url}")
    
    try:
        driver.get(url)
        logging.info(f"Navigated to {url}. Waiting for page to load...")
        await asyncio.sleep(3)  # Use asyncio.sleep instead of time.sleep

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        chapter_name = soup.find("h1", class_='book-chapter-text')
        logging.debug(f"Extracted chapter name: {chapter_name.get_text(strip=True) if chapter_name else 'N/A'}")

        main_tag = soup.find('main')
        text = ""

        if main_tag:
            span_tags = main_tag.find_all('span', class_='align-left')
            for span in span_tags:
                text +="\n"+span.get_text(strip=True)
            logging.info("Text extracted from main tag.")
        else:
            logging.warning("Main tag not found")

        # Find the audio/video tag
        video_tag = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'audio-player'))
        )
        video_tag = soup.find("video", class_='audio-player')

        if video_tag and video_tag.has_attr('src'):
            audio_url = video_tag['src']
            logging.info(f"Audio URL found")

            async with aiohttp.ClientSession() as session:
                async with session.get(audio_url) as audio_response:
                    if audio_response.status == 200:
                        audio_content = await audio_response.read()
                        logging.info("Audio downloaded successfully.")

                        async with request_lock:
                            request_count += 1
                            # Wait if request count is a multiple of 25
                            if request_count % 25 == 0 and request_count!=0:
                                logging.info("Request count is a multiple of 25. Waiting for 60 seconds...")
                                await asyncio.sleep(random.choice([45,62,53,57]))

                        return {
                            "chapter_url": url,
                            "text": text,
                            "audio": audio_content
                        }
                    else:
                        logging.error(f"Failed to download audio, HTTP status: {audio_response.status}")
                        return {
                            "chapter_url": url,
                            "error": f"Failed to download audio, HTTP status: {audio_response.status}"
                        }
        else:
            logging.warning("Audio <video> tag with class 'audio-player' or 'src' attribute not found.")
            return {
                "url": url,
                "text": text,
                "audio": None
            }

    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        return {
            'url': url,
            'error': f"An unexpected error occurred: {str(e)}"
        }
    finally:
        driver.quit() 
        logging.info("WebDriver closed.")

def extract_content_nonasync(url):
    global request_count
    
    driver = create_driver()
    logging.info(f"Starting to extract data from {url}")

    try:
        driver.get(url)
        logging.info(f"Navigated to {url}. Waiting for page to load...")
        time.sleep(3)

        page_source=driver.page_source
        soup=BeautifulSoup(page_source,'html.parser')

        main_tag=soup.find('main')
        text=""

        if main_tag:
            span_tags = main_tag.find_all('span', class_='align-left')
            for span in span_tags:
                text +="\n"+span.get_text(strip=True)
            logging.info("Text extracted from main tag.")
        else:
            logging.warning("Main tag not found")

        # Find the audio/video tag
        video_tag = soup.find("video", class_='audio-player')
        if video_tag and video_tag.has_attr('src'):
            audio_url = video_tag['src']
            logging.info(f"Audio URL found")
            
            print(audio_url)
            audio_repsonse=requests.get(audio_url)
            if audio_repsonse.status_code==200:
                logging.info('Audio Downloaded Sucessfully')
                return {
                    'chapter_url':url,
                    'text':text,
                    'audio':audio_repsonse.content
                }
            else:
                logging.error(f"Failed to load audio")
                return {
                    "chapter_url":url,
                    "error":f'Failed to Download Audio'
                }
        else:
            logging.warning("Audio <video> tag with class 'audio-player or src not found")
            return {
                'url':url,
                'text':text,
                'audio':None
            }

    except Exception as e:
        logging.error(f'An unexpected error has occured: {str(e)}')
        return {
            'url':url,
            'error':f"An unexpected error has occured: {str(e)}"
        }
    finally:
        driver.quit()
        logging.info("WebDriver closed.")
        
        # Wait if request count is a multiple of 25
        if request_count % 25 == 0 and request_count!=0:
            logging.info("Request count is a multiple of 25. Waiting for some time...")
            time.sleep(random.choice([45,62,53,57]))
        
        request_count += 1


def fetch_data_nonasync(urls):
    results=[]
    if isinstance(urls,str):
        results=[extract_content_nonasync(urls)]
    for url in urls:
        results.append(extract_content_nonasync(url))
        time.sleep(random.uniform(0.5,1.5))
    print(results[0])
    return results

async def fetch_data_for_urls(urls):
    tasks = [extract_text_and_audio(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return results

if __name__ == '__main__':
    pass 