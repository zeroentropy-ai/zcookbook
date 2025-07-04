# Index and Query with ZeroEntropy

This folder contains a simple setup to **index** and **query** documents using [ZeroEntropy](https://zeroentropy.dev). It's designed to be a minimal, self-contained example for quickly testing search over your own files.

## 🔧 Setup Instructions

1. **Install dependencies**:

   ```bash
   pip install zeroentropy python-dotenv tqdm
   ```

2. **Create your API Key on the dashboard:**:

Visit the [ZeroEntropy Dashboard](https://dashboard.zeroentropy.dev) and create your API Key.

3. **Create a .env file in this folder:**:

   ```bash
   touch .env
   ```
Then add your ZeroEntropy API key: 

```bash
   ZEROENTROPY_API_KEY=your_api_key_here
   ```
4. **Add your documents to the `data/` folder:** 
   Supported formats:  
   - `.csv` — indexed line by line  
   - `.pdf` — indexed with OCR  
   - `.txt` — indexed as a single document

5. **Index your data:**:

```bash
   python index.py
   ```
This will create a collection named default and upload all files under data/.

6. **Run a query:**:

```bash
   python query.py
   ```
You can modify the default query string in query.py.

## File Structure

```bash
   index_and_query/
* data/           place your .csv .txt or .pdf files here
* index.py        indexes all documents in the data folder
* query.py        queries the indexed documents
* .env            your API key goes here
* README.md       this file
   ```

## Notes

- All documents are added to a collection named default. You can change this in index.py and query.py
- If you re-run index.py, it will skip documents that already exist using the document path as the ID