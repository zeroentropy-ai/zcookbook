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
def top_documents(query: str, k: int = 3) -> str:
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
    Retrieve top documents from the ZeroEntropy collection using a query.

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




if __name__ == "__main__":
    agent = Agent(
        name="ZeroEntropyVoiceAgent",
        instructions=SYSTEM_PROMPT,
        model="gpt-4.1-mini",
        tools=[top_documents, rerank_documents],
    )
    # for tool in agent.tools:
    #     if isinstance(tool, FunctionTool):
    #         print(tool.name)
    #         print(tool.description)
    #         print(json.dumps(tool.params_json_schema, indent=2))
    #         print()

    runner = Runner.run_sync(agent, "What are best AI voice companies in YC?")
    print(runner.final_output)
