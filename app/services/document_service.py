# Сервис для работы с документами (RAG-пайплайн)
import faiss
import os
import docx
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from typing import List, Dict

# Основной класс для работы с документами (загрузка, индексация, поиск)
class DocumentService:
    def __init__(self, test_mode=False):
        self.model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        self.index = faiss.IndexFlatL2(384)
        self.documents: List[Dict] = []
        if not test_mode:
            self._load_documents()
            self._build_index()

    # Загрузка документов из папок и извлечение текста
    def _load_documents(self):
        docs_dirs = ["documents", "documents/statutes"]
        for docs_dir in docs_dirs:
            for filename in os.listdir(docs_dir):
                path = os.path.join(docs_dir, filename)
                if filename.endswith(".pdf"):
                    text = self._extract_text_from_pdf(path)
                elif filename.endswith(".docx"):
                    text = self._extract_text_from_docx(path)
                else:
                    continue
                
                self.documents.append({
                    "name": filename,
                    "path": path,
                    "text": text,
                    "embedding": self.model.encode(text)
                })

    # Построение FAISS индекса для векторного поиска
    def _build_index(self):
        embeddings = [doc["embedding"] for doc in self.documents]
        if embeddings:
            import numpy as np
            self.index.add(np.array(embeddings).astype('float32'))

    def _extract_text_from_pdf(self, path: str) -> str:
        try:
            with open(path, "rb") as f:
                reader = PdfReader(f)
                return "\n".join(
                    page.extract_text() or "" 
                    for page in reader.pages
                )
        except Exception as e:
            print(f"Error reading PDF {path}: {str(e)}")
            return ""

    def _extract_text_from_docx(self, path: str) -> str:
        try:
            doc = docx.Document(path)
            return "\n".join(para.text for para in doc.paragraphs)
        except Exception as e:
            print(f"Error reading DOCX {path}: {str(e)}")
            return ""

    # Поиск документов по запросу с использованием векторного поиска
async def search(self, query: str, top_k: int = 5) -> List[Dict]:
        query_emb = self.model.encode([query])
        distances, idx = self.index.search(query_emb, top_k)
        return [
            {
                **self.documents[i],
                "score": float(1 - distances[0][j])
            }
            for j, i in enumerate(idx[0]) if i >= 0
        ]

doc_service = DocumentService(test_mode=os.getenv("ENVIRONMENT") == "test")
