from zeroentropy import AsyncZeroEntropy, ConflictError
import asyncio
from dotenv import load_dotenv
from tqdm.asyncio import tqdm
import os
import base64

load_dotenv()

zclient = AsyncZeroEntropy()
sem = asyncio.Semaphore(16)

async def index_document(document_path: str, collection_name: str) -> None:
    response = None
    if not os.path.exists(document_path):
        raise FileNotFoundError(f"File {document_path} not found")
    
    # for csv we will index each row as a separate document
    if os.path.splitext(document_path)[1] == ".csv":
        with open(document_path) as f:
            documents = f.readlines()
        for i, document in enumerate(documents):
            async with sem:
                for _retry in range(3):
                        try:
                            content = { "type": "text", "text": document }
                            response = await zclient.documents.add(
                                collection_name=collection_name,
                                path=f"{document_path}_{i}",
                                content=content,
                                metadata={"type": "csv"},
                            )
                            break
                        except ConflictError as e:
                            print(f"Document '{document_path}' already exists in collection '{collection_name}'")
    # for pdf we need to specifify the type so we can use OCR
    elif os.path.splitext(document_path)[1] == ".pdf":
        with open(document_path, "rb") as f:
            pdf_bytes = f.read()
            pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
            async with sem:
                for _retry in range(3):
                    try:
                        content = { "type": "auto", "base64_data": pdf_base64 } #this will automatically OCR the PDF
                        response = await zclient.documents.add(
                        collection_name=collection_name,
                        path=document_path,
                        content=content,
                        metadata={"type": "pdf"},
                            )
                        break
                    except ConflictError as e:
                        print(f"Document '{document_path}' already exists in collection '{collection_name}'")
    #for txt no need to use OCR
    elif os.path.splitext(document_path)[1] == ".txt":   
        with open(document_path, "r", encoding="utf-8") as f:
            text = f.read()
            async with sem:
                for _retry in range(3):
                    try:
                        content = { "type": "text", "text": text }
                        response = await zclient.documents.add(
                                    collection_name=collection_name,
                                    path=document_path,
                                    content=content,
                                    metadata={"type": "text"},
                                )
                        break
                    except ConflictError as e:
                        print(f"Document '{document_path}' already exists in collection '{collection_name}'")
    else:
        print(f"Unsupported file type: {os.path.splitext(document_path)[1]}")
        return None
    return response

async def main():
    #list all files in the data folder
    
    DATA_DIR = "./data"
    COLLECTION_NAME = "default"

    documents_path = [os.path.join(DATA_DIR, file) for file in os.listdir(DATA_DIR)]
    try:
        await zclient.collections.add(collection_name=COLLECTION_NAME)
    except ConflictError:
        print(f"Collection '{COLLECTION_NAME}' already exists")
    print(f"Indexing {len(documents_path)} documents in collection '{COLLECTION_NAME}'")
    await tqdm.gather(*[index_document(document_path, COLLECTION_NAME) for document_path in documents_path], desc="Indexing Documents")
    print(f"Indexing completed for collection '{COLLECTION_NAME}'")

if __name__ == "__main__":
    asyncio.run(main())