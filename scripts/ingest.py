from app.config import settings
from app.rag import Indexer
import os

def main():
    input_dir = os.path.join("data", "products")
    storage_dir = "storage"
    os.makedirs(storage_dir, exist_ok=True)
    idx = Indexer(settings.EMBEDDING_MODEL)
    idx.build(input_dir=input_dir, storage_dir=storage_dir)

if __name__ == "__main__":
    main()
