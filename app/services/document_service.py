import faiss
from sentence_transformers import SentenceTransformer

class DocumentService:
    def __init__(self):
        self.model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        self.index = faiss.IndexFlatL2(384)

    async def search(self, query: str, top_k: int = 3) -> list[str]:
        emb = self.model.encode([query])
        _, idx = self.index.search(emb, top_k)
        return [f"chunk_{i}" for i in idx[0]]  # stub

doc_service = DocumentService()
