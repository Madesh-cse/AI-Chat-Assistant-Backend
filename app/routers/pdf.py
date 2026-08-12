from fastapi import (APIRouter,UploadFile,File,Form,HTTPException,)  # type: ignore

from app.db.database import SessionLocal
from app.services.pdf_service import pdf_service
from app.services.chat_database import ChatDatabase


router = APIRouter(
    prefix="/pdf",
    tags=["PDF"],
)


@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    conversation_id: int = Form(...),
):

    print("\n==============================")
    print("PDF UPLOAD")
    print("==============================")

    print("Filename:", file.filename)
    print("Conversation ID:", conversation_id)

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

        conversation = ChatDatabase.get_conversation(
            db=db,
            conversation_id=conversation_id,
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

        pdf = ChatDatabase.create_pdf_document(
            db=db,
            filename=file.filename,
            file_path="",
            conversation_id=conversation_id,
        )

        print(
            "PDF record created:",
            pdf.id,
        )

        file_path = pdf_service.save_pdf(
            file,
            pdf.id,
        )

        print(
            "PDF saved:",
            file_path,
        )


        pdf.file_path = file_path

        db.commit()

        db.refresh(pdf)

        print("\nExtracting PDF text...")

        documents = pdf_service.extract_text(
            file_path
        )

        print(
            "Pages extracted:",
            len(documents),
        )

        print("\nSplitting PDF into chunks...")

        chunks = pdf_service.split_documents(
            documents
        )

        print(
            "Chunks created:",
            len(chunks),
        )

        print("\nCreating vector store...")

        pdf_service.create_vector_store(
            chunks,
            pdf.id,
        )

        print(
            "Vector store created ✅"
        )

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
            detail=str(e),
        )

    finally:

        db.close()

        print(
            "\nPDF DATABASE CONNECTION CLOSED ✅"
        )

@router.get("/{pdf_id}/summary")
async def summarize_pdf(
    pdf_id: int,
):

    db = SessionLocal()

    try:

        pdf = ChatDatabase.get_pdf_document(
            db=db,
            pdf_id=pdf_id,
        )

        if not pdf:

            raise HTTPException(
                status_code=404,
                detail="PDF not found",
            )

        print(
            "\nGenerating summary for PDF:",
            pdf_id,
        )

        documents = pdf_service.extract_text(
            pdf.file_path
        )

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

        print("PDF SUMMARY ERROR:", e)

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    finally:

        db.close()

@router.post("/ask")
async def ask_pdf_question(
    request: dict,
):

    pdf_id = request.get(
        "pdf_id"
    )

    question = request.get(
        "question"
    )


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

        pdf = ChatDatabase.get_pdf_document(
            db=db,
            pdf_id=pdf_id,
        )

        if not pdf:

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
            "Question:",
            question,
        )

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

        print("\nPDF QUESTION ERROR:")
        print(e)

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    finally:

        db.close()