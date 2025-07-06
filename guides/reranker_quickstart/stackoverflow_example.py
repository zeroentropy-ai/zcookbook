import asyncio
import json
import os

import aiohttp


async def main() -> None:
    headers = {
        "Authorization": f"Bearer {os.environ["ZEROENTROPY_API_KEY"]}",
    }
    payload = {
        "query": "What is 2+2?",
        "documents": [
            "4",
            "The answer is definitely 1 million.",
        ],
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
