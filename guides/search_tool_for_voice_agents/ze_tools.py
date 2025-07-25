import os
import dotenv
import json

from agents import Agent, Runner, function_tool, FunctionTool
from zeroentropy import ZeroEntropy

# Load environment variables
dotenv.load_dotenv()
ZEROENTROPY_API_KEY = os.getenv("ZEROENTROPY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "yc_voice_agent_support")

# Initialize SDK client
ze_client = ZeroEntropy(api_key=ZEROENTROPY_API_KEY)

SYSTEM_PROMPT = "You are a helpful voice assistant who can answer any question about any YC company"

@function_tool
def top_documents(query: str, k: int = 3) -> list[dict]:
    """
    Retrieve top documents from the ZeroEntropy collection using a query.

    Args:
        query: The search string to run against the collection.
        k: The number of top documents to return.

    Returns:
        A string containing the top documents' content and paths.
    """
    try:
        print(f"Querying ZeroEntropy collection for top documents: {COLLECTION_NAME}")
        response = ze_client.queries.top_documents(
            collection_name=COLLECTION_NAME,
            query=query,
            k=k,
        )
        return response.results
    except Exception as e:
        return f"❌ Error fetching top documents: {str(e)}"



@function_tool
def rerank_documents(query: str, documents: list[str], model: str = "zerank-1", top_n: int = 3) -> str:
    """
    Reranks the provided documents, according to the provided query.

    Args:
        query: The search string to run against the collection.
        documents: The list of documents to rerank.
        model: The model to use for reranking.
        top_n: The number of top documents to return.

    Returns:
        A string containing the reranked documents.
    """
    try:
        print(f"Querying ZeroEntropy collection for reranking: {COLLECTION_NAME}")
        response = ze_client.models.rerank(
            query=query,
            documents=documents,
        )
        return response.results
    except Exception as e:
        return f"❌ Error reranking documents: {str(e)}"


@function_tool
def add_document(content: str, path: str, collection_name: str = COLLECTION_NAME) -> str:
    """
    Adds a document to a given collection.

    Args:
        collection_name (str): The name of the collection to add the document to. 
            A 404 Not Found status code will be returned if this collection name does not exist.
        path (str): The path of the document to add. 
            A 409 Conflict status code will be returned if this path already exists.
        content (dict): The content of the document to add. Must be one of three types:
            
            For text documents:
            {
                "type": "text",
                "text": "The content of this document, as a text string"
            }
            
            For paginated text documents:
            {
                "type": "text-pages", 
                "pages": ["Page 1 content", "Page 2 content", ...]
            }
            Note: Pages are 0-indexed, so the first page has index 0, second has index 1, etc.
            
            For binary documents:
            {
                "type": "auto",
                "base64_data": "base64-encoded string of the file's raw data"
            }
            Note: File extension and binary data are used to automatically deduce filetype.
        
    Returns:
        A string containing the result of the document addition.
    """
    try:
        print(f"Adding document to ZeroEntropy collection: {collection_name}")
        response = ze_client.documents.add(
            collection_name=collection_name,
            document=content,
            path=path,
        )
        return response.results
    except Exception as e:
        return f"❌ Error adding document: {str(e)}"

@function_tool
def delete_document(collection_name: str, path: str) -> dict:
    """
    Delete a document from a collection
    Args:
        collection_name (str): The name of the collection to delete the document from.
        path (str): The path of the document to delete.
    Returns:
        dict: A dictionary with a success key and a message key
    """
    try:
        ze_client.documents.delete(collection_name=collection_name, path=path)
        return {
            "success": True,
            "message": f"Document '{path}' deleted from collection '{collection_name}'"
        }
    except Exception as e:
        return f"❌ Error deleting document: {str(e)}"

@function_tool
def get_document_info(collection_name: str, path: str, include_content: bool = False) -> dict:
        """
        Get information about a document
        Args:
            collection_name (str): The name of the collection to get the document from.
            path (str): The path of the document to get the information about.
            include_content (bool): Whether to include the content of the document. Defaults to False.
        Returns:
            dict: A dictionary with the document information
        """
        response = ze_client.documents.get_info(collection_name=collection_name, path=path, include_content=include_content)
        return response.document.model_dump()

@function_tool
def get_document_info_list(collection_name: str, limit: int = 1024, path_prefix: str | None = None, path_gt: str | None = None) -> list[dict]:
        """
        Get a list of documents in a collection
        Args:
            collection_name (str): The name of the collection to get the document list from.
            limit (int): The maximum number of documents to return. Defaults to 1024.
            path_prefix (str | None): All documents returned will have a path that starts with the provided path prefix.
            path_gt (str | None): All documents returned will have a path that is greater than the provided path.
        Returns:
            list[dict]: A list of dictionaries with the document information
        """
        response = ze_client.documents.get_info_list(
            collection_name=collection_name, limit=limit, path_prefix=path_prefix, path_gt=path_gt
        )
        
        return [doc.model_dump() for doc in response.documents]

@function_tool
def get_page_info(collection_name: str, path: str, page_index: int, include_content: bool = False) -> dict:
        """
        Get information about a page of a document
        Args:
            collection_name (str): The name of the collection to get the page from.
            path (str): The path of the document to get the page from.
            page_index (int): The index of the page to get the information about.
            include_content (bool): Whether to include the content of the page. Defaults to False.
        Returns:
            dict: A dictionary with the page information
        """
        response = ze_client.documents.get_page_info(collection_name=collection_name, path=path, page_index=page_index, include_content=include_content)
        return response.page.model_dump()


if __name__ == "__main__":
    agent = Agent(
        name="ZeroEntropyVoiceAgent",
        instructions=SYSTEM_PROMPT,
        model="gpt-4.1-mini",
        tools=[top_documents, rerank_documents, add_document, delete_document, get_document_info, get_document_info_list, get_page_info],
    )
    for tool in agent.tools:
        if isinstance(tool, FunctionTool):
            print(tool.name)
            print(tool.description)
            print(json.dumps(tool.params_json_schema, indent=2))
            print()

    runner = Runner.run_sync(agent, "What are best healthcare companies in YC?")
    print(runner.final_output)
