# sarvam_tasks
# How to run the project

create virtual enviroment and install dependencies

    pip install -r requirements.txt 

Download the chromedriver from the browser, and extract it place it in the project directory.

Run:

    python3 main.py <base_url>

base_url: https://live.bible.is/bible/HINDPI/GEN/1

The bot will start scraping The New Testaments.
Folder Structure:

      testamen_{id}
      |----chapter_{id}
      |      |--- content.txt
             |----audio.mp3

Metadata of the files will be stored as global_metadata.json:

    {
        "testament_name": "\u092e\u0924\u094d\u0924\u0940 \u0930\u091a\u093f\u0924 \u0938\u0941\u0938\u092e\u093e\u091a\u093e\u0930",
        "testament_folder_name": "testament_0",
        "chapters": [
            {
                "chapter_id": "1",
                "chapter_url": "https://live.bible.is/bible/HINDPI/MAT/1",
                "text_file_path": "testament_0/chapter_1/content.txt",
                "audio_file_path": "testament_0/chapter_1/audio.mp3"
            },
            {
                "chapter_id": "2",
                "chapter_url": "https://live.bible.is/bible/HINDPI/MAT/2",
                "text_file_path": "testament_0/chapter_2/content.txt",
                "audio_file_path": "testament_0/chapter_2/audio.mp3"
            },]}
      

  
