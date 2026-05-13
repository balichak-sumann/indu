"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ConversationRole(str, Enum):
    """Role in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Language(str, Enum):
    """Supported languages"""
    ENGLISH = "en"
    HINDI = "hi"
    HINGLISH = "hinglish"
    TELUGU = "te"


class Personality(str, Enum):
    """AI personality types"""
    THERAPIST = "therapist"
    MENTOR = "mentor"
    ASSISTANT = "assistant"
    SALES = "sales"
    STORYTELLER = "storyteller"
    STUDY_BUDDY = "study_buddy"


class SessionCreate(BaseModel):
    """Session creation request"""
    user_id: Optional[str] = None
    language: Language = Language.ENGLISH
    personality: Personality = Personality.ASSISTANT
    name: Optional[str] = None


class SessionResponse(BaseModel):
    """Session response"""
    session_id: str
    user_id: Optional[str]
    created_at: datetime
    language: Language
    personality: Personality
    status: str = "active"


class MessageRequest(BaseModel):
    """Message request"""
    session_id: str
    content: str
    message_type: str = "text"


class TranscriptionMessage(BaseModel):
    """Transcription message from STT"""
    session_id: str
    text: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    language: Optional[Language] = None
    is_final: bool = False


class LLMResponseMessage(BaseModel):
    """LLM response message"""
    session_id: str
    content: str
    personality: Personality


class AudioChunk(BaseModel):
    """Audio chunk data"""
    session_id: str
    chunk_data: str  # base64 encoded
    sequence_number: int


class ConversationMessage(BaseModel):
    """Conversation message in memory"""
    role: ConversationRole
    content: str
    timestamp: datetime
    language: Optional[Language] = None


class ConversationHistory(BaseModel):
    """Conversation history"""
    session_id: str
    messages: List[ConversationMessage]
    user_preferences: Optional[Dict[str, Any]] = None
    emotional_context: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    details: Optional[str] = None
    error_code: Optional[str] = None
