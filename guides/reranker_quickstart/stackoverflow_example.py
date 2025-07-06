import asyncio
import os
import pandas as pd
import aiohttp
from datasets import load_dataset
from dotenv import load_dotenv

from zeroentropy import ZeroEntropy

load_dotenv()

zclient = ZeroEntropy(api_key=os.environ["ZEROENTROPY_API_KEY"])

def load_dataset_from_hf(dataset_name: str):
    ds = load_dataset(dataset_name, split="test")
    df = ds.to_pandas()
    
    # Convert all entries to list of dictionaries
    text_entries = df.to_dict('records')
    
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
    for i, doc in enumerate(documents, start=1000):
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

async def rerank_documents(query: str, documents: list) -> dict:
    """
    Rerank documents using top documents from the API
    """
    documents_as_strings = [doc["content"] for doc in documents]
    
    headers = {
        "Authorization": f"Bearer {os.environ['ZEROENTROPY_API_KEY']}",
    }
    
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
    Main function to search for top documents and rerank them
    """
    query = "Find absolute path in the file system"
    collection_name = "stackoverflow"
    
    # Create collection and add documents or you can use existing collection
    await create_collection(collection_name)
    doc_list = load_dataset_from_hf("mteb/stackoverflowdupquestions-reranking")
    await add_documents(collection_name, doc_list)

    top_docs = await top_documents(query, "cosqa")
    
    # Create document objects with both content and metadata
    documents = []
    for i, doc in enumerate(top_docs):
        content = await fetch_document_content(doc.file_url)
        documents.append({
            "content": content,
            "path": doc.file_url,
            "score": getattr(doc, 'score', 'N/A'),
            "original_rank": i + 1  # Track original ranking (1-indexed)
        })

    response = await rerank_documents(query, documents)
    
    # Print the reranked results in table format
    if "results" in response:
        print("\n" + "="*120)
        print("RERANKING RESULTS COMPARISON")
        print("="*120)
        print(f"{'Rerank':<8} {'Original':<10} {'Content Preview':<70}")
        print("-"*120)
        
        for i, result in enumerate(response["results"][:10]):  # Show top 10
            index = result["index"]
            original_doc = documents[index] if index < len(documents) else {}
            original_rank = original_doc.get("original_rank", "N/A")
            
            # Get content snippet (first 70 characters)
            content_snippet = original_doc.get("content", "")[:67] + "..." if len(original_doc.get("content", "")) > 67 else original_doc.get("content", "")

            print(f"{i+1:<8} {original_rank:<10} {content_snippet:<70}")
        
    else:
        print("\nNo results found in reranking response")


if __name__ == "__main__":
    asyncio.run(main())
