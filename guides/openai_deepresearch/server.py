"""
Sample MCP Server for ZeroEntropy's ChatGPT Deep Research Integration

This server implements the Model Context Protocol (MCP) with search and fetch
capabilities designed to work with ChatGPT's deep research feature.

This will require installing the dependencies in requirements.txt. Hosting can be done on a cloud provider, but the easiest is replit!
"""

import logging
import uvicorn
import os
from typing import Set, Dict, List, Any
from zeroentropy import AsyncZeroEntropy

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers
from starlette.requests import Request
from starlette.exceptions import HTTPException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

zclient = AsyncZeroEntropy(api_key="")

server_instructions = """
This MCP server provides search and document retrieval capabilities
for deep research. Use the search tool to find relevant documents
based on keywords, then use the fetch tool to retrieve complete
document content with citations.
"""


def create_server():
    """Create and configure the MCP server with search and fetch tools."""

    # Initialize the FastMCP server
    mcp = FastMCP(name="Sample Deep Research MCP Server",
                  instructions=server_instructions) #  stateless_http=True)

    @mcp.tool()
    async def search(query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search for documents using ZeroEntropy

        This tool will search over the ZeroEntropy database for relevant results.

        Args:
            query: Search query string. Natural language queries work best for semantic search.

        Returns:
            Dictionary with 'results' key containing List of matching documents.
            Each result includes id, title, text snippet, and URL.
        """
        headers = get_http_headers()

        auth_token = headers.get("authorization", "")
        collection_name = headers.get("x-collection-name", None)
        if collection_name is None:
            raise HTTPException(status_code=400, detail="The header X-Collection-Name must be provided.")

        response = await zclient.queries.top_snippets(
            collection_name=collection_name,
            k=15,
            query=query,
            extra_headers={
                "Authorization": auth_token,
            },
        )

        path_to_url: Dict[str, str] = {}
        for document_result in response.document_results:
            path_to_url[document_result.path] = document_result.file_url

        ids_shown: Set[str] = set()
        ret_results: List[Dict[str, Any]] = []
        for result in response.results:
            if result.path in ids_shown:
                continue
            ids_shown.add(result.path)
            ret_results.append({
                "id": result.path,
                "title": result.path,
                "text": result.content,
                "url": path_to_url[result.path],
            })

        return {
            "results": ret_results,
        }

    @mcp.tool()
    async def fetch(id: str) -> Dict[str, Any]:
        """
        Retrieve complete document content by ID for detailed
        analysis and citation. This tool fetches the full document
        content from ZeroEntropy. Use this after finding
        relevant documents with the search tool to get complete
        information for analysis and proper citation.

        Args:
            id: File ID from ZeroEntropy

        Returns:
            Complete document with id, title, full text content,
            optional URL, and metadata

        Raises:
            ValueError: If the specified ID is not found
        """
        if not id:
            raise ValueError("Document ID is required")

        headers = get_http_headers()

        auth_token = headers.get("authorization", "")
        collection_name = headers.get("x-collection-name", None)
        if collection_name is None:
            raise HTTPException(status_code=400, detail="The header X-Collection-Name must be provided.")

        response = await zclient.documents.get_info(
            collection_name=collection_name,
            path=id,
            include_content=True,
            extra_headers={
                "Authorization": auth_token,
            },
        )

        return {
            "id": id,
            "title": id,
            "text": response.document.content,
            "url": response.document.file_url,
        }

        # return {
        #     "id": id,
        #     "title": "Apples to Oranges",
        #     "text": "The secret is 29310512",
        #     "url": "https://example.com",
        # }

    return mcp


def main():
    """Main function to start the MCP server."""
    # Create the MCP server
    deepresearch_fastmcp = create_server()
    sse_app = deepresearch_fastmcp.sse_app(path="/sse")

    # Configure and start the server
    logger.info("Starting MCP server on 0.0.0.0:8000")
    logger.info("Server will be accessible via SSE transport")

    try:
        # Use FastMCP's built-in run method with SSE transport
        uvicorn.run(sse_app, host="localhost", port=8000)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    main()
