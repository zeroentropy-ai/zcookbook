# Reranker Quickstart

This example demonstrates how to use ZeroEntropy's reranking API to improve search results by reordering documents based on relevance to a query.

## Overview

The example shows a complete workflow:
1. **Load dataset** - Uses the StackOverflow duplicate questions dataset from HuggingFace
2. **Create collection** - Sets up a document collection in ZeroEntropy
3. **Add documents** - Indexes documents for search
4. **Search** - Retrieves top documents matching a query
5. **Rerank** - Uses ZeroEntropy's reranking model to improve result ordering
6. **Display results** - Shows reranked documents with relevance scores and content snippets

## Prerequisites

- Python 3.8+
- ZeroEntropy API key (set as `ZEROENTROPY_API_KEY` environment variable)
- HuggingFace CLI installed and logged in. Check [here](https://huggingface.co/settings/tokens) for token creation.

## Run the script

```bash
uv sync
uv run python stackoverflow_example.py
```

## What it does

The script will:
1. Load the StackOverflow duplicate questions dataset from HuggingFace
2. Create a collection called "stackoverflow" in ZeroEntropy
3. Add documents from the dataset to the collection
4. Search for documents related to "environment variable"
5. Fetch the full content of the top search results
6. Rerank the documents using ZeroEntropy's reranking API
7. Display the top 10 reranked results with:
   - Reranking score
   - Original search score  
   - Content snippet (first 200 characters)

## Key Functions

- `load_dataset_from_hf()` - Loads and preprocesses the HuggingFace dataset
- `create_collection()` - Creates a new document collection
- `add_documents()` - Indexes documents for search
- `top_documents()` - Retrieves top search results
- `rerank_documents()` - Reranks documents using ZeroEntropy API

## Output

The script outputs reranked search results showing how the reranking model improves the relevance ordering compared to the original search scores.

## Configuration

You can modify the search query and collection name in the `main()` function to experiment with different searches and datasets.
