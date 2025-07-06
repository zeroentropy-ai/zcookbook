import asyncio
import json
import os
import pandas as pd
import aiohttp


from datasets import load_dataset

def documents(dataset_name: str):
    ds = load_dataset(dataset_name, split="test")
    df = ds.to_pandas()
    
    print(f"Dataset has {len(df)} rows")
    print(f"Columns: {list(df.columns)}")
    
    # Convert all entries to list of dictionaries
    text_entries = df.to_dict('records')
    
    print(f"\nReturning {len(text_entries)} text entries")
    return text_entries[:50]


async def main() -> None:
    headers = {
        "Authorization": f"Bearer {os.environ["ZEROENTROPY_API_KEY"]}",
    }
    documents_list = documents("mteb/stackoverflowdupquestions-reranking")
    
    # Convert to strings for API call
    documents_as_strings = [str(doc) for doc in documents_list]
    
    payload = {
        "query": "environment variable",
        "documents": documents_as_strings,
    }

    async with aiohttp.ClientSession() as client, client.post(
        "https://api.zeroentropy.dev/v1/models/rerank",
        headers=headers,
        json=payload,
    ) as raw_response:
        response = await raw_response.json()
        print(json.dumps(response, indent=4))
        
        # Print the queries based on returned indices
        if "results" in response:
            print("\n=== Top ranked queries ===")
            for i, result in enumerate(response["results"][:10]):  # Show top 10
                index = result["index"]
                score = result["relevance_score"]
                query = documents_list[index]["query"]
                print(f"{i+1}. (Score: {score:.4f}) {query}")
        else:
            print("\nNo results found in response")

if __name__ == "__main__":
    asyncio.run(main())
