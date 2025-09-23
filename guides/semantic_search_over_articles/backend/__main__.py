# main.py
import asyncio
import json
import argparse
from dotenv import load_dotenv

# Internal imports
from indexer_ze import ZeroEntropyArticleIndexer
from search_ze import ZeroEntropyArticleSearcher
from utils_ze import ZeroEntropyUtils
from logger import getLogger

# Load environment variables
load_dotenv()

# Configure logger to display log messages
logger = getLogger()


class ZeroEntropyArticleManager:
    """
    Main class that orchestrates RSS scraping, indexing, and searching using ZeroEntropy.
    """

    def __init__(self, collection_name: str = "articles"):
        self.collection_name = collection_name
        self.indexer = ZeroEntropyArticleIndexer(collection_name)
        self.searcher = ZeroEntropyArticleSearcher(collection_name)
        self.utils = ZeroEntropyUtils(collection_name)

    async def scrape_and_index(self):
        """Scrape RSS feeds and index articles"""
        # Initialize RSS feed URLs
        rss_public_urls = [
            "https://www.public.fr/feed",
            "https://www.public.fr/people/feed",
            "https://www.public.fr/tele/feed",
            "https://www.public.fr/mode/feed",
            "https://www.public.fr/people/familles-royales/feed",
        ]

        rss_vsd_urls = [
            "https://vsd.fr/actu-people/feed/",
            "https://vsd.fr/tele/feed/",
            "https://vsd.fr/societe/feed/",
            "https://vsd.fr/culture/feed/",
            "https://vsd.fr/loisirs/feed/",
        ]

        # Initialize collection
        await self.indexer.initialize_collection()

        # Extract content from RSS feeds
        articles = []
        for url in rss_public_urls + rss_vsd_urls:
            content = self.indexer.get_rss_feed_content(url)
            if content:
                articles.extend(content)
                logger.info("Successfully extracted content from %s", url)
            else:
                logger.warning("Failed to extract content from %s", url)

        # Save all content to a JSON file for backup
        with open("articles.json", "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=4)

        logger.info(f"Extracted {len(articles)} articles total")

        # Index articles in ZeroEntropy
        if articles:
            await self.indexer.index_articles(articles)
            logger.info("Successfully scraped and indexed articles in ZeroEntropy.")
        else:
            logger.warning("No articles to index.")

    async def search_articles(
        self,
        query: str,
        search_type: str = "documents",
        k: int = 10,
        filter_creator: str = None,
        filter_category: str = None,
        reranker: str = "zerank-1-small",
        show_status: bool = False,
    ):
        """Search for articles"""
        # Show status if requested
        if show_status:
            await self.searcher.get_collection_status()

        # Prepare filter if specified
        filter_dict = {}
        if filter_creator:
            filter_dict["creator"] = {"$eq": filter_creator}
        if filter_category:
            filter_dict["categories"] = {"$eq": filter_category}

        filter_dict = filter_dict if filter_dict else None

        # Perform search based on type
        if search_type == "documents":
            results = await self.searcher.search_documents(
                query=query,
                k=k,
                filter_dict=filter_dict,
                reranker=reranker,
            )
            self.searcher.display_document_results(results, query)

        elif search_type == "snippets":
            results = await self.searcher.search_snippets(
                query=query,
                k=k,
                filter_dict=filter_dict,
                reranker=reranker,
            )
            self.searcher.display_snippet_results(results, query)

        elif search_type == "pages":
            results = await self.searcher.search_pages(
                query=query, k=k, filter_dict=filter_dict
            )
            self.searcher.display_page_results(results, query)

        elif search_type == "advanced":
            results = await self.utils.search_and_rerank(
                query=query, k=k * 2, rerank_top_n=k
            )
            self.utils.display_advanced_results(results, query)

        return results

    async def manage_collections(self, action: str, collection_name: str = None):
        """Manage collections (list, delete, status)"""
        if action == "list":
            collections = await self.utils.list_all_collections()
            logger.info(f"Available collections: {collections}")
            return collections

        elif action == "delete" and collection_name:
            success = await self.utils.delete_collection(collection_name)
            if success:
                logger.info(f"Successfully deleted collection: {collection_name}")
            else:
                logger.info(f"Failed to delete collection: {collection_name}")
            return success

        elif action == "status":
            status = await self.searcher.get_collection_status()
            return status

        else:
            logger.info("Invalid action or missing collection name")
            return None


async def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="ZeroEntropy RSS Article Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Scrape RSS feeds and index articles")
    scrape_parser.add_argument("--collection", type=str, default="articles",
                               help="Collection name to use")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search for articles")
    search_parser.add_argument("query", type=str, help="Search query string")
    search_parser.add_argument("--k", type=int, default=10, help="Number of results to return")
    search_parser.add_argument("--search-type", choices=["documents", "snippets", "pages", "advanced"],
                               default="documents", help="Type of search to perform")
    search_parser.add_argument("--collection", type=str, default="articles",
                               help="Collection name to search in")
    search_parser.add_argument("--filter-creator", type=str, help="Filter by creator/author")
    search_parser.add_argument("--filter-category", type=str, help="Filter by category")
    search_parser.add_argument("--status", action="store_true",
                               help="Show collection status before searching")
    search_parser.add_argument("--reranker", type=str, default="zerank-1-small",
                               help="Reranker model to use")

    # Collection management command
    manage_parser = subparsers.add_parser("manage", help="Manage collections")
    manage_parser.add_argument("action", choices=["list", "delete", "status"],
                               help="Management action to perform")
    manage_parser.add_argument("--collection", type=str, help="Collection name (required for delete)")

    # Parse arguments
    args = parser.parse_args()

    if args.command == "scrape":
        # Initialize manager and scrape
        manager = ZeroEntropyArticleManager(args.collection)
        await manager.scrape_and_index()

    elif args.command == "search":
        # Initialize manager and search
        manager = ZeroEntropyArticleManager(args.collection)
        await manager.search_articles(
            query=args.query,
            search_type=args.search_type,
            k=args.k,
            filter_creator=args.filter_creator,
            filter_category=args.filter_category,
            reranker=args.reranker,
            show_status=args.status
        )

    elif args.command == "manage":
        # Initialize manager and manage collections
        manager = ZeroEntropyArticleManager()
        await manager.manage_collections(
            action=args.action,
            collection_name=args.collection
        )


if __name__ == "__main__":
    # Run the main async function
    asyncio.run(main())
