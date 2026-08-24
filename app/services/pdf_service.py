import os
import pickle
import concurrent.futures

from langchain_community.document_loaders import PyPDFLoader  # type: ignore
from langchain_text_splitters import RecursiveCharacterTextSplitter  # type: ignore
from langchain_community.vectorstores import FAISS  # type: ignore
from langchain_community.retrievers import BM25Retriever  # type: ignore
from langchain_classic.retrievers import EnsembleRetriever  # type: ignore
from langchain_ollama import OllamaEmbeddings  # type: ignore
from sentence_transformers import CrossEncoder  # type: ignore

from app.services.llm import llm


UPLOAD_DIR = "uploads/pdfs"
VECTOR_DIR = "app/vectorstore/pdf_vectors"

# Reranker is stateless/CPU-friendly — load once at module level so it
# isn't reloaded per request or per PDFService instance.
_RERANKER = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(VECTOR_DIR, exist_ok=True)


class PDFService:

    def __init__(self):

        self.embeddings = OllamaEmbeddings(
            model="nomic-embed-text"
        )

        self.reranker = _RERANKER

    # =========================================================
    # RESPONSE CONTENT
    # =========================================================

    def _extract_response_content(self, response):

        content = getattr(
            response,
            "content",
            "",
        )

        if isinstance(content, str):

            return content.strip()

        if isinstance(content, list):

            text_parts = []

            for item in content:

                if isinstance(item, str):

                    text_parts.append(item)

                elif isinstance(item, dict):

                    if "text" in item:

                        text_parts.append(
                            str(item["text"])
                        )

            return "\n".join(
                text_parts
            ).strip()

        return str(content).strip()

    # =========================================================
    # SAVE PDF
    # =========================================================

    def save_pdf(
        self,
        file,
        pdf_id: int,
    ):

        filename = os.path.basename(
            file.filename
        )

        file_path = os.path.join(
            UPLOAD_DIR,
            f"{pdf_id}_{filename}",
        )

        with open(
            file_path,
            "wb",
        ) as buffer:

            buffer.write(
                file.file.read()
            )

        return file_path

    # =========================================================
    # EXTRACT TEXT
    # =========================================================

    def extract_text(
        self,
        file_path: str,
    ):

        if not os.path.exists(file_path):

            raise FileNotFoundError(
                f"PDF not found: {file_path}"
            )

        loader = PyPDFLoader(
            file_path
        )

        documents = loader.load()

        if not documents:

            raise ValueError(
                "No text could be extracted from PDF"
            )

        return documents

    # =========================================================
    # SPLIT DOCUMENT
    # =========================================================

    def split_documents(
        self,
        documents,
    ):

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
        )

        chunks = splitter.split_documents(
            documents
        )

        if not chunks:

            raise ValueError(
                "No chunks created from PDF"
            )

        return chunks

    # =========================================================
    # CONTEXTUAL CHUNK HEADERS
    # =========================================================
    # Prepends a short LLM-generated blurb to each chunk describing
    # where it sits in the document, before embedding. This is what
    # fixes chunks like "the fee increases by 15%" that are meaningless
    # in isolation. Run once at ingestion time.

    def _generate_chunk_context(
        self,
        chunk_text: str,
        doc_summary: str,
    ) -> str:

        prompt = f"""
You are helping prepare a document chunk for search retrieval.

DOCUMENT SUMMARY:
{doc_summary}

CHUNK:
{chunk_text}

Give a short 1-2 sentence context that situates this chunk within the
overall document (e.g. what section/topic it belongs to). Answer ONLY
with the context sentence(s), nothing else.
"""

        try:

            response = llm.invoke(prompt)

            context = self._extract_response_content(response)

            return context if context else ""

        except Exception as e:

            print("Context generation failed for chunk:", e)

            return ""

    def add_contextual_headers(
        self,
        chunks,
        documents,
        max_workers: int = 5,
    ):

        # Build a short whole-document summary once, used as shared
        # context for every chunk's header (cheaper than passing the
        # full doc into every single chunk call).

        full_text = "\n\n".join(
            document.page_content
            for document in documents
        )[:15000]

        summary_prompt = f"""
Summarize the following document in 3-5 sentences, capturing its main
topic, structure, and purpose. This will be used as shared context for
indexing chunks of the document.

DOCUMENT:
{full_text}
"""

        try:

            summary_response = llm.invoke(summary_prompt)

            doc_summary = self._extract_response_content(
                summary_response
            )

        except Exception as e:

            print("Document summary for contextualization failed:", e)

            doc_summary = ""

        print(
            "\nGenerating contextual headers for",
            len(chunks),
            "chunks...",
        )

        def process_chunk(chunk):

            context = self._generate_chunk_context(
                chunk.page_content,
                doc_summary,
            )

            if context:

                chunk.page_content = f"{context}\n\n{chunk.page_content}"

            return chunk

        # Parallelize since this is the slow, one-time-per-PDF step.
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers
        ) as executor:

            contextualized_chunks = list(
                executor.map(process_chunk, chunks)
            )

        print("Contextual headers done ✅")

        return contextualized_chunks

    # =========================================================
    # CREATE VECTOR STORE + BM25 (HYBRID)
    # =========================================================

    def create_vector_store(
        self,
        chunks,
        pdf_id: int,
    ):

        if not chunks:

            raise ValueError(
                "Cannot create vector store without chunks"
            )

        vectorstore = FAISS.from_documents(
            chunks,
            self.embeddings,
        )

        vector_path = os.path.join(
            VECTOR_DIR,
            str(pdf_id),
        )

        os.makedirs(
            vector_path,
            exist_ok=True,
        )

        vectorstore.save_local(
            vector_path
        )

        # BM25Retriever isn't natively disk-serializable via LangChain,
        # so we persist the underlying chunk docs and rebuild the BM25
        # index from them on load. Cheap — BM25 build is fast even for
        # a few thousand chunks.

        bm25_path = os.path.join(
            vector_path,
            "bm25_chunks.pkl",
        )

        with open(bm25_path, "wb") as f:

            pickle.dump(chunks, f)

        return vector_path

    # =========================================================
    # LOAD VECTOR STORE
    # =========================================================

    def load_vector_store(
        self,
        pdf_id: int,
    ):

        vector_path = os.path.join(
            VECTOR_DIR,
            str(pdf_id),
        )

        if not os.path.exists(
            vector_path
        ):

            raise FileNotFoundError(
                f"PDF vector store not found: {vector_path}"
            )

        vectorstore = FAISS.load_local(
            vector_path,
            self.embeddings,
            allow_dangerous_deserialization=True,
        )

        return vectorstore

    # =========================================================
    # LOAD / BUILD HYBRID RETRIEVER
    # =========================================================

    def load_hybrid_retriever(
        self,
        pdf_id: int,
        k: int = 20,
    ):

        vectorstore = self.load_vector_store(pdf_id)

        vector_path = os.path.join(
            VECTOR_DIR,
            str(pdf_id),
        )

        bm25_path = os.path.join(
            vector_path,
            "bm25_chunks.pkl",
        )

        if not os.path.exists(bm25_path):

            raise FileNotFoundError(
                f"BM25 chunk store not found: {bm25_path}"
            )

        with open(bm25_path, "rb") as f:

            chunks = pickle.load(f)

        bm25_retriever = BM25Retriever.from_documents(chunks)
        bm25_retriever.k = k

        vector_retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": k,
                "fetch_k": k * 2,
            },
        )

        hybrid_retriever = EnsembleRetriever(
            retrievers=[bm25_retriever, vector_retriever],
            weights=[0.4, 0.6],
        )

        return hybrid_retriever

    # =========================================================
    # RERANK
    # =========================================================

    def rerank(
        self,
        question: str,
        documents,
        top_k: int = 5,
    ):

        if not documents:

            return []

        pairs = [
            [question, document.page_content]
            for document in documents
        ]

        scores = self.reranker.predict(pairs)

        ranked = sorted(
            zip(documents, scores),
            key=lambda pair: pair[1],
            reverse=True,
        )

        print("\nRerank scores (top -> bottom):")

        for document, score in ranked[:top_k]:

            preview = document.page_content[:80].replace("\n", " ")

            print(f"  {score:.4f}  {preview}...")

        return [document for document, _ in ranked[:top_k]]

    # =========================================================
    # SUMMARIZE PDF
    # =========================================================

    def summarize(
        self,
        documents,
    ):

        if not documents:

            return "No text found in the PDF."

        text = "\n\n".join(
            document.page_content
            for document in documents
        )

        # Prevent huge prompts
        text = text[:30000]

        prompt = f"""
You are a PDF document summarization assistant.

Read the document below and summarize it.

Use ONLY information present in the document.

Return the answer in this format:

# Summary

A short overview of the document.

## Main Topics

- Topic 1
- Topic 2
- Topic 3

## Important Points

- Important point 1
- Important point 2

## Key Findings

- Finding 1
- Finding 2

## Conclusion

A short conclusion.

Do not invent information.

DOCUMENT:

{text}
"""

        print("\n==============================")
        print("PDF SUMMARY PROMPT")
        print("==============================")

        print(
            "Characters:",
            len(text),
        )

        response = llm.invoke(
            prompt
        )

        answer = self._extract_response_content(
            response
        )

        print("\n==============================")
        print("PDF SUMMARY RESPONSE")
        print("==============================")

        print(answer)

        if not answer:

            return "The LLM returned an empty summary."

        return answer

    # =========================================================
    # ASK QUESTION (HYBRID RETRIEVAL + RERANK)
    # =========================================================

    def ask_question(
        self,
        pdf_id: int,
        question: str,
    ):

        if not question.strip():

            return "Please provide a question."

        retriever = self.load_hybrid_retriever(
            pdf_id
        )

        candidates = retriever.invoke(question)

        print("\n==============================")
        print("PDF RAG SEARCH (hybrid)")
        print("==============================")

        print(
            "Question:",
            question,
        )

        print(
            "Candidates retrieved:",
            len(candidates),
        )

        if not candidates:

            return (
                "I couldn't find that information "
                "in the uploaded PDF."
            )

        documents = self.rerank(
            question,
            candidates,
            top_k=5,
        )

        print(
            "Chunks after rerank:",
            len(documents),
        )

        if not documents:

            return (
                "I couldn't find that information "
                "in the uploaded PDF."
            )

        context = "\n\n---\n\n".join(
            document.page_content
            for document in documents
        )

        print(
            "\nRetrieved context:"
        )

        print(
            context[:5000]
        )

        prompt = f"""
You are an AI assistant answering questions about an uploaded PDF.

Answer the question using ONLY the context provided below.

Rules:

1. Do not use outside knowledge.
2. Do not invent information.
3. If the answer exists in the context, answer directly.
4. If the answer does not exist in the context, say exactly:

"I couldn't find that information in the uploaded PDF."

5. Use Markdown formatting when useful.

CONTEXT:

{context}

QUESTION:

{question}

ANSWER:
"""

        print("\n==============================")
        print("PDF QUESTION PROMPT")
        print("==============================")

        response = llm.invoke(
            prompt
        )

        answer = self._extract_response_content(
            response
        )

        print("\n==============================")
        print("PDF LLM RESPONSE")
        print("==============================")

        print(answer)

        if not answer:

            return (
                "The AI model returned an empty response."
            )

        return answer


pdf_service = PDFService()

# =========================================================
# INGESTION USAGE (update pdf.py route to match)
# =========================================================
# In your /upload route, insert the contextual-header step between
# split_documents() and create_vector_store():
#
#   documents = pdf_service.extract_text(file_path)
#   chunks = pdf_service.split_documents(documents)
#   chunks = pdf_service.add_contextual_headers(chunks, documents)   # NEW
#   pdf_service.create_vector_store(chunks, pdf.id)
#
# New dependencies to add to requirements.txt:
#   rank-bm25
#   sentence-transformers
#
# The first ask_question() call after a server restart will download
# the cross-encoder model (~80MB) from Hugging Face if it isn't already
# cached locally.