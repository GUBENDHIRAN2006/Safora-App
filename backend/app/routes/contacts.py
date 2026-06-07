from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.db.database import get_db
from app.models.models import User, EmergencyContact
from app.schemas.schemas import EmergencyContactCreate, EmergencyContactUpdate, EmergencyContactResponse
from app.routes.auth import get_current_user

router = APIRouter(prefix="/contacts", tags=["Emergency Contacts"])

@router.get("/", response_model=List[EmergencyContactResponse])
def get_contacts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieves all emergency contacts configured by the user, sorted by priority."""
    return db.query(EmergencyContact)\
             .filter(EmergencyContact.user_id == current_user.id)\
             .order_by(EmergencyContact.priority.asc())\
             .all()


@router.post("/", response_model=EmergencyContactResponse, status_code=status.HTTP_201_CREATED)
def create_contact(
    contact_in: EmergencyContactCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Creates a new emergency contact for the user."""
    # Limit number of contacts per user to avoid abuse
    contact_count = db.query(EmergencyContact).filter(EmergencyContact.user_id == current_user.id).count()
    if contact_count >= 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum limit of 10 emergency contacts reached."
        )
    
    # If this is set as priority 1, update existing contacts to lower priority if necessary
    if contact_in.priority == 1:
        db.query(EmergencyContact)\
          .filter(EmergencyContact.user_id == current_user.id, EmergencyContact.priority == 1)\
          .update({EmergencyContact.priority: 2})
          
    new_contact = EmergencyContact(
        user_id=current_user.id,
        name=contact_in.name,
        relationship=contact_in.relationship,
        mobile_number=contact_in.mobile_number,
        priority=contact_in.priority
    )
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)
    return new_contact


@router.put("/{contact_id}", response_model=EmergencyContactResponse)
def update_contact(
    contact_id: UUID,
    contact_in: EmergencyContactUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates an existing emergency contact's details."""
    contact = db.query(EmergencyContact)\
                .filter(EmergencyContact.id == contact_id, EmergencyContact.user_id == current_user.id)\
                .first()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emergency contact not found"
        )
        
    update_data = contact_in.model_dump(exclude_unset=True)
    
    # If priority is updated to 1, demote other priority 1s
    if update_data.get("priority") == 1:
        db.query(EmergencyContact)\
          .filter(EmergencyContact.user_id == current_user.id, EmergencyContact.priority == 1)\
          .update({EmergencyContact.priority: 2})

    for key, value in update_data.items():
        setattr(contact, key, value)
        
    db.commit()
    db.refresh(contact)
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(
    contact_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Removes an emergency contact."""
    contact = db.query(EmergencyContact)\
                .filter(EmergencyContact.id == contact_id, EmergencyContact.user_id == current_user.id)\
                .first()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emergency contact not found"
        )
    
    db.delete(contact)
    db.commit()
    return
