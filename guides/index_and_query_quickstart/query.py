from zeroentropy import AsyncZeroEntropy
import asyncio
from dotenv import load_dotenv

load_dotenv()

zclient = AsyncZeroEntropy()

async def query_collection(collection_name: str, query: str, top_k_csv: int = 5, top_k_txt: int = 10) -> None:
    # get the top 5 rows of the csv
    response_csv = await zclient.queries.top_documents(collection_name=collection_name, 
                                                       k=top_k_csv, 
                                                       query=query, 
                                                       filter={
                                                           "type": 
                                                                {"$eq":"csv"}
                                                            }
                                                       )
    response_txt = await zclient.queries.top_snippets(collection_name=collection_name, 
                                                      k=top_k_txt, 
                                                      query=query, 
                                                      precise_responses = True, # this controls the length of the snippets (around 200 chars or 2000 chars more or less)
                                                      filter={
                                                          "type": 
                                                                {"$ne":"csv"}
                                                          }
                                                      )
    # get the content of the documents csv (not included in the response for top documents)
    final_response = []
    for result in response_csv.results:
        document_content = await zclient.documents.get_info(collection_name=collection_name, path=result.path, include_content=True)
        response = {
            "path": result.path,
            "content": document_content.document.content,
            "score": result.score,
            "metadata": result.metadata
        }
        final_response.append(response)

    # combine the response with the snippets
    return final_response + response_txt.results

async def main():
    COLLECTION_NAME = "default"
    query = "This is a test query"
    response = await query_collection(COLLECTION_NAME, query, top_k_csv=5, top_k_txt=10)
    for i, result in enumerate(response):
        print(f"Result {i+1}:")
        print(result)
        print("\n")

if __name__ == "__main__":
    asyncio.run(main())
