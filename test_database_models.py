import os

from app.db.database import SessionLocal
from app.services.chat_database import ChatDatabase
from app.services.pdf_service import pdf_service
from app.models.user import User


# ============================================================
# CONFIGURATION
# ============================================================

PDF_PATH = "uploads/Piston_Docker_Quick_Reference.pdf"

TEST_EMAIL = "madesh_pdf_test_001@test.com"
TEST_NAME = "Madesh"


# ============================================================
# DATABASE
# ============================================================

db = SessionLocal()


try:

    print("\n")
    print("=" * 60)
    print("STARTING PDF DATABASE TEST")
    print("=" * 60)


    # ========================================================
    # 1. GET OR CREATE USER
    # ========================================================

    print("\n1. CHECKING USER...")

    user = (
        db.query(User)
        .filter(
            User.email == TEST_EMAIL
        )
        .first()
    )

    if user:

        print("EXISTING USER FOUND ✅")

    else:

        user = ChatDatabase.create_user(
            db=db,
            name=TEST_NAME,
            email=TEST_EMAIL,
        )

        print("USER CREATED ✅")

    print("User ID:", user.id)
    print("Name:", user.name)
    print("Email:", user.email)


    # ========================================================
    # 2. CREATE CONVERSATION
    # ========================================================

    print("\n2. CREATING CONVERSATION...")

    conversation = ChatDatabase.create_conversation(
        db=db,
        user_id=user.id,
        title="PDF Testing Conversation",
    )

    print("CONVERSATION CREATED ✅")
    print("Conversation ID:", conversation.id)
    print("Title:", conversation.title)


    # ========================================================
    # 3. CREATE USER MESSAGE
    # ========================================================

    print("\n3. CREATING USER MESSAGE...")

    user_message = ChatDatabase.create_message(
        db=db,
        conversation_id=conversation.id,
        role="user",
        content="I am uploading a PDF for testing.",
    )

    print("USER MESSAGE CREATED ✅")
    print("Message ID:", user_message.id)


    # ========================================================
    # 4. CHECK PDF FILE
    # ========================================================

    print("\n4. CHECKING PDF FILE...")

    if not os.path.exists(PDF_PATH):

        raise FileNotFoundError(
            f"PDF file not found: {PDF_PATH}"
        )

    print("PDF FOUND ✅")
    print("Path:", PDF_PATH)

    filename = os.path.basename(
        PDF_PATH
    )

    print("Filename:", filename)


    # ========================================================
    # 5. CREATE PDF DATABASE RECORD
    # ========================================================

    print("\n5. CREATING PDF DATABASE RECORD...")

    pdf = ChatDatabase.create_pdf_document(
        db=db,
        filename=filename,
        file_path=PDF_PATH,
        conversation_id=conversation.id,
    )

    print("PDF DOCUMENT CREATED ✅")

    print("PDF ID:", pdf.id)
    print("Filename:", pdf.filename)
    print("File Path:", pdf.file_path)
    print("Conversation ID:", pdf.conversation_id)


    # ========================================================
    # 6. EXTRACT PDF TEXT
    # ========================================================

    print("\n6. EXTRACTING PDF TEXT...")

    documents = pdf_service.extract_text(
        PDF_PATH
    )

    print(
        "Pages extracted:",
        len(documents),
    )

    if not documents:

        raise ValueError(
            "No text could be extracted from the PDF."
        )

    # Print first page preview

    first_page = documents[0].page_content

    print("\nFIRST PAGE PREVIEW:")
    print("-" * 60)

    print(
        first_page[:1000]
    )

    print("-" * 60)


    # ========================================================
    # 7. SPLIT PDF INTO CHUNKS
    # ========================================================

    print("\n7. SPLITTING PDF INTO CHUNKS...")

    chunks = pdf_service.split_documents(
        documents
    )

    print(
        "Chunks created:",
        len(chunks),
    )

    if not chunks:

        raise ValueError(
            "No chunks were created from the PDF."
        )


    # ========================================================
    # 8. CREATE FAISS VECTOR STORE
    # ========================================================

    print("\n8. CREATING FAISS VECTOR STORE...")

    vector_path = pdf_service.create_vector_store(
        chunks,
        pdf.id,
    )

    print(
        "VECTOR STORE CREATED ✅"
    )

    print(
        "Vector path:",
        vector_path,
    )


    # ========================================================
    # 9. VERIFY VECTOR STORE
    # ========================================================

    print("\n9. VERIFYING VECTOR STORE...")

    vectorstore = pdf_service.load_vector_store(
        pdf.id
    )

    print(
        "VECTOR STORE LOADED ✅"
    )

    # Test similarity search

    test_query = "Docker"

    results = vectorstore.similarity_search(
        test_query,
        k=2,
    )

    print(
        "Similarity search results:",
        len(results),
    )

    for index, document in enumerate(
        results,
        start=1,
    ):

        print(
            f"\nResult {index}:"
        )

        print(
            document.page_content[:500]
        )


    # ========================================================
    # 10. GENERATE PDF SUMMARY
    # ========================================================

    print("\n10. GENERATING PDF SUMMARY...")

    summary = pdf_service.summarize(
        documents
    )

    print("\n")
    print("=" * 60)
    print("PDF SUMMARY")
    print("=" * 60)

    print(summary)


    # ========================================================
    # 11. ASK QUESTION ABOUT PDF
    # ========================================================

    question = (
        "What is the main topic of this PDF?"
    )

    print("\n")
    print("=" * 60)
    print("ASKING PDF QUESTION")
    print("=" * 60)

    print(
        "Question:",
        question,
    )


    answer = pdf_service.ask_question(
        pdf_id=pdf.id,
        question=question,
    )


    print("\n")
    print("=" * 60)
    print("PDF ANSWER")
    print("=" * 60)

    print(answer)


    # ========================================================
    # 12. CREATE AI MESSAGE
    # ========================================================

    print("\n12. SAVING AI MESSAGE...")

    ai_message = ChatDatabase.create_message(
        db=db,
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
    )

    print(
        "AI MESSAGE CREATED ✅"
    )

    print(
        "AI Message ID:",
        ai_message.id,
    )


    # ========================================================
    # 13. GET PDF FROM DATABASE
    # ========================================================

    print("\n13. FETCHING PDF FROM DATABASE...")

    found_pdf = ChatDatabase.get_pdf_document(
        db=db,
        pdf_id=pdf.id,
    )

    if not found_pdf:

        raise ValueError(
            "PDF was not found in database."
        )

    print(
        "PDF FOUND IN DATABASE ✅"
    )

    print(
        "PDF ID:",
        found_pdf.id,
    )

    print(
        "Filename:",
        found_pdf.filename,
    )

    print(
        "File Path:",
        found_pdf.file_path,
    )

    print(
        "Conversation ID:",
        found_pdf.conversation_id,
    )


    # ========================================================
    # 14. GET ALL PDFs FOR CONVERSATION
    # ========================================================

    print("\n14. GETTING CONVERSATION PDFs...")

    pdfs = ChatDatabase.get_conversation_pdfs(
        db=db,
        conversation_id=conversation.id,
    )


    print("\n")
    print("=" * 60)
    print("CONVERSATION PDFs")
    print("=" * 60)


    if not pdfs:

        print(
            "No PDFs found."
        )

    else:

        for item in pdfs:

            print(
                f"ID: {item.id} | "
                f"Filename: {item.filename} | "
                f"Path: {item.file_path} | "
                f"Conversation: {item.conversation_id}"
            )


    # ========================================================
    # 15. SUCCESS
    # ========================================================

    print("\n")
    print("=" * 60)
    print("PDF TEST COMPLETED SUCCESSFULLY ✅")
    print("=" * 60)

    print(
        "\nUser ID:",
        user.id,
    )

    print(
        "Conversation ID:",
        conversation.id,
    )

    print(
        "PDF ID:",
        pdf.id,
    )

    print(
        "Pages:",
        len(documents),
    )

    print(
        "Chunks:",
        len(chunks),
    )

    print(
        "Vector Store:",
        vector_path,
    )


except Exception as e:

    print("\n")
    print("=" * 60)
    print("TEST ERROR ❌")
    print("=" * 60)

    print(
        "Error Type:",
        type(e).__name__,
    )

    print(
        "Error:",
        str(e),
    )

    db.rollback()

    print(
        "\nDATABASE ROLLBACK COMPLETED"
    )


finally:

    db.close()

    print(
        "\nDATABASE CONNECTION CLOSED ✅"
    )