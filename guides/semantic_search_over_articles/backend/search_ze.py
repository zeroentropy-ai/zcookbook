# search_ze.py
from dotenv import load_dotenv
from zeroentropy import AsyncZeroEntropy

# Logger import
from logger import getLogger

# Load environment variables
load_dotenv()

# Configure logger to display log messages
logger = getLogger()


class ZeroEntropyArticleSearcher:
    """
    ZeroEntropyArticleSearcher handles article searching using ZeroEntropy's advanced retrieval capabilities.

    Parameters
    ----------
    collection_name : str, optional
        Name of the ZeroEntropy collection to search in, by default "articles"

    Attributes
    ----------
    collection_name : str
        The name of the ZeroEntropy collection
    zclient : AsyncZeroEntropy
        The ZeroEntropy async client instance
    """

    def __init__(self, collection_name: str = "articles"):
        self.collection_name = collection_name
        self.zclient = AsyncZeroEntropy()

    async def search_documents(
        self,
        query: str,
        k: int = 10,
        filter_dict: dict = None,
        include_metadata: bool = True,
        reranker: str = "zerank-1-small",
    ) -> list:
        """Search for documents using ZeroEntropy's top_documents query.

        Parameters
        ----------
        query : str
            The search query string
        k : int, optional
            Number of top results to return, by default 10
        filter_dict : dict, optional
            Dictionary containing filters for metadata fields, by default None
        include_metadata : bool, optional
            Whether to include document metadata in results, by default True
        reranker : str, optional
            Name of the reranker model to use, by default "zerank-1-small"

        Returns
        -------
        List:
            List of document result dictionaries, each containing:
            - path : str
                Unique document path identifier
            - score : float
                Relevance score for the document
            - file_url : str or None
                URL to access the full document file
            - metadata : Dict
                Document metadata including title, creator, categories, etc.
        """
        response = await self.zclient.queries.top_documents(
            collection_name=self.collection_name,
            query=query,
            k=k,
            filter=filter_dict,
            include_metadata=include_metadata,
            reranker=reranker,
            latency_mode="low",
        )

        # Convert Result objects to dictionaries
        results = []
        for result in response.results:
            result_dict = {
                'path': result.path,
                'score': result.score,
                'file_url': getattr(result, 'file_url', None),
                'metadata': getattr(result, 'metadata', {})
            }
            results.append(result_dict)

        return results

    async def search_snippets(
        self,
        query: str,
        k: int = 10,
        filter_dict: dict = None,
        precise_responses: bool = True,
        reranker: str = "zerank-1-small",
    ) -> list:
        """
        Search for specific snippets using ZeroEntropy's top_snippets query.

        Parameters
        ----------
        query : str
            The search query string
        k : int, optional
            Number of top snippets to return, by default 10
        filter_dict : dict, optional
            Dictionary containing filters for metadata fields, by default None
        precise_responses : bool, optional
            Whether to return precise snippet boundaries, by default True
        reranker : str, optional
            Name of the reranker model to use, by default "zerank-1-small"

        Returns
        -------
        List:
            List of snippet result dictionaries, each containing:
            - path : str
                Document path where the snippet was found
            - score : float
                Relevance score for the snippet
            - start_index : int
                Starting character index of the snippet in the document
            - end_index : int
                Ending character index of the snippet in the document
            - page_span : List[int]
                List indicating which pages the snippet spans
            - content : str
                The actual text content of the snippet
            - metadata : Dict
                Document metadata including title, creator, categories, etc.
        """
        response = await self.zclient.queries.top_snippets(
            collection_name=self.collection_name,
            query=query,
            k=k,
            filter=filter_dict,
            precise_responses=precise_responses,
            include_document_metadata=True,
            reranker=reranker,
        )

        # Convert Result objects to dictionaries
        results = []
        for result in response.results:
            result_dict = {
                'path': result.path,
                'score': result.score,
                'start_index': getattr(result, 'start_index', 0),
                'end_index': getattr(result, 'end_index', 0),
                'page_span': getattr(result, 'page_span', []),
                'content': getattr(result, 'content', ''),
                'metadata': getattr(result, 'metadata', {})
            }
            results.append(result_dict)

        return results

    async def search_pages(
        self,
        query: str,
        k: int = 10,
        filter_dict: dict = None,
        include_content: bool = True,
    ) -> list:
        """
        Search for pages using ZeroEntropy's top_pages query.

        Parameters
        ----------
        query : str
            The search query string
        k : int, optional
            Number of top pages to return, by default 10
        filter_dict : dict, optional
            Dictionary containing filters for metadata fields, by default None
        include_content : bool, optional
            Whether to include page content in results, by default True

        Returns
        -------
        List:
            List of page result dictionaries, each containing:
            - path : str
                Document path containing the page
            - score : float
                Relevance score for the page
            - page_index : int
                Index of the page within the document (0-based)
            - content : str
                The text content of the page (if include_content=True)
            - metadata : Dict
                Document metadata including title, creator, categories, etc.
        """
        response = await self.zclient.queries.top_pages(
            collection_name=self.collection_name,
            query=query,
            k=k,
            filter=filter_dict,
            include_content=include_content,
            latency_mode="low",
        )

        # Convert Result objects to dictionaries
        results = []
        for result in response.results:
            result_dict = {
                'path': result.path,
                'score': result.score,
                'page_index': getattr(result, 'page_index', 0),
                'content': getattr(result, 'content', ''),
                'metadata': getattr(result, 'metadata', {})
            }
            results.append(result_dict)

        return results

    @staticmethod
    def display_document_results(results: list, query: str) -> None:
        """
        Display document search results in a formatted way.

        Parameters
        ----------
        results : list
            List of document result dictionaries from search_documents()
        query : str
            The original search query string for display purposes
        """
        if not results:
            print(f"No results found for query: '{query}'")
            return

        print(f"\n{'=' * 60}")
        print(f"DOCUMENT SEARCH RESULTS FOR: '{query}'")
        print(f"Found {len(results)} results")
        print(f"{'=' * 60}\n")

        for i, result in enumerate(results, 1):
            print(f"Result {i}")
            print(f"Document Path: {result['path']}")
            print(f"Relevance Score: {result['score']:.4f}")

            if result.get("metadata"):
                metadata = result["metadata"]
                print(f"Title: {metadata.get('title', 'N/A')}")
                print(f"Author: {metadata.get('creator', 'N/A')}")
                print(f"Publication Date: {metadata.get('pub_date', 'N/A')}")
                print(f"Categories: {metadata.get('categories', 'N/A')}")
                print(f"Source URL: {metadata.get('source_url', 'N/A')}")

            # NOTE: file_url contains sensitive tokens - UNCOMMENT ONLY FOR DEBUGGING/TESTING
            if result.get("file_url"):
                # print(f"File URL: {result['file_url']}")
                print("File URL: [Available - hidden for security]")

            print("\n" + "-" * 50 + "\n")

    @staticmethod
    def display_snippet_results(results: list, query: str):
        """Display snippet search results in a formatted way.

        Parameters
        ----------
        results : list
            List of snippet result dictionaries from search_snippets()
        query : str
            The original search query string for display purposes
        """
        if not results:
            print(f"No snippets found for query: '{query}'")
            return

        print(f"\n{'=' * 60}")
        print(f"SNIPPET SEARCH RESULTS FOR: '{query}'")
        print(f"Found {len(results)} snippets")
        print(f"{'=' * 60}\n")

        for i, result in enumerate(results, 1):
            print(f"Snippet {i}")
            print(f"Document Path: {result['path']}")
            print(f"Relevance Score: {result['score']:.4f}")
            print(f"Character Range: {result['start_index']}-{result['end_index']}")
            print(f"Page Span: {result['page_span']}")

            if result.get("content"):
                print(f"Content: {result['content'][:300]}...")

            if result.get("metadata"):
                metadata = result["metadata"]
                print(f"Title: {metadata.get('title', 'N/A')}")
                print(f"Author: {metadata.get('creator', 'N/A')}")

            print("\n" + "-" * 40 + "\n")

    @staticmethod
    def display_page_results(results: list, query: str):
        """
        Display page search results in a formatted way.

        Parameters
        ----------
        results : list
            List of page result dictionaries from search_pages()
        query : str
            The original search query string for display purposes
        """
        if not results:
            print(f"No page results found for query: '{query}'")
            return

        print(f"\n{'=' * 60}")
        print(f"PAGE SEARCH RESULTS FOR: '{query}'")
        print(f"Found {len(results)} page results")
        print(f"{'=' * 60}\n")

        for i, result in enumerate(results, 1):
            print(f"Page {i}")
            print(f"Document Path: {result['path']}")
            print(f"Page Index: {result['page_index']}")
            print(f"Relevance Score: {result['score']:.4f}")

            if result.get("content"):
                print(f"Content: {result['content'][:300]}...")

            if result.get("metadata"):
                metadata = result["metadata"]
                print(f"Title: {metadata.get('title', 'N/A')}")
                print(f"Author: {metadata.get('creator', 'N/A')}")

            print("\n" + "-" * 40 + "\n")

    async def get_collection_status(self):
        """Get and display collection status information.

        Returns
        -------
        status : object
            ZeroEntropy status response object containing collection statistics

        Notes
        -----
        Prints collection status including total documents, indexed documents,
        documents currently being parsed/indexed, and failed documents.
        This is useful for monitoring the health and progress of document indexing.
        """
        status = await self.zclient.status.get(collection_name=self.collection_name)
        print(f"\nCollection Status for '{self.collection_name}':")
        print(f"Total Documents: {status.num_documents}")
        print(f"Indexed Documents: {status.num_indexed_documents}")
        print(f"Parsing Documents: {status.num_parsing_documents}")
        print(f"Indexing Documents: {status.num_indexing_documents}")
        print(f"Failed Documents: {status.num_failed_documents}")
        return status
