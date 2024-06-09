import keys
import feedparser
import openai
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import ftplib
import inspect
import sys

debug = False
screen = False
openai.api_key = keys.token

class feed_sum:
    max_posts = 0
    feed_file_name = './hnrsum.xml'
    entry_log_list = './hnr_entries.log'
    url = None
    feed = None
    new_feed_name = None
    new_feed_id = None
    new_feed_link = None
    new_feed_description = None
    new_feed_language = None

    def __init__(self, feed_url, new_feed_name, new_feed_id, new_feed_link, new_feed_description, new_feed_language, max_posts = 0):
        if debug: print(inspect.currentframe().f_code.co_name)

        self.url = feed_url
        self.new_feed_name = new_feed_name 
        self.new_feed_id = new_feed_id
        self.new_feed_link = new_feed_link
        self.new_feed_description = new_feed_description
        self.new_feed_language = new_feed_language
        self.max_posts = max_posts


    def process_feed(self):
        if debug: print(inspect.currentframe().f_code.co_name)

        self._create_feed()
        self._read_feed()

        process_count = 0
        for entry in self.feed['entries']:
            
            print(entry['title'])

            if self._check_if_entry_in_log(entry['title']):
                print('Already processed.')
                continue
            else:
                self._write_entry_to_log(entry['title'])

            summarized_text = self._summarize(entry['link'])

            title = entry.get('title','No title')
            link = entry.get('link','https://news.ycombinator.com')
            comments = entry.get('comments','No comments')
            published = entry.get('published', 'No date')

            self._add_feed_entry(title, link, comments, published, summarized_text)

            process_count = process_count + 1

            if process_count == self.max_posts:
                break
            
        self._write_feed()
        self._upload_file()


    def _write_entry_to_log(self, entry):
        with open(self.entry_log_list, 'a+') as file:
            file.seek(0)
            file.write(entry + '\n')
    

    def _check_if_entry_in_log(self, entry) -> bool:
        with open(self.entry_log_list, 'r') as file:
            processed_strings = file.read().splitlines()
            return entry in processed_strings
        

    def _read_feed(self):
        if debug: print(inspect.currentframe().f_code.co_name)

        self.feed = feedparser.parse(self.url)


    def _add_feed_entry(self, title, link, comments, published, summarized_text):
        if debug: print(inspect.currentframe().f_code.co_name)

        fe = self.new_feed.add_entry()
        fe.title(title)
        fe.link(href=link)
        fe.summary(summarized_text + f'\n<a href="{comments}">comments</a>')
        fe.published(published)
        # fe.comments(comments)


    def _create_feed(self):
        if debug: print(inspect.currentframe().f_code.co_name)

        self.new_feed = FeedGenerator()
        self.new_feed.id(self.new_feed_id)
        self.new_feed.title(self.new_feed_name)
        self.new_feed.link( href=self.new_feed_link, rel='alternate' )
        self.new_feed.description(self.new_feed_description)
        self.new_feed.language(self.new_feed_language)


    def _write_feed(self):
        if debug: print(inspect.currentframe().f_code.co_name)

        if screen: print(self.new_feed.rss_str(pretty=True)) 
        self.new_feed.rss_file(self.feed_file_name)


    def _get_page_text(self, url):
        if debug: print(inspect.currentframe().f_code.co_name)

        try:
            response = requests.get(url, timeout=5)
            content_type = response.headers.get('content-type')
            if response.status_code == 200:
                if 'text/html' in content_type:
                    return response.content[:10000]
        except requests.Timeout:
            print("Request timed out!")
        except requests.exceptions.RequestException:
            print("Request failed")


    def _summarize(self, url):
        if debug: print(inspect.currentframe().f_code.co_name)

        content = self._get_page_text(url)

        if content is None:
            return "Could not parse target."

        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text()
        cleaned_text = ' '.join(text.split())

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",  
            messages=[
                {
                    "role": "user",
                    "content": "Summarize the following text:\n" + cleaned_text
                }
            ],
            max_tokens=150,  
            n=1,  
            stop=None,
            temperature=0.7 
        )
        
        return response.choices[0].message.content
    

    def _upload_file(self):
        if debug: print(inspect.currentframe().f_code.co_name)

        with ftplib.FTP_TLS(keys.server_name, keys.username, keys.password) as ftp:        
            status = ftp.getwelcome()
            print(f'Connection status: {status}')
            with open(self.feed_file_name, 'rb') as file:
                ftp.storbinary('STOR ' + keys.base_folder + self.feed_file_name, file)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        posts = int(sys.argv[1])
    else:
        posts = 20
    fd = feed_sum('https://news.ycombinator.com/rss','hnrss', 'summarized', keys.destination_file, 'Description', 'en', 20)
    fd.process_feed()