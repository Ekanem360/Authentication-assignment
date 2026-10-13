import json
from datetime import datetime
from database import Base
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text


class User(Base):
  __tablename__ = "users"

  username = Column(String, primary_key=True, index=True)
  email = Column(String, unique=True, index=True, nullable=False)
  full_name = Column(String, nullable=True)
  password = Column(String, nullable=False)
  disabled = Column(Boolean, default=False)
  role = Column(String, default="user")


class Note(Base):
  __tablename__ = "notes"

  id = Column(Integer, primary_key=True, index=True, autoincrement=True)
  title = Column(String, nullable=False)
  content = Column(Text, nullable=False)
  owner = Column(String, index=True, nullable=False)
  is_public = Column(Boolean, default=False)
  created_at = Column(DateTime, default=datetime.utcnow)
  tags_json = Column(String, default="[]")

  @property
  def tags(self):
    try:
      return json.loads(self.tags_json)
    except Exception:
      return []

  @tags.setter
  def tags(self, value):
    self.tags_json = json.dumps(value if value else [])
