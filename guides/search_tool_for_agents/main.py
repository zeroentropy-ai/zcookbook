import os
import time
from concurrent.futures import ThreadPoolExecutor

import dotenv
import requests
from zeroentropy import ZeroEntropy
from agents import Agent, Runner, function_tool

# Load environment variables
dotenv.load_dotenv()

# Configuration
ZEROENTROPY_API_KEY = os.getenv("ZEROENTROPY_API_KEY")
COLLECTION_NAME = "yc_voice_agent_support"
YC_API_URL = "https://yc-oss.github.io/api/companies/all.json"

# Prompts
SYSTEM_PROMPT = (
    "You are a helpful search agent that can answer any question about YC companies. "
    "Use the search tool to find relevant information and provide clear, concise answers."
)

# Initialize clients
ze_client = ZeroEntropy(api_key=ZEROENTROPY_API_KEY)

@function_tool
def search(query: str) -> str:
    """
    Search for information in the YC companies collection.
    
    Args:
        query: The search query string
        
    Returns:
        Search results from the collection
    """
    print(f"🔍 Searching for: {query}")
    try:
        response = ze_client.queries.top_documents(
            collection_name=COLLECTION_NAME,
            query=query,
            k=3,
        )
        return response.results
    except Exception as e:
        return f"❌ Error searching: {str(e)}"

def add_single_company(company):
    """Helper function to add a single company to the collection."""
    try:
        slug = str(company.get('slug', ''))
        text = (
            f"{company.get('name', '')} — {company.get('one_liner', '')}\n\n"
            f"{company.get('long_description', '')}\n\n"
            f"{company.get('website', '')}\n\n"
            f"{company.get('subindustry', '')}\n\n"
            f"Stage: {company.get('stage', '')}"
        )
        metadata = {
            "batch": company.get("batch", ""),
            "list:industries": company.get("industries", []),
            "stage": company.get("stage", ""),
        }
        
        ze_client.documents.add(
            collection_name=COLLECTION_NAME,
            path=slug,
            content={"type": "text", "text": text},
            metadata=metadata
        )
        return True
    except Exception as e:
        print(f"Failed to add company {company.get('slug', '')}: {e}")
        return False

def setup_yc_data():
    """Fetch YC companies and add to ZeroEntropy collection."""
    print("Setting up YC company data...")
    
    # Create collection
    try:
        ze_client.collections.add(collection_name=COLLECTION_NAME)
        print(f"Created collection: {COLLECTION_NAME}")
    except Exception:
        print(f"Collection {COLLECTION_NAME} already exists")
        return True
    
    # Fetch companies
    try:
        response = requests.get(YC_API_URL, timeout=30)
        response.raise_for_status()
        companies = response.json()
        print(f"Fetched {len(companies)} companies")
    except Exception as e:
        print(f"Failed to fetch companies: {e}")
        return False
    
    # Add companies to collection concurrently
    print(f"Processing companies with 10 concurrent workers...")
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all tasks and collect results
        results = list(executor.map(add_single_company, companies))
    
    success_count = sum(results)
    elapsed = time.time() - start_time
    print(f"Completed! Added {success_count}/{len(companies)} companies successfully. Total time: {elapsed:.1f}s")
    
    return True

def run_search_agent():
    """Main search agent loop."""
    print("\n🤖 Search Agent")
    print("📝 Instructions:")
    print("   • Type your questions about YC companies")
    print("   • Type 'quit' or 'exit' to end the session")
    print("   • Press Ctrl+C to exit")
    print("-" * 50)
    
    # Create agent
    agent = Agent(
        name="YC Search Agent",
        instructions=SYSTEM_PROMPT,
        model="o3-mini",
        tools=[search],
    )
    
    try:
        while True:
            # Get user input
            user_query = input("\n💬 You: ").strip()
            
            if user_query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not user_query:
                continue
            
            print("🤖 Assistant: ", end="", flush=True)
            
            try:
                # Run the agent
                runner = Runner.run_sync(agent, user_query)
                print(runner.final_output)
            except Exception as e:
                print(f"❌ Error: {str(e)}")
            
            print("-" * 30)
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

def main():
    """Main entry point."""
    if not ZEROENTROPY_API_KEY:
        print("Error: Missing ZEROENTROPY_API_KEY. Please set it in your environment.")
        return
    
    # Setup data
    if not setup_yc_data():
        print("Failed to setup YC data")
        return
    
    # Run agent
    run_search_agent()

if __name__ == "__main__":
    main()