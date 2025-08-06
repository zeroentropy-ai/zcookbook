# streamlit_app.py
import os
import sys
import asyncio
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set the working directory to the backend
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.abspath(os.path.join(current_dir, "../..", "backend"))
sys.path.append(backend_path)

# Internal imports
from backend.search_ze import ZeroEntropyArticleSearcher  # noqa: E402
from backend.utils_ze import ZeroEntropyUtils  # noqa: E402


# Cache the searcher and utils to avoid reinitializing
@st.cache_resource
def get_searcher_and_utils(collection_name="articles"):
    """Initialize and cache ZeroEntropy searcher and utils"""
    searcher = ZeroEntropyArticleSearcher(collection_name)
    utils = ZeroEntropyUtils(collection_name)
    return searcher, utils


async def get_search_results(
    query: str,
    search_type: str,
    k: int,
    collection_name: str,
    filter_creator: str = None,
    filter_category: str = None,
    reranker: str = "zerank-1-small",
):
    """Async search function that uses ZeroEntropy backend functionality"""
    searcher, utils = get_searcher_and_utils(collection_name)

    # Prepare filter if specified
    filter_dict = {}
    if filter_creator:
        filter_dict["creator"] = {"$eq": filter_creator}
    if filter_category:
        filter_dict["categories"] = {"$eq": filter_category}
    filter_dict = filter_dict if filter_dict else None

    # Perform search based on type
    if search_type == "documents":
        results = await searcher.search_documents(
            query=query,
            k=k,
            filter_dict=filter_dict,
            reranker=reranker,
        )
    elif search_type == "snippets":
        results = await searcher.search_snippets(
            query=query,
            k=k,
            filter_dict=filter_dict,
            reranker=reranker,
        )
    elif search_type == "pages":
        results = await searcher.search_pages(
            query=query, k=k, filter_dict=filter_dict
        )
    elif search_type == "advanced":
        results = await utils.search_and_rerank(
            query=query, k=k * 2, rerank_top_n=k  # Get more documents initially
        )
    else:
        results = []

    return results, search_type


def run_async_search(
    query: str,
    search_type: str,
    k: int,
    collection_name: str,
    filter_creator: str = None,
    filter_category: str = None,
    reranker: str = "zerank-1-small",
):
    """Wrapper to run async search in Streamlit"""
    # Create new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Run the async function
    results, search_type = loop.run_until_complete(
        get_search_results(
            query,
            search_type,
            k,
            collection_name,
            filter_creator,
            filter_category,
            reranker,
        )
    )

    loop.close()
    return results, search_type


def display_document_results(results):
    """Display document search results"""
    for i, result in enumerate(results, 1):
        with st.container():
            col1, col2 = st.columns([3, 1])

            with col1:
                metadata = result.get("metadata", {})
                title = metadata.get("title", "N/A")

                # Make title clickable if file_url exists
                if result.get("file_url"):
                    st.markdown(f"### [{title}]({result['file_url']})")
                else:
                    st.markdown(f"### {title}")

                st.markdown(f"**Author:** {metadata.get('creator', 'N/A')}")
                st.markdown(f"**Publication Date:** {metadata.get('pub_date', 'N/A')}")
                st.markdown(f"**Categories:** {metadata.get('categories', 'N/A')}")

                if metadata.get("source_url"):
                    st.markdown(f"**Source:** {metadata.get('source_url', 'N/A')}")

            with col2:
                st.metric("Relevance Score", f"{result['score']:.3f}")
                if result.get("rerank_score"):
                    st.metric("Rerank Score", f"{result['rerank_score']:.3f}")

            st.markdown("---")


def display_snippet_results(results):
    """Display snippet search results"""
    for i, result in enumerate(results, 1):
        with st.container():
            col1, col2 = st.columns([3, 1])

            with col1:
                metadata = result.get("metadata", {})
                st.markdown(f"### Snippet {i}")
                st.markdown(f"**From:** {metadata.get('title', 'N/A')}")
                st.markdown(f"**Author:** {metadata.get('creator', 'N/A')}")

                # Show snippet content
                if result.get("content"):
                    with st.expander("Show Content", expanded=True):
                        st.write(result["content"])

            with col2:
                st.metric("Relevance Score", f"{result['score']:.3f}")
                st.write(
                    f"**Char Range:** {result.get('start_index', 0)}-{result.get('end_index', 0)}"
                )
                st.write(f"**Page Span:** {result.get('page_span', [])}")

            st.markdown("---")


def display_page_results(results):
    """Display page search results"""
    for i, result in enumerate(results, 1):
        with st.container():
            col1, col2 = st.columns([3, 1])

            with col1:
                metadata = result.get("metadata", {})
                st.markdown(f"### Page {i}")
                st.markdown(f"**From:** {metadata.get('title', 'N/A')}")
                st.markdown(f"**Page Index:** {result.get('page_index', 0)}")

                # Show page content
                if result.get("content"):
                    with st.expander("Show Content", expanded=False):
                        st.write(
                            result["content"][:500] + "..."
                            if len(result["content"]) > 500
                            else result["content"]
                        )

            with col2:
                st.metric("Relevance Score", f"{result['score']:.3f}")

            st.markdown("---")


def display_advanced_results(results):
    """Display advanced search results with reranking"""
    for i, result in enumerate(results, 1):
        with st.container():
            col1, col2 = st.columns([3, 1])

            with col1:
                metadata = result.get("metadata", {})
                title = metadata.get("title", "N/A")

                st.markdown(f"### {title}")
                st.markdown(f"**Author:** {metadata.get('creator', 'N/A')}")
                st.markdown(f"**Publication Date:** {metadata.get('pub_date', 'N/A')}")
                st.markdown(f"**Categories:** {metadata.get('categories', 'N/A')}")

            with col2:
                st.metric("Original Score", f"{result.get('original_score', 0):.3f}")
                st.metric("Rerank Score", f"{result.get('rerank_score', 0):.3f}")

            st.markdown("---")


async def get_collection_status(collection_name):
    """Get collection status"""
    try:
        searcher, _ = get_searcher_and_utils(collection_name)
        status = await searcher.get_collection_status()
        return status
    except Exception as e:
        st.error(f"Error getting status: {str(e)}")
        return None


def run_async_status(collection_name):
    """Wrapper to run async status check in Streamlit"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        status = loop.run_until_complete(get_collection_status(collection_name))
        loop.close()
        return status
    except Exception as e:
        st.error(f"Error getting status: {str(e)}")
        return None


def main():
    st.set_page_config(
        page_title="ZeroEntropy Gossip Search", layout="wide", page_icon="📰"
    )

    st.title("📰 RAG Gossip Semantic Search with ZeroEntropy")
    st.write(
        "Search for the latest articles from VSD and Public using advanced AI-powered retrieval."
    )

    # Sidebar for configuration
    with st.sidebar:
        st.header("🔧 Search Configuration")

        collection_name = st.text_input("Collection Name", value="my_articles")

        search_type = st.selectbox(
            "Search Type",
            options=["documents", "snippets", "pages", "advanced"],
            index=0,
            help="Choose the type of search to perform",
        )

        k = st.slider("Number of results", min_value=1, max_value=20, value=5)

        # Advanced options
        with st.expander("🔍 Advanced Options"):
            reranker = st.selectbox(
                "Reranker Model", options=["zerank-1-small"], index=0
            )

            filter_creator = st.text_input(
                "Filter by Creator", placeholder="e.g., Arno Crampont"
            )
            filter_category = st.text_input(
                "Filter by Category", placeholder="e.g., TPMP"
            )

        # Collection status
        if st.button("📊 Check Collection Status"):
            with st.spinner("Getting status..."):
                status = run_async_status(collection_name)
                if status:
                    st.success("✅ Collection Status")
                    st.write(f"**Total Documents:** {status.num_documents}")
                    st.write(f"**Indexed:** {status.num_indexed_documents}")
                    st.write(f"**Parsing:** {status.num_parsing_documents}")
                    st.write(f"**Indexing:** {status.num_indexing_documents}")
                    st.write(f"**Failed:** {status.num_failed_documents}")

    # Main search interface
    query = st.text_input(
        "🔍 Enter your search query:",
        value="",
        placeholder="e.g., TPMP, famille royale, célébrités...",
    )

    if st.button("Search for a keyword", type="primary"):
        if query.strip():
            with st.spinner(f"Searching with {search_type} mode..."):
                results, result_type = run_async_search(
                    query=query,
                    search_type=search_type,
                    k=k,
                    collection_name=collection_name,
                    filter_creator=filter_creator if filter_creator else None,
                    filter_category=filter_category if filter_category else None,
                    reranker=reranker,
                )

                if results:
                    st.success(f"✅ Found {len(results)} results for '{query}'")

                    # Display results based on search type
                    if result_type == "documents":
                        display_document_results(results)
                    elif result_type == "snippets":
                        display_snippet_results(results)
                    elif result_type == "pages":
                        display_page_results(results)
                    elif result_type == "advanced":
                        display_advanced_results(results)

                else:
                    st.warning("❌ No results found for your query.")
        else:
            st.error("⚠️ Please enter a valid query.")

    # Help section
    with st.expander("ℹ️ How to use this app"):
        st.markdown(
            """
        ### Search Types:
        - **Documents**: Search entire articles for the most relevant matches
        - **Snippets**: Find specific text snippets within articles
        - **Pages**: Search individual pages of documents
        - **Advanced**: Uses reranking for improved relevance

        ### Filters:
        - **Creator**: Filter by article author
        - **Category**: Filter by article category

        ### Tips:
        - Use specific keywords for better results
        - Try different search types for different use cases
        - Use filters to narrow down results
        """
        )


if __name__ == "__main__":
    main()
