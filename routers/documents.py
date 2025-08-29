from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import shutil
from pathlib import Path

from database import get_db
from models import Document

router = APIRouter()

def ensure_upload_directory(storage_path: str):
    Path(storage_path).mkdir(parents=True, exist_ok=True)

@router.post("/upload/{policy_space_id}")
async def upload_document(
    policy_space_id: str,
    file: UploadFile = File(...),
    created_by: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    storage_path = os.getenv("FILE_STORAGE_PATH", "./uploads")
    ensure_upload_directory(storage_path)
    
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(storage_path, unique_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = os.path.getsize(file_path)
        
        db_document = Document(
            policy_space_id=policy_space_id,
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            content_type=file.content_type or "application/octet-stream",
            created_by=created_by,
            description=description
        )
        
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        return {
            "id": db_document.id,
            "policy_space_id": db_document.policy_space_id,
            "filename": db_document.original_filename,
            "file_size": db_document.file_size,
            "content_type": db_document.content_type,
            "created_by": db_document.created_by,
            "description": db_document.description,
            "created_at": db_document.created_at
        }
    
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )

@router.get("/{policy_space_id}")
async def get_documents(
    policy_space_id: str,
    db: Session = Depends(get_db)
):
    documents = db.query(Document).filter(
        Document.policy_space_id == policy_space_id
    ).order_by(Document.created_at.desc()).all()
    
    return [
        {
            "id": doc.id,
            "policy_space_id": doc.policy_space_id,
            "filename": doc.original_filename,
            "file_size": doc.file_size,
            "content_type": doc.content_type,
            "created_by": doc.created_by,
            "description": doc.description,
            "created_at": doc.created_at,
            "updated_at": doc.updated_at
        }
        for doc in documents
    ]