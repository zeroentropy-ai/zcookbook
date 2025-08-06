# utils_ze.py
from dotenv import load_dotenv
from zeroentropy import AsyncZeroEntropy

# Logger import
from logger import getLogger

# Load environment variables
load_dotenv()

# Configure logger to display log messages
logger = getLogger()


class ZeroEntropyUtils:
    """
    Utility class for advanced ZeroEntropy operations including reranking, collection management, and batch operations.

    Parameters
    ----------
    collection_name : str, optional
        Name of the default ZeroEntropy collection to work with, by default "articles"

    Attributes
    ----------
    collection_name : str
        The default collection name for operations
    zclient : AsyncZeroEntropy
        The ZeroEntropy async client instance
    """
    def __init__(self, collection_name: str = "articles"):
        self.collection_name = collection_name
        self.zclient = AsyncZeroEntropy()

    async def rerank_documents(
        self,
        query: str,
        document_texts: list,
        model: str = "zerank-1-small",
        top_n: int = 10,
    ) -> list:
        """
        Use ZeroEntropy's reranking model to rerank a list of documents.

        Parameters
        ----------
        query : str
            The search query to use for reranking
        document_texts : list
            List of document text strings to be reranked
        model : str, optional
            Name of the reranking model to use, by default "zerank-1-small"
        top_n : int, optional
            Number of top reranked results to return, by default 10

        Returns
        -------
        list
            List of reranked result dictionaries, each containing:
            - index : int
                Original index of the document in the input list
            - relevance_score : float
                Reranking relevance score for the document
        """
        response = await self.zclient.models.rerank(
            query=query, documents=document_texts, model=model, top_n=top_n
        )
        return response.results

    async def list_all_collections(self) -> list:
        """
        List all available collections in the ZeroEntropy instance.

        Returns
        -------
        list
            List of collection names available in the ZeroEntropy instance
        """
        response = await self.zclient.collections.get_list()
        return response.collection_names

    async def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection from ZeroEntropy.

        Parameters
        ----------
        collection_name : str
            Name of the collection to delete

        Returns
        -------
        bool
            True if deletion was successful
        """
        await self.zclient.collections.delete(collection_name=collection_name)
        logger.info(f"Successfully deleted collection: {collection_name}")
        return True

    async def list_documents_in_collection(
        self, collection_name: str = None, limit: int = 100
    ) -> list:
        """
        List all documents in a collection with pagination support.

        Parameters
        ----------
        collection_name : str, optional
            Name of the collection to list documents from. If None, uses the default
            collection name, by default None
        limit : int, optional
            Maximum number of documents to return, by default 100

        Returns
        -------
        list
            List of document metadata dictionaries containing information about
            each document in the collection
        """
        if collection_name is None:
            collection_name = self.collection_name

        response = await self.zclient.documents.get_info_list(
            collection_name=collection_name, limit=limit
        )
        return response.documents

    async def get_document_info(
        self,
        path: str,
        collection_name: str = None,
        include_content: bool = False,
    ) -> dict:
        """
        Get detailed information about a specific document.

        Parameters
        ----------
        path : str
            Unique path identifier of the document
        collection_name : str, optional
            Name of the collection containing the document. If None, uses the default
            collection name, by default None
        include_content : bool, optional
            Whether to include the full document content in the response, by default False

        Returns
        -------
        Optional[Dict]
            Dictionary containing document information including metadata, status,
            and optionally the full content. Returns None if document not found.
        """
        if collection_name is None:
            collection_name = self.collection_name

        response = await self.zclient.documents.get_info(
            collection_name=collection_name,
            path=path,
            include_content=include_content,
        )
        return response.document

    async def update_document_metadata(
        self, path: str, metadata: dict, collection_name: str = None
    ) -> bool:
        """
        Update metadata for a specific document.

        Parameters
        ----------
        path : str
            Unique path identifier of the document to update
        metadata : Dict[str, str]
            Dictionary of metadata keys and values to update
        collection_name : str, optional
            Name of the collection containing the document. If None, uses the default
            collection name, by default None

        Returns
        -------
        bool
            True if the metadata update was successful
        """
        if collection_name is None:
            collection_name = self.collection_name

        await self.zclient.documents.update(
            collection_name=collection_name, path=path, metadata=metadata
        )
        logger.info(f"Successfully updated metadata for document: {path}")
        return True

    async def delete_document(
        self, path: str, collection_name: str = None
    ) -> bool:
        """
        Delete a specific document from a collection.

        Parameters
        ----------
        path : str
            Unique path identifier of the document to delete
        collection_name : str, optional
            Name of the collection containing the document. If None, uses the default
            collection name, by default None

        Returns
        -------
        bool
            True if the document deletion was successful
        """
        if collection_name is None:
            collection_name = self.collection_name

        await self.zclient.documents.delete(
            collection_name=collection_name, path=path
        )
        logger.info(f"Successfully deleted document: {path}")
        return True

    async def batch_delete_documents(
        self, paths: list, collection_name: str = None
    ) -> dict:
        """
        Delete multiple documents in batch operation.

        Parameters
        ----------
        paths : list
            List of document path identifiers to delete
        collection_name : str, optional
            Name of the collection containing the documents. If None, uses the default
            collection name, by default None

        Returns
        -------
        Dict[str, bool]
            Dictionary mapping each document path to its deletion success status.
            True indicates successful deletion, False indicates failure.
        """
        if collection_name is None:
            collection_name = self.collection_name

        results = {}
        for path in paths:
            success = await self.delete_document(path, collection_name)
            results[path] = success

        return results

    async def search_and_rerank(
        self,
        query: str,
        k: int = 20,
        rerank_top_n: int = 10,
        collection_name: str = None,
    ) -> list:
        """
        Advanced search that first retrieves more documents, then reranks them for improved relevance.

        Parameters
        ----------
        query : str
            The search query string
        k : int, optional
            Number of initial documents to retrieve before reranking, by default 20
        rerank_top_n : int, optional
            Number of top documents to return after reranking, by default 10
        collection_name : str, optional
            Name of the collection to search in. If None, uses the default
            collection name, by default None

        Returns
        -------
        list
            List of reranked document result dictionaries, each containing:
            - All original document fields (path, metadata, etc.)
            - original_score : float
                The original search relevance score
            - rerank_score : float
                The improved relevance score from reranking
        """
        if collection_name is None:
            collection_name = self.collection_name

        # First, get more documents than needed
        search_results = await self.zclient.queries.top_documents(
            collection_name=collection_name,
            query=query,
            k=k,
            include_metadata=True,
            latency_mode="low",
        )

        if not search_results.results:
            return []

        # Extract document texts for reranking
        document_texts = []
        for result in search_results.results:
            # Get full document content
            doc_info = await self.get_document_info(
                path=result["path"],
                collection_name=collection_name,
                include_content=True,
            )
            if doc_info and doc_info.get("content"):
                document_texts.append(doc_info["content"])
            else:
                # Fallback to using metadata if content not available
                metadata = result.get("metadata", {})
                fallback_text = (
                    f"{metadata.get('title', '')} {metadata.get('description', '')}"
                )
                document_texts.append(fallback_text)

        # Rerank the documents
        rerank_results = await self.rerank_documents(
            query=query,
            document_texts=document_texts,
            top_n=min(rerank_top_n, len(document_texts)),
        )

        # Combine rerank results with original metadata
        final_results = []
        for rerank_result in rerank_results:
            original_result = search_results.results[rerank_result["index"]]
            final_results.append(
                {
                    **original_result,
                    "rerank_score": rerank_result["relevance_score"],
                    "original_score": original_result["score"],
                }
            )

        return final_results

    def display_advanced_results(self, results: list, query: str):
        """
        Display results with both original and rerank scores in a formatted way.

        Parameters
        ----------
        results : list
            List of advanced search result dictionaries from search_and_rerank()
        query : str
            The original search query string for display purposes
        """
        if not results:
            print(f"No results found for query: '{query}'")
            return

        print(f"\n{'='*70}")
        print(f"ADVANCED SEARCH & RERANK RESULTS FOR: '{query}'")
        print(f"Found {len(results)} results")
        print(f"{'='*70}\n")

        for i, result in enumerate(results, 1):
            print(f"Result {i}")
            print(f"Document Path: {result['path']}")
            print(f"Original Score: {result['original_score']:.4f}")
            print(f"Rerank Score: {result['rerank_score']:.4f}")

            if result.get("metadata"):
                metadata = result["metadata"]
                print(f"Title: {metadata.get('title', 'N/A')}")
                print(f"Author: {metadata.get('creator', 'N/A')}")
                print(f"Publication Date: {metadata.get('pub_date', 'N/A')}")
                print(f"Categories: {metadata.get('categories', 'N/A')}")

            print("\n" + "-" * 60 + "\n")
