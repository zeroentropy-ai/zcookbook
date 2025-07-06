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
    
    # Convert all entries to list of strings
    text_entries = [str(row) for row in df.to_dict('records')]
    
    print(f"\nReturning {len(text_entries)} text entries")
    return text_entries[:500]


async def main() -> None:
    headers = {
        "Authorization": f"Bearer {os.environ["ZEROENTROPY_API_KEY"]}",
    }
    documents_list = documents("mteb/stackoverflowdupquestions-reranking")
    payload = {
        "query": "How to fix 'AttributeError: 'NoneType' object has no attribute 'lower''?",
        "documents": documents_list,
    }

    async with aiohttp.ClientSession() as client, client.post(
        "https://api.zeroentropy.dev/v1/models/rerank",
        headers=headers,
        json=payload,
    ) as raw_response:
        response = await raw_response.json()
        print(json.dumps(response, indent=4))


if __name__ == "__main__":
    asyncio.run(main())
