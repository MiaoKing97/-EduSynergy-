# backend/app/services/rag_service.py
import os
import io
import chromadb
import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter


class RAGService:
    def __init__(self):
        # 1. 初始化持久化本地向量数据库
        persist_directory = os.path.join(os.getcwd(), "chroma_data")
        self.chroma_client = chromadb.PersistentClient(path=persist_directory)

        # 2. 创建或加载集合（Collection）
        # ChromaDB 默认会使用 all-MiniLM-L6-v2 模型将文本转化为向量
        self.collection = self.chroma_client.get_or_create_collection(name="school_knowledge_base")

        # 3. 初始化文本分块器（按段落切分，保留上下文重叠）
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,  # 每个文本块大约 500 个字符
            chunk_overlap=50,  # 相邻块重叠 50 个字符，防止句子被生硬切断
            length_function=len,
        )

    def ingest_pdf(self, file_bytes: bytes, filename: str) -> str:
        """解析 PDF，分块并存入向量数据库"""
        try:
            text = ""
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

            if not text.strip():
                return f"[警告：未能从 {filename} 中提取到有效文本，可能为纯扫描版图片PDF]"

            # 分块
            chunks = self.text_splitter.split_text(text)
            if not chunks:
                return f"[警告：{filename} 文本切块失败]"

            # 准备存入 ChromaDB 的数据结构
            # 使用 文件名+索引 作为唯一 ID，防止重复
            ids = [f"{filename}_{i}" for i in range(len(chunks))]
            metadatas = [{"source": filename, "chunk_index": i} for i in range(len(chunks))]

            # 写入向量库
            self.collection.add(
                documents=chunks,
                metadatas=metadatas,
                ids=ids
            )
            return f"[✅ 知识库构建成功：{filename} 已被解析为 {len(chunks)} 个知识块，永久存入校本向量库！]"
        except Exception as e:
            return f"[❌ 解析 PDF 失败: {str(e)}]"

    def retrieve_context(self, query: str, n_results: int = 3) -> str:
        """根据用户问题，检索最相关的 N 个文本块"""
        if not query.strip() or self.collection.count() == 0:
            return ""

        try:
            # 检索最相关的片段
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )

            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]

            if not documents:
                return ""

            # 拼装上下文供 LLM 读取
            context = "【本地校本资料检索结果】：\n"
            for i, (doc, meta) in enumerate(zip(documents, metadatas)):
                source = meta.get("source", "未知来源")
                context += f"--- 片段 {i + 1} (来源文件: {source}) ---\n{doc}\n\n"

            return context
        except Exception as e:
            print(f"检索失败: {e}")
            return ""
