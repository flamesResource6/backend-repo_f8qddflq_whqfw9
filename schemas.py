"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- UserProfile -> "userprofile" collection
- Highlight -> "highlight" collection
- Bookmark -> "bookmark" collection
- Note -> "note" collection
- ReadingProgress -> "readingprogress" collection
- Plan -> "plan" collection
- VersePlaylist -> "verseplaylist" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class UserProfile(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    name: Optional[str] = Field(None)
    email: Optional[str] = Field(None)
    avatar_url: Optional[str] = Field(None)
    preferred_translation: str = Field("ESV", description="Default Bible translation")
    preferred_language: str = Field("en", description="Language code")
    theme: str = Field("dark", description="Theme: dark | light | sepia")
    dyslexia_font: bool = Field(False)
    streak_days: int = Field(0)
    last_read_date: Optional[str] = Field(None, description="ISO date string")

class Highlight(BaseModel):
    user_id: str
    reference: str = Field(..., description="Bible reference like John 3:16")
    translation: str = Field(...)
    color: str = Field("yellow")
    note: Optional[str] = None

class Bookmark(BaseModel):
    user_id: str
    reference: str
    translation: str
    label: Optional[str] = None

class Note(BaseModel):
    user_id: str
    reference: str
    translation: str
    content: str

class ReadingProgress(BaseModel):
    user_id: str
    plan_id: Optional[str] = None
    reference: str
    percentage: float = Field(0, ge=0, le=100)

class Plan(BaseModel):
    user_id: str
    title: str
    description: Optional[str] = None
    references: List[str] = Field(default_factory=list)
    schedule: Optional[Dict[str, List[str]]] = None

class VersePlaylist(BaseModel):
    user_id: str
    title: str
    mood: Optional[str] = None
    theme: Optional[str] = None
    references: List[str] = Field(default_factory=list)
