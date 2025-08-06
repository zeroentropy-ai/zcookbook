# French Gossip Semantic Search with ZeroEntropy

This is a guide of production-ready semantic search for French gossip articles from **vsd.fr** and **public.fr** using ZeroEntropy.

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![ZeroEntropy](https://img.shields.io/badge/zeroentropy-latest-purple.svg)](https://zeroentropy.dev/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.30+-green.svg)](https://streamlit.io/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://docker.com/)

## Features

- **Advanced AI Retrieval**: Powered by ZeroEntropy's state-of-the-art search & reranking
- **Multiple Search Types**: Documents, snippets, pages, and advanced reranked results  
- **Real-time RSS Scraping**: Automatically indexes articles from gossip websites
- **Interactive Web UI**: Beautiful Streamlit interface with advanced filtering
- **Smart Reranking**: Uses `zerank-1-small` model for improved relevance

## Quick Start

### 1. Setup Environment
```bash
# Clone repository
git clone <https://github.com/zeroentropy-ai/zcookbook>
cd .\guides\semantic_search_over_articles

# Install dependencies  
pip install -r requirements.txt

# Configure API key then add your ZEROENTROPY Credentials
cp .env.example .env

```

### 2. Index Articles
```bash
# Scrape RSS feeds and index articles
python backend scrape --collection my_articles
```

### 3. Search Articles
```bash
# Search for articles (CLI)
python backend search "TPMP" --k 5 --collection my_articles
python backend search "famille royale" --search-type snippets
python backend search "célébrités" --search-type advanced --k 10
```

### 4. Web Interface
```bash
# Launch Streamlit app
streamlit run frontend/streamlit_app.py
```
Access at: `http://localhost:8501`

## Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build docker image and run the command within the container
docker build -t gossip-search .
docker exec -it gossip-search-container python backend scrape --collection my_articles
docker exec -it gossip-search-container python backend search "TPMP" --k 5
```

## Project Structure

```
├── backend/
│   ├── main.py              # Main CLI interface
│   ├── indexer_ze.py        # RSS scraping & indexing
│   ├── search_ze.py         # Search functionality  
│   ├── utils_ze.py          # Advanced utilities & reranking
│   └── logger.py            # Logging configuration
├── frontend/
│   └── streamlit_app.py     # Web interface
├── demo_notebook.ipynb      # Interactive demo
├── docker-compose.yml       # Container orchestration
├── requirements.txt         # Dependencies
└── README.md               # This file
```

## Usage Examples

### CLI Commands
```bash
# Collection management
python backend manage list
python backend manage status --collection my_articles

# Advanced search with filters
python backend search "mode" --filter-creator "Public" --reranker zerank-1-small

# Different search types
python backend search "actualité" --search-type documents --k 10
python backend search "télé" --search-type snippets --k 5  
python backend search "people" --search-type advanced --k 8
```


## Demo Notebook

An Jupyter notebook is also available to explore the code and run it step by step;
```bash
jupyter notebook demo_notebook.ipynb
```

---
## Author & Contribution

**Created by [Naoufal Acharki](https://github.com/nacharki)**: This project is a demo of ZeroEntropy on a RAG for French gossip content. 
