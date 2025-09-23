# indexer_ze.py
import requests
from typing import List, Dict
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from zeroentropy import AsyncZeroEntropy, ConflictError

# Logger import
from logger import getLogger

# Load environment variables
load_dotenv()

# Configure logger to display log messages
logger = getLogger()


class ZeroEntropyArticleIndexer:
    """
    ZeroEntropyArticleIndexer handles RSS feed scraping and article indexing using ZeroEntropy API.
    """
    def __init__(self, collection_name: str = "articles"):
        self.collection_name = collection_name
        self.zclient = AsyncZeroEntropy()

    async def initialize_collection(self):
        """
        Initialize ZeroEntropy collection. Creates a new collection in ZeroEntropy if it doesn't exist.
        If the collection already exists, logs a message and continues.

        Raises
        ------
        ConflictError
            If there's a conflict during collection creation (handled gracefully)
        """
        try:
            await self.zclient.collections.add(collection_name=self.collection_name)
            logger.info(f"Created new collection: {self.collection_name}")
        except ConflictError:
            logger.error(f"Collection '{self.collection_name}' already exists")

    @staticmethod
    def get_rss_feed_content(url: str) -> List[Dict]:
        """
        Extract content from an RSS feed URL and returns a list of dictionaries containing the extracted content.

        Parameters
        ----------
        url : str
            The RSS feed URL to extract content from

        Returns
        -------
        List[Dict]
            A list of dictionaries, each containing article information with keys:
            - title : str
                The article title
            - creator : str
                The article author/creator
            - categories : List[str]
                List of article categories
            - description : str
                Brief description of the article
            - pub_date : str
                Publication date of the article
            - content : str
                Full cleaned text content of the article
            - source_url : str
                The original RSS feed URL

        Raises
        ------
        requests.exceptions.HTTPError
            If the HTTP request fails
        requests.exceptions.RequestException
            If there's a general request error
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"  # noqa: E501
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response.encoding = "utf-8"

        soup = BeautifulSoup(response.content, "xml")
        items = soup.find_all("item")
        content_list = []

        for item in items:
            title = item.find("title").get_text(strip=True) if item.find("title") else "N/A"
            creator = item.find("dc:creator").get_text(strip=True) if item.find("dc:creator") else "N/A"
            categories = [category.get_text(strip=True) for category in item.find_all("category")]
            description = item.find("description").get_text(strip=True) if item.find("description") else "N/A"
            publication_date = item.find("pubDate").get_text(strip=True) if item.find("pubDate") else "N/A"
            content_encoded = (
                item.find("content:encoded").get_text(strip=True) if item.find("content:encoded") else "N/A"
            )

            # Clean up HTML content
            content_text = ""
            if content_encoded != "N/A":
                content_encoded_soup = BeautifulSoup(content_encoded, "html.parser")
                for script_or_style in content_encoded_soup(["script", "style"]):
                    script_or_style.decompose()
                content_text = content_encoded_soup.get_text(separator=" ", strip=True).replace("\n", " ")
            else:
                description_soup = BeautifulSoup(description, "html.parser")
                for script_or_style in description_soup(["script", "style"]):
                    script_or_style.decompose()
                content_text = description_soup.get_text(separator=" ", strip=True).replace("\n", " ")

            content_list.append({
                "title": title,
                "creator": creator,
                "categories": categories,
                "description": description,
                "pub_date": publication_date,
                "content": content_text,
                "source_url": url
            })

        return content_list

    async def index_articles(self, articles: List[Dict]):
        """
        Index articles in ZeroEntropy using the documents API.

        Takes a list of article dictionaries and indexes them in the ZeroEntropy
        collection. Creates unique document paths and prepares metadata for each article.

        Parameters
        ----------
        articles : List[Dict]
            List of article dictionaries containing article information.
            Each dictionary should have keys: title, creator, categories,
            description, pub_date, content, source_url
        """
        indexed_count = 0
        failed_count = 0

        for idx, article in enumerate(articles):
            try:
                # Create unique document path
                doc_path = f"article_{idx}_{hash(article['title'][:50])}"

                # Prepare content for indexing - combine title, description, and content
                full_content = f"Title: {article['title']}\n\n"
                full_content += f"Description: {article['description']}\n\n"
                full_content += f"Content: {article['content']}"

                # Prepare metadata
                metadata = {
                    "title": article["title"][:500],  # Limit length for metadata
                    "creator": article["creator"][:200],
                    "categories": ", ".join(article["categories"][:5])[:300],  # Limit categories
                    "pub_date": article["pub_date"][:100],
                    "source_url": article["source_url"][:300],
                    "type": "rss_article",
                }

                # Add document to ZeroEntropy
                await self.zclient.documents.add(
                    collection_name=self.collection_name,
                    path=doc_path,
                    content={"type": "text", "text": full_content},
                    metadata=metadata,
                )

                indexed_count += 1
                if indexed_count % 10 == 0:
                    logger.info(f"Indexed {indexed_count} articles...")

            except ConflictError:
                logger.warning(f"Article {idx} already exists, skipping...")
                continue

        logger.info(f"Indexing complete. Success: {indexed_count}, Failed: {failed_count}")
