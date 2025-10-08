"""
患者管理API
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import get_current_user
from ..models.user import User
from ..models.patient import Patient, PatientCreate, PatientUpdate, PatientResponse
import uuid


router = APIRouter(prefix="/patients", tags=["就诊人管理"])


@router.get("/", summary="获取当前用户的就诊人列表")
def list_patients(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patients = db.query(Patient).filter(Patient.user_id == current_user.id).all()
    return {"patients": [p.to_dict() for p in patients]}


@router.post("/", response_model=PatientResponse, summary="创建就诊人")
def create_patient(
    payload: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = Patient(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        patient_unique_id=str(uuid.uuid4()),
        **payload.dict(exclude_unset=True),
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.put("/{patient_unique_id}", response_model=PatientResponse, summary="更新就诊人")
def update_patient(
    patient_unique_id: str,
    payload: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = (
        db.query(Patient)
        .filter(Patient.patient_unique_id == patient_unique_id, Patient.user_id == current_user.id)
        .first()
    )
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="就诊人不存在")

    for k, v in payload.dict(exclude_unset=True).items():
        setattr(patient, k, v)
    db.commit()
    db.refresh(patient)
    return patient


@router.delete("/{patient_unique_id}", summary="删除就诊人")
def delete_patient(
    patient_unique_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = (
        db.query(Patient)
        .filter(Patient.patient_unique_id == patient_unique_id, Patient.user_id == current_user.id)
        .first()
    )
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="就诊人不存在")
    db.delete(patient)
    db.commit()
    return {"status": "success"}


