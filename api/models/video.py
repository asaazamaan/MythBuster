from sqlmodel import SQLModel, Field
from typing import Optional, List
import datetime
from sqlalchemy import Column, JSON

class Video(SQLModel, table=True):
    __tablename__ = "Video"

    videoID: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(max_length=500, unique=True, nullable=False)
    title: Optional[str] = Field(default=None, max_length=200)
    transcription: Optional[str] = Field(default=None)
    claims: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    processed_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))