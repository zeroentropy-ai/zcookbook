import os
import time
import threading
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from zeroentropy import ZeroEntropy
from slack_sdk.webhook import WebhookClient
from index import index_document
from query import query_collection
from dotenv import load_dotenv
load_dotenv()


# --- Configuration ---
FOLDER_TO_WATCH = './example'  # Folder to monitor
COLLECTION_NAME = 'example'
# Add queries depending on the use case
QUERIES = [
    'security vulnerability'
]
# For now the implementation supports slack alerts.
ALERT_METHOD = 'slack' 

SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL') 
API_KEY = os.getenv('ZEROENTROPY_API_KEY')



zclient = ZeroEntropy(api_key=API_KEY)

# sending alert via slack 
def send_slack_alert(message):
    webhook = WebhookClient(SLACK_WEBHOOK_URL)
    response = webhook.send(text=message)
    if response.status_code != 200:
        print(f"Failed to send Slack alert: {response.status_code}")
    else: 
        print(f"Slack alert sent successfully: {response.status_code}")


# Indexing and querying the documents and sending alerts if relevant content is found.
def index_and_alert(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext not in ['.txt', '.pdf', '.csv']:
        print(f'Skipping unsupported file type: {filepath}')
        return
    
    async def async_index_and_query():
        try:
            await index_document(filepath, COLLECTION_NAME)
            print(f'Indexed: {filepath}')
            for query in QUERIES:
                results = await query_collection(COLLECTION_NAME, query, top_k_csv=1, top_k_txt=1)
                if results and hasattr(results[0], 'score') and results[0].score > 0.2:
                    alert_msg = f'Relevant content found for query "{query}" in file {filepath}.'
                    send_slack_alert(alert_msg)
        except Exception as e:
            print(f'Error indexing or querying {filepath}: {e}')
    
    # Run the async function in a new event loop in a thread
    threading.Thread(target=lambda: asyncio.run(async_index_and_query())).start()

# Watchdog handler to monitor the folder for new files and modified files.
class NewFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            threading.Thread(target=index_and_alert, args=(event.src_path,)).start()
    def on_modified(self, event):
        if not event.is_directory:
            threading.Thread(target=index_and_alert, args=(event.src_path,)).start()

def main():
    # check if collection exists and create it if it doesn't
    try:
        zclient.collections.add(collection_name=COLLECTION_NAME)
    except Exception:
        pass  
    
    # Start monitoring
    event_handler = NewFileHandler()
    observer = Observer()
    observer.schedule(event_handler, FOLDER_TO_WATCH, recursive=False)
    observer.start()
    print(f'Watching folder: {FOLDER_TO_WATCH}')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == '__main__':
    main() 