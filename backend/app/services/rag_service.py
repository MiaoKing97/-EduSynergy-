# backend/app/services/rag_service.py
import asyncio
import io
import os
import chromadb
import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter


class RAGService:
    def __init__(self):
        persist_directory = os.path.join(os.getcwd(), "chroma_data")
        self.chroma_client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.chroma_client.get_or_create_collection(name="school_knowledge_base")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
        )

    async def ingest_pdf(self, file_bytes: bytes, filename: str) -> str:
        """Parse PDF and ingest into ChromaDB (runs CPU-bound work in thread)."""
        return await asyncio.to_thread(self._ingest_pdf_sync, file_bytes, filename)

    def _ingest_pdf_sync(self, file_bytes: bytes, filename: str) -> str:
        try:
            text = ""
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

            if not text.strip():
                return f"[警告：未能从 {filename} 中提取到有效文本，可能为纯扫描版图片PDF]"

            chunks = self.text_splitter.split_text(text)
            if not chunks:
                return f"[警告：{filename} 文本切块失败]"

            ids = [f"{filename}_{i}" for i in range(len(chunks))]
            metadatas = [{"source": filename, "chunk_index": i} for i in range(len(chunks))]

            self.collection.add(documents=chunks, metadatas=metadatas, ids=ids)
            return f"[✅ 知识库构建成功：{filename} 已被解析为 {len(chunks)} 个知识块，永久存入校本向量库！]"
        except Exception as e:
            return f"[❌ 解析 PDF 失败: {str(e)}]"

    def retrieve_context(self, query: str, n_results: int = 3) -> str:
        """Sync retrieval (ChromaDB query is fast)."""
        if not query.strip() or self.collection.count() == 0:
            return ""

        try:
            results = self.collection.query(query_texts=[query], n_results=n_results)
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]

            if not documents:
                return ""

            context = "【本地校本资料检索结果】：\n"
            for i, (doc, meta) in enumerate(zip(documents, metadatas)):
                source = meta.get("source", "未知来源")
                context += f"--- 片段 {i + 1} (来源文件: {source}) ---\n{doc}\n\n"
            return context
        except Exception as e:
            print(f"检索失败: {e}")
            return ""
