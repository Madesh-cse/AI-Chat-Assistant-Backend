import os

from langchain_community.document_loaders import PyPDFLoader  # type: ignore
from langchain_text_splitters import RecursiveCharacterTextSplitter  # type: ignore
from langchain_community.vectorstores import FAISS  # type: ignore
from langchain_ollama import OllamaEmbeddings  # type: ignore

from app.services.llm import llm


UPLOAD_DIR = "uploads/pdfs"
VECTOR_DIR = "app/vectorstore/pdf_vectors"


os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(VECTOR_DIR, exist_ok=True)


class PDFService:

    def __init__(self):

        self.embeddings = OllamaEmbeddings(
            model="nomic-embed-text"
        )

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
    # CREATE VECTOR STORE
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
    # ASK QUESTION
    # =========================================================

    def ask_question(
        self,
        pdf_id: int,
        question: str,
    ):

        if not question.strip():

            return "Please provide a question."

        vectorstore = self.load_vector_store(
            pdf_id
        )

        documents = vectorstore.similarity_search(
            question,
            k=5,
        )

        print("\n==============================")
        print("PDF RAG SEARCH")
        print("==============================")

        print(
            "Question:",
            question,
        )

        print(
            "Documents found:",
            len(documents),
        )

        if not documents:

            return (
                "I couldn't find that information "
                "in the uploaded PDF."
            )

        context = "\n\n".join(
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