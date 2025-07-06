import asyncio
import json
import os
import pandas as pd
import aiohttp
import requests
from datasets import load_dataset

from zeroentropy import ZeroEntropy

zclient = ZeroEntropy(api_key=os.environ["ZEROENTROPY_API_KEY"])

def documents(dataset_name: str):
    ds = load_dataset(dataset_name, split="test")
    df = ds.to_pandas()
    
    print(f"Dataset has {len(df)} rows")
    print(f"Columns: {list(df.columns)}")
    
    # Convert all entries to list of dictionaries
    text_entries = df.to_dict('records')
    
    print(f"\nReturning {len(text_entries)} text entries")
    print(text_entries[0])
    return text_entries

async def fetch_document_content(file_url: str) -> str:
    """
    Fetch document content from the file_url
    """
    try:
        async with aiohttp.ClientSession() as client, client.get(file_url) as response:
            if response.status == 200:
                content = await response.text()
                return content
            else:
                print(f"Failed to fetch content from {file_url}: {response.status}")
                return ""
    except Exception as e:
        print(f"Error fetching content from {file_url}: {e}")
        return ""

async def create_collection(collection_name: str):
    """
    Create a collection in ZeroEntropy API
    """
    try:
        collection = zclient.collections.add(collection_name=collection_name)
        print(collection.message)
    except Exception as e:
        print(f"Error creating collection: {e}")

async def add_documents(collection_name: str, documents: list):
    """
    Add documents to a collection in ZeroEntropy API
    """
    for i, doc in enumerate(documents, start=1050):
        try:
            print(f"Adding document {i}")
            zclient.documents.add(
                collection_name=collection_name, 
                path=f"v0/doc_{i}.json", 
                content= {
                    "type": "text",
                    "text": str(doc)
                }
            )
        except Exception as error:
            print(f"Error adding document {i}: {error}")

async def top_documents(query: str, collection_name: str = "default", k: int = 50):
    """
    Retrieve top documents from ZeroEntropy API
    """
    response = zclient.queries.top_documents(
        collection_name=collection_name,
        query=query,
        k=k
    )
    return response.results

async def reranking(query: str, documents: list) -> dict:
    """
    Rerank documents using top documents from the API
    """
    headers = {
        "Authorization": f"Bearer {os.environ['ZEROENTROPY_API_KEY']}",
    }
    
    # Extract just the content strings for the API call
    documents_as_strings = [doc["content"] for doc in documents]
    
    payload = {
        "query": query,
        "documents": documents_as_strings,
    }

    async with aiohttp.ClientSession() as client, client.post(
        "https://api.zeroentropy.dev/v1/models/rerank",
        headers=headers,
        json=payload,
    ) as raw_response:
        response = await raw_response.json()
        return response

async def main():
    """
    Main function to run the top documents and reranking example
    """
    # await create_collection("stackoverflow")
    # doc_list = documents("mteb/stackoverflowdupquestions-reranking")
    # await add_documents("stackoverflow", doc_list[49:])

    top_docs = await top_documents("environment variable", "stackoverflow")
    
    # Create document objects with both content and metadata
    documents = []
    for doc in top_docs:
        content = await fetch_document_content(doc.file_url)
        documents.append({
            "content": content,
            "path": doc.file_url,
            "score": getattr(doc, 'score', 'N/A')  # Use getattr in case score doesn't exist
        })

    response = await reranking("environment variable", documents)
    
    # Print the reranked results
    if "results" in response:
        print("\n=== Top reranked documents ===")
        for i, result in enumerate(response["results"][:10]):  # Show top 10
            index = result["index"]
            score = result["relevance_score"]
            original_doc = documents[index] if index < len(documents) else {}
            original_score = original_doc.get("score", "N/A")
            
            # Print a snippet of the document content
            content_snippet = original_doc.get("content", "")[:200] + "..." if len(original_doc.get("content", "")) > 200 else original_doc.get("content", "")
            
            print(f"{i+1}. (Rerank Score: {score:.4f}, Original Score: {original_score})")
            print(f"   Content: {content_snippet}")
            print()
    else:
        print("\nNo results found in reranking response")


if __name__ == "__main__":
    asyncio.run(main())
