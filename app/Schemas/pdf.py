from pydantic import BaseModel  # type: ignore


class PDFUploadResponse(BaseModel):

    id: int
    filename: str
    message: str


class PDFSummaryResponse(BaseModel):

    pdf_id: int
    summary: str


class PDFQuestionRequest(BaseModel):

    pdf_id: int
    question: str


class PDFQuestionResponse(BaseModel):

    pdf_id: int
    question: str
    answer: str