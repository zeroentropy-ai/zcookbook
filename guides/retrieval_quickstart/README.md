# Retrieval Quickstart

A quick walkthrough of the ZeroEntropy Python SDK: create a collection, load documents into it, and search with natural language queries.

## Overview

1. Load a dataset from HuggingFace (SciFact, a scientific abstracts corpus)
2. Create a collection and add the documents
3. Wait for indexing to finish
4. Search using `top_documents` and `top_snippets` (both coarse and precise)
5. Print ranked results with scores

## Prerequisites

- Python 3.12+
- ZeroEntropy API key (set as `ZEROENTROPY_API_KEY` environment variable)
- HuggingFace CLI installed and logged in ([create a token here](https://huggingface.co/settings/tokens))

## Run the script

```bash
uv sync
uv run python retrieval_search_example.py
```

## What it does

The script loads the `mteb/scifact` corpus, creates a collection called `scifact`, and uploads the abstracts. Once indexing is done it runs a few sample queries and prints results in two modes:

- **Top Documents** ranks entire documents by relevance.
- **Top Snippets (coarse)** returns ~2000-character passages with surrounding context.
- **Top Snippets (precise)** returns ~200-character passages that zero in on the answer.

## Notebook

There's also `retrieval_quickstart.ipynb` if you prefer a step-by-step walkthrough. It uses a handful of local Markdown files instead of a HuggingFace dataset, so it's faster to run and easier to follow.

## Key Functions

- `load_dataset_from_hf()` loads and preprocesses the HuggingFace dataset
- `create_collection()` creates a new collection
- `add_documents()` uploads documents to the collection
- `wait_for_indexing()` polls until all documents are indexed
- `search_top_documents()` retrieves the most relevant documents
- `search_top_snippets()` retrieves snippets (coarse or precise)

## Sample Output

```
Dataset: mteb/scifact

====================================================================================================
TOP DOCUMENTS
Query: "What causes Alzheimer's disease?"
====================================================================================================
Rank   Score        Path
----------------------------------------------------------------------------------------------------
1      0.8734       doc_42.txt
2      0.8521       doc_187.txt
3      0.8103       doc_91.txt
4      0.7856       doc_305.txt
5      0.7641       doc_12.txt

====================================================================================================
TOP SNIPPETS - PRECISE
Query: "What causes Alzheimer's disease?"
====================================================================================================
Rank   Score        Path                 Snippet Preview
----------------------------------------------------------------------------------------------------
1      0.8734       doc_42.txt           Amyloid-beta accumulation in the brain is widely...
2      0.8521       doc_187.txt          Tau protein tangles contribute to neuronal degene...
3      0.8103       doc_91.txt           Genetic factors including APOE4 allele increase t...
```

## Configuration

Edit these values at the top of `retrieval_search_example.py`:

- `collection_name` (default: `"scifact"`)
- `dataset_name` (default: `"mteb/scifact"`)
- `queries` list of search queries
