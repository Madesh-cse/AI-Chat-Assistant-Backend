from fastapi import ( # type: ignore
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException,
    Depends,
)  

from app.db.database import SessionLocal
from app.services.pdf_service import pdf_service
from app.services.chat_database import ChatDatabase

from app.core.dependencies import get_current_user
from app.models.user import User


router = APIRouter(
    prefix="/pdf",
    tags=["PDF"],
)


# ============================================================
# UPLOAD PDF
# ============================================================

@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    conversation_id: int = Form(...),
    current_user: User = Depends(get_current_user),
):
    print("\n==============================")
    print("PDF UPLOAD")
    print("==============================")

    print("Filename:", file.filename)
    print("Conversation ID:", conversation_id)
    print("User ID:", current_user.id)

    # --------------------------------------------------------
    # Validate filename
    # --------------------------------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename missing",
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported",
        )

    db = SessionLocal()

    try:
        # ----------------------------------------------------
        # Verify conversation belongs to current user
        # ----------------------------------------------------

        conversation = ChatDatabase.get_conversation_for_user(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id,
        )

        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
            )

        print(
            "Conversation found:",
            conversation.id,
        )

        # ----------------------------------------------------
        # Create PDF database record
        # ----------------------------------------------------

        pdf = ChatDatabase.create_pdf_document(
            db=db,
            filename=file.filename,
            file_path="",
            conversation_id=conversation_id,
        )

        if not pdf:
            raise HTTPException(
                status_code=500,
                detail="Failed to create PDF record",
            )

        print(
            "PDF record created:",
            pdf.id,
        )

        # ----------------------------------------------------
        # Save PDF
        # ----------------------------------------------------

        file_path = pdf_service.save_pdf(
            file,
            pdf.id,
        )

        print(
            "PDF saved:",
            file_path,
        )

        # ----------------------------------------------------
        # Update file path
        # ----------------------------------------------------

        pdf.file_path = file_path

        db.commit()
        db.refresh(pdf)

        # ----------------------------------------------------
        # Extract PDF text
        # ----------------------------------------------------

        print("\nExtracting PDF text...")

        documents = pdf_service.extract_text(
            file_path
        )

        print(
            "Pages extracted:",
            len(documents),
        )

        # ----------------------------------------------------
        # Split into chunks
        # ----------------------------------------------------

        print("\nSplitting PDF into chunks...")

        chunks = pdf_service.split_documents(
            documents
        )

        print(
            "Chunks created:",
            len(chunks),
        )

        # ----------------------------------------------------
        # Create vector store
        # ----------------------------------------------------

        print("\nCreating vector store...")

        pdf_service.create_vector_store(
            chunks,
            pdf.id,
        )

        print(
            "Vector store created ✅"
        )

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        return {
            "success": True,
            "id": pdf.id,
            "filename": pdf.filename,
            "conversation_id": conversation_id,
            "pages": len(documents),
            "chunks": len(chunks),
            "message": "PDF uploaded successfully",
        }

    except HTTPException:
        raise

    except Exception as e:
        print("\n==============================")
        print("PDF UPLOAD ERROR")
        print("==============================")

        print(e)

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="PDF upload failed",
        )

    finally:
        db.close()

        print(
            "\nPDF DATABASE CONNECTION CLOSED ✅"
        )


# ============================================================
# PDF SUMMARY
# ============================================================

@router.get("/{pdf_id}/summary")
async def summarize_pdf(
    pdf_id: int,
    current_user: User = Depends(get_current_user),
):
    db = SessionLocal()

    try:
        # ----------------------------------------------------
        # Get PDF
        # ----------------------------------------------------

        pdf = ChatDatabase.get_pdf_document(
            db=db,
            pdf_id=pdf_id,
        )

        if not pdf:
            raise HTTPException(
                status_code=404,
                detail="PDF not found",
            )

        # ----------------------------------------------------
        # Verify PDF's conversation belongs to user
        # ----------------------------------------------------

        conversation = ChatDatabase.get_conversation_for_user(
            db=db,
            conversation_id=pdf.conversation_id,
            user_id=current_user.id,
        )

        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="PDF not found",
            )

        print(
            "\nGenerating summary for PDF:",
            pdf_id,
        )

        # ----------------------------------------------------
        # Extract text
        # ----------------------------------------------------

        documents = pdf_service.extract_text(
            pdf.file_path
        )

        # ----------------------------------------------------
        # Generate summary
        # ----------------------------------------------------

        summary = pdf_service.summarize(
            documents
        )

        return {
            "success": True,
            "pdf_id": pdf_id,
            "filename": pdf.filename,
            "summary": summary,
        }

    except HTTPException:
        raise

    except Exception as e:
        print(
            "PDF SUMMARY ERROR:",
            e,
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to summarize PDF",
        )

    finally:
        db.close()


# ============================================================
# ASK QUESTION ABOUT PDF
# ============================================================

@router.post("/ask")
async def ask_pdf_question(
    request: dict,
    current_user: User = Depends(get_current_user),
):
    pdf_id = request.get("pdf_id")
    question = request.get("question")

    # --------------------------------------------------------
    # Validate request
    # --------------------------------------------------------

    if not pdf_id:
        raise HTTPException(
            status_code=400,
            detail="pdf_id is required",
        )

    if not question:
        raise HTTPException(
            status_code=400,
            detail="question is required",
        )

    db = SessionLocal()

    try:
        # ----------------------------------------------------
        # Get PDF
        # ----------------------------------------------------

        pdf = ChatDatabase.get_pdf_document(
            db=db,
            pdf_id=pdf_id,
        )

        if not pdf:
            raise HTTPException(
                status_code=404,
                detail="PDF not found",
            )

        # ----------------------------------------------------
        # Verify PDF belongs to current user
        # ----------------------------------------------------

        conversation = ChatDatabase.get_conversation_for_user(
            db=db,
            conversation_id=pdf.conversation_id,
            user_id=current_user.id,
        )

        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="PDF not found",
            )

        print("\n==============================")
        print("PDF QUESTION")
        print("==============================")

        print(
            "PDF ID:",
            pdf_id,
        )

        print(
            "User ID:",
            current_user.id,
        )

        print(
            "Question:",
            question,
        )

        # ----------------------------------------------------
        # Ask PDF service
        # ----------------------------------------------------

        answer = pdf_service.ask_question(
            pdf_id=pdf_id,
            question=question,
        )

        return {
            "success": True,
            "pdf_id": pdf_id,
            "filename": pdf.filename,
            "question": question,
            "answer": answer,
        }

    except HTTPException:
        raise

    except Exception as e:
        print(
            "\nPDF QUESTION ERROR:"
        )

        print(e)

        raise HTTPException(
            status_code=500,
            detail="Failed to answer PDF question",
        )

    finally:
        db.close()