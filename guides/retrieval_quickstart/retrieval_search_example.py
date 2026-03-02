import os
import time
from datasets import load_dataset
from dotenv import load_dotenv
from zeroentropy import ZeroEntropy

load_dotenv()

zclient = ZeroEntropy(api_key=os.environ["ZEROENTROPY_API_KEY"])


def load_dataset_from_hf(dataset_name: str, subset: str = "corpus", split: str = "train"):
    ds = load_dataset(dataset_name, subset, split=split)
    df = ds.to_pandas()
    text_entries = df.to_dict("records")
    return text_entries


def create_collection(collection_name: str):
    try:
        collection = zclient.collections.add(collection_name=collection_name)
        print(collection.message)
    except Exception as e:
        print(f"Collection already exists or error: {e}")


def add_documents(collection_name: str, documents: list):
    for i, doc in enumerate(documents):
        try:
            title = doc.get("title", "")
            text = doc.get("text", str(doc))
            content_str = f"{title}\n\n{text}" if title else text

            print(f"Adding document {i + 1}/{len(documents)}", end="\r")
            zclient.documents.add(
                collection_name=collection_name,
                path=f"doc_{i}.txt",
                content={"type": "text", "text": content_str},
            )
        except Exception as error:
            print(f"Error adding document {i}: {error}")

    print(f"\nAdded {len(documents)} documents to '{collection_name}'")


def wait_for_indexing(collection_name: str):
    print("Waiting for documents to be indexed", end="")
    while True:
        status = zclient.status.get_status(collection_name=collection_name)
        indexed = status.num_indexed_documents
        total = status.num_documents
        if indexed == total and total > 0:
            print(f"\nAll {total} documents indexed.")
            break
        print(".", end="", flush=True)
        time.sleep(2)


def search_top_documents(query: str, collection_name: str, k: int = 10):
    response = zclient.queries.top_documents(
        collection_name=collection_name,
        query=query,
        k=k,
    )
    return response.results


def search_top_snippets(query: str, collection_name: str, k: int = 10, precise: bool = False):
    response = zclient.queries.top_snippets(
        collection_name=collection_name,
        query=query,
        k=k,
        precise_responses=precise,
    )
    return response.results


def display_document_results(results, query: str):
    print(f"\n{'=' * 100}")
    print("TOP DOCUMENTS")
    print(f"Query: \"{query}\"")
    print(f"{'=' * 100}")
    print(f"{'Rank':<6} {'Score':<12} {'Path':<20} ")
    print(f"{'-' * 100}")

    for i, result in enumerate(results[:10]):
        score = f"{result.score:.4f}" if hasattr(result, "score") else "N/A"
        path = getattr(result, "path", "N/A")
        print(f"{i + 1:<6} {score:<12} {path:<20}")


def display_snippet_results(results, query: str, precise: bool):
    mode = "PRECISE" if precise else "COARSE"
    print(f"\n{'=' * 100}")
    print(f"TOP SNIPPETS - {mode}")
    print(f"Query: \"{query}\"")
    print(f"{'=' * 100}")
    print(f"{'Rank':<6} {'Score':<12} {'Path':<20} {'Snippet Preview':<60}")
    print(f"{'-' * 100}")

    for i, result in enumerate(results[:10]):
        score = f"{result.score:.4f}" if hasattr(result, "score") else "N/A"
        path = getattr(result, "path", "N/A")
        content = getattr(result, "content", "") or ""
        snippet = content[:57] + "..." if len(content) > 57 else content
        snippet = snippet.replace("\n", " ")
        print(f"{i + 1:<6} {score:<12} {path:<20} {snippet:<60}")


def main():
    collection_name = "scifact"
    dataset_name = "mteb/scifact"
    queries = [
        "What causes Alzheimer's disease?",
        "How does vaccination affect immune response?",
        "What is the role of p53 in cancer?",
    ]

    print(f"Dataset: {dataset_name}\n")

    # Step 1: Create collection
    create_collection(collection_name)

    # Step 2: Load and add documents
    corpus = load_dataset_from_hf(dataset_name, subset="corpus", split="corpus")
    add_documents(collection_name, corpus)

    # Step 3: Wait for indexing
    wait_for_indexing(collection_name)

    # Step 4: Run searches for each query
    for query in queries:
        doc_results = search_top_documents(query, collection_name, k=5)
        display_document_results(doc_results, query)

        coarse_results = search_top_snippets(query, collection_name, k=5, precise=False)
        display_snippet_results(coarse_results, query, precise=False)

        precise_results = search_top_snippets(query, collection_name, k=5, precise=True)
        display_snippet_results(precise_results, query, precise=True)

    # Step 5: Cleanup
    zclient.collections.delete(collection_name=collection_name)
    print(f"\nCollection '{collection_name}' deleted.")


if __name__ == "__main__":
    main()
