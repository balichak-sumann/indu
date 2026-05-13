"""
Database initialization and models
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)


class Conversation(Base):
    """Conversation model"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    session_id = Column(String(255), unique=True)
    language = Column(String(50), default="en")
    personality = Column(String(50), default="assistant")
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)


class Message(Base):
    """Message model"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer)
    role = Column(String(50))  # user, assistant, system
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)


class AudioLog(Base):
    """Audio log model"""
    __tablename__ = "audio_logs"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer)
    duration = Column(Float)
    file_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
