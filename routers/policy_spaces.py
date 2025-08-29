from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import uuid

from database import get_db
from models import PolicySpace

router = APIRouter()

class PolicySpaceCreate(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    created_by: str

class PolicySpaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class PolicySpaceResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    created_by: str
    is_active: bool
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True

@router.post("/", response_model=PolicySpaceResponse)
async def create_policy_space(
    policy_space: PolicySpaceCreate,
    db: Session = Depends(get_db)
):
    # Generate ID if not provided
    policy_space_id = policy_space.id or str(uuid.uuid4())
    
    # Check if ID already exists
    existing = db.query(PolicySpace).filter(PolicySpace.id == policy_space_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Policy space with this ID already exists"
        )
    
    db_policy_space = PolicySpace(
        id=policy_space_id,
        name=policy_space.name,
        description=policy_space.description,
        created_by=policy_space.created_by
    )
    
    db.add(db_policy_space)
    db.commit()
    db.refresh(db_policy_space)
    
    return PolicySpaceResponse(
        id=db_policy_space.id,
        name=db_policy_space.name,
        description=db_policy_space.description,
        created_by=db_policy_space.created_by,
        is_active=db_policy_space.is_active,
        created_at=db_policy_space.created_at.isoformat(),
        updated_at=db_policy_space.updated_at.isoformat() if db_policy_space.updated_at else None
    )

@router.get("/", response_model=List[PolicySpaceResponse])
async def get_policy_spaces(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(PolicySpace)
    
    if is_active is not None:
        query = query.filter(PolicySpace.is_active == is_active)
    
    policy_spaces = query.order_by(PolicySpace.created_at.desc()).all()
    
    return [
        PolicySpaceResponse(
            id=ps.id,
            name=ps.name,
            description=ps.description,
            created_by=ps.created_by,
            is_active=ps.is_active,
            created_at=ps.created_at.isoformat(),
            updated_at=ps.updated_at.isoformat() if ps.updated_at else None
        )
        for ps in policy_spaces
    ]

@router.get("/{policy_space_id}", response_model=PolicySpaceResponse)
async def get_policy_space(
    policy_space_id: str,
    db: Session = Depends(get_db)
):
    policy_space = db.query(PolicySpace).filter(PolicySpace.id == policy_space_id).first()
    
    if not policy_space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy space not found"
        )
    
    return PolicySpaceResponse(
        id=policy_space.id,
        name=policy_space.name,
        description=policy_space.description,
        created_by=policy_space.created_by,
        is_active=policy_space.is_active,
        created_at=policy_space.created_at.isoformat(),
        updated_at=policy_space.updated_at.isoformat() if policy_space.updated_at else None
    )

@router.put("/{policy_space_id}", response_model=PolicySpaceResponse)
async def update_policy_space(
    policy_space_id: str,
    policy_space_update: PolicySpaceUpdate,
    db: Session = Depends(get_db)
):
    db_policy_space = db.query(PolicySpace).filter(PolicySpace.id == policy_space_id).first()
    
    if not db_policy_space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy space not found"
        )
    
    update_data = policy_space_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_policy_space, field, value)
    
    db.commit()
    db.refresh(db_policy_space)
    
    return PolicySpaceResponse(
        id=db_policy_space.id,
        name=db_policy_space.name,
        description=db_policy_space.description,
        created_by=db_policy_space.created_by,
        is_active=db_policy_space.is_active,
        created_at=db_policy_space.created_at.isoformat(),
        updated_at=db_policy_space.updated_at.isoformat() if db_policy_space.updated_at else None
    )

@router.delete("/{policy_space_id}")
async def delete_policy_space(
    policy_space_id: str,
    db: Session = Depends(get_db)
):
    db_policy_space = db.query(PolicySpace).filter(PolicySpace.id == policy_space_id).first()
    
    if not db_policy_space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy space not found"
        )
    
    db.delete(db_policy_space)
    db.commit()
    
    return {"message": f"Policy space {policy_space_id} deleted successfully"}