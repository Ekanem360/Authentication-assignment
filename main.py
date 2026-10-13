from datetime import timedelta
import auth
from database import Base, engine, get_db
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
import models
import schemas
from sqlalchemy.orm import Session

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FastAPI Authentication and Notes Assignment")


# --- Authentication Endpoints ---
@app.post(
    "/auth/register",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
  existing = (
      db.query(models.User)
      .filter(
          (models.User.username == user.username)
          | (models.User.email == user.email)
      )
      .first()
  )
  if existing:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Username or email already registered",
    )

  new_user = models.User(
      username=user.username,
      email=user.email,
      full_name=user.full_name,
      password=auth.get_password_hash(user.password),
      role=user.role if user.role in ["admin", "editor", "user"] else "user",
  )
  db.add(new_user)
  db.commit()
  db.refresh(new_user)
  return new_user


@app.post("/auth/token", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
  user = (
      db.query(models.User)
      .filter(models.User.username == form_data.username)
      .first()
  )
  if not user or not auth.verify_password(form_data.password, user.password):
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
  access_token = auth.create_access_token(
      data={"sub": user.username},
      expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES),
  )
  return {"access_token": access_token, "token_type": "bearer"}


# --- User Management Endpoints ---
@app.get("/users/me", response_model=schemas.UserResponse)
def get_user_me(current_user: models.User = Depends(auth.get_current_user)):
  return current_user


@app.get("/users/", response_model=list[schemas.UserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    admin: models.User = Depends(auth.get_current_admin_user),
):
  return db.query(models.User).all()


@app.put("/users/me", response_model=schemas.UserResponse)
def update_user_me(
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
  if user_update.email:
    current_user.email = user_update.email
  if user_update.full_name:
    current_user.full_name = user_update.full_name
  if user_update.password:
    current_user.password = auth.get_password_hash(user_update.password)
  db.commit()
  db.refresh(current_user)
  return current_user


@app.delete("/users/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_me(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
  db.delete(current_user)
  db.commit()
  return None


# --- Notes Endpoints ---
@app.post(
    "/notes/",
    response_model=schemas.NoteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_note(
    note: schemas.NoteCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
  new_note = models.Note(
      title=note.title,
      content=note.content,
      owner=current_user.username,
      is_public=note.is_public,
      tags=note.tags,
  )
  db.add(new_note)
  db.commit()
  db.refresh(new_note)
  return new_note


@app.get("/notes/", response_model=list[schemas.NoteResponse])
def get_notes(
    tag: str | None = Query(None),
    search_term: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
  query = db.query(models.Note)

  # Regular users see only their own notes or public notes; admins see all notes[span_9](start_span)[span_9](end_span)
  if current_user.role != "admin":
    query = query.filter(
        (models.Note.owner == current_user.username)
        | (models.Note.is_public == True)
    )

  if search_term:
    query = query.filter(
        (models.Note.title.ilike(f"%{search_term}%"))
        | (models.Note.content.ilike(f"%{search_term}%"))
    )

  notes = query.all()
  if tag:
    notes = [n for n in notes if tag.lower() in [t.lower() for t in n.tags]]
  return notes


@app.get("/notes/{note_id}", response_model=schemas.NoteResponse)
def get_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
  note = db.query(models.Note).filter(models.Note.id == note_id).first()
  if not note:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
    )

  # Check permissions: owner, admin, or public[span_10](start_span)[span_10](end_span)
  if (
      note.owner != current_user.username
      and current_user.role != "admin"
      and not note.is_public
  ):
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
    )

  return note


@app.put("/notes/{note_id}", response_model=schemas.NoteResponse)
def update_note(
    note_id: int,
    note_update: schemas.NoteUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
  note = db.query(models.Note).filter(models.Note.id == note_id).first()
  if not note:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
    )

  # Owner or admin only[span_11](start_span)[span_11](end_span)
  if note.owner != current_user.username and current_user.role != "admin":
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
    )

  if note_update.title is not None:
    note.title = note_update.title
  if note_update.content is not None:
    note.content = note_update.content
  if note_update.is_public is not None:
    note.is_public = note_update.is_public
  if note_update.tags is not None:
    note.tags = note_update.tags

  db.commit()
  db.refresh(note)
  return note


@app.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
  note = db.query(models.Note).filter(models.Note.id == note_id).first()
  if not note:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
    )

  # Owner or admin only[span_12](start_span)[span_12](end_span)
  if note.owner != current_user.username and current_user.role != "admin":
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
    )

  db.delete(note)
  db.commit()
  return None
