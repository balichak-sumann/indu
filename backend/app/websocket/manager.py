"""
WebSocket Connection Manager
Real-time conversation pipeline: STT → Streaming LLM → Parallel TTS
Optimized for minimal latency (sentence-level TTS pipelining)
"""

import base64
import json
import logging
import asyncio
from typing import Dict, List
from datetime import datetime
from fastapi import WebSocket

from app.ai.sarvam import stt, llm, tts

logger = logging.getLogger(__name__)


# Filler words that don't need AI response (all Indian languages)
FILLER_WORDS = {
    # English
    "hmm", "hm", "um", "uh", "ah", "oh", "okay", "ok", "yeah",
    "yes", "no", "hmm hmm", "uh huh", "mm", "mhm", "huh",
    "right", "sure", "yep", "nope", "alright", "fine", "got it",
    "i see", "wow", "cool", "nice", "great",
    # Hindi
    "accha", "acha", "haan", "ha", "nahi", "theek", "theek hai",
    "sahi", "sahi hai", "bas", "chalo", "hmm hmm", "ji", "ji haan",
    "are", "arre", "oho", "wah", "kya", "han",
    # Telugu
    "avunu", "kadha", "sare", "ok", "emo", "adhi", "ala",
    "hmm ala", "antha", "mari", "le", "ra", "ey",
    # Tamil
    "aamaa", "seri", "illa", "poda", "da", "di", "pa",
    # Kannada
    "howdu", "illa", "sari", "aitu", "ri",
    # Bengali
    "achha", "hya", "na", "toh", "ki",
    # Marathi
    "ho", "nahi", "bara", "chalel",
    # Gujarati
    "ha", "na", "saru", "thik", "bhai",
    # Common
    "arey", "yaar", "bhai", "dude", "like", "so",
}


class SessionState:
    """Represents a session state"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.is_recording = False
        self.is_ai_speaking = False
        self.interrupted = False
        self.product_config = None
        self.audio_buffer: List[bytes] = []
        self.conversation_history: List[dict] = []
        self.language = "en"
        self.personality = "assistant"
        self._tts_task = None  # Track ongoing TTS task for cancellation

    def update_activity(self):
        self.last_activity = datetime.now()

    def add_message(self, role: str, content: str):
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })


class ConnectionManager:
    """Manages WebSocket connections and real-time conversation pipeline"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_states: Dict[str, SessionState] = {}

    async def connect(self, websocket: WebSocket, session_id: str) -> None:
        await websocket.accept()
        self.active_connections[session_id] = websocket
        if session_id not in self.session_states:
            self.session_states[session_id] = SessionState(session_id)
        logger.info(f"📱 Connected: {session_id}")

    def disconnect(self, session_id: str) -> None:
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"📴 Disconnected: {session_id}")

    async def send_personal(self, session_id: str, message: dict) -> None:
        if session_id in self.active_connections:
            try:
                websocket = self.active_connections[session_id]
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Send error {session_id}: {str(e)}")
                self.disconnect(session_id)

    async def handle_start_session(self, session_id: str, data: dict) -> None:
        """Handle session start - configure and optionally initiate sales call"""
        try:
            session = self.session_states[session_id]
            session.language = data.get("language", "en")
            session.personality = data.get("personality", "assistant")
            session.product_config = data.get("productConfig", None)

            logger.info(f"🎯 Session started: {session_id} | Lang: {session.language}")

            await self.send_personal(session_id, {
                "event": "session_started",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
            })

            # AI initiates the sales call
            if session.product_config:
                await self._initiate_sales_call(session_id, session)

        except Exception as e:
            logger.error(f"Error starting session: {str(e)}")

    async def _initiate_sales_call(self, session_id: str, session):
        """AI initiates conversation with product greeting"""
        try:
            pc = session.product_config
            product_name = pc.get("productName", "our product")
            company_name = pc.get("companyName", "our company")
            language = pc.get("language", "en")

            opening_prompt = (
                f"You are calling a potential customer to introduce {product_name} from {company_name}. "
                f"Start with a warm greeting and briefly introduce yourself. Keep it to 1-2 sentences max. "
                f"Be natural like a real phone call."
            )

            # Generate greeting (non-streaming for simplicity)
            ai_greeting = await llm.generate_response(
                prompt=opening_prompt,
                context=[],
                personality="sales",
                language=language,
            )

            if ai_greeting:
                session.add_message("assistant", ai_greeting)

                # Send text
                await self.send_personal(session_id, {
                    "event": "ai_response",
                    "text": ai_greeting,
                    "timestamp": datetime.now().isoformat(),
                })

                # Generate and send audio
                detected_lang = "en-IN"
                if language == "hi":
                    detected_lang = "hi-IN"
                elif language == "te":
                    detected_lang = "te-IN"

                session.is_ai_speaking = True
                audio_b64 = await tts.synthesize_speech(ai_greeting.strip(), detected_lang)
                if audio_b64 and not session.interrupted:
                    await self.send_personal(session_id, {
                        "event": "ai_audio",
                        "audio": audio_b64,
                        "format": "mp3",
                        "sequence": 0,
                    })

                session.is_ai_speaking = False
                await self.send_personal(session_id, {
                    "event": "processing_complete",
                    "timestamp": datetime.now().isoformat(),
                })

        except Exception as e:
            logger.error(f"Error initiating sales call: {str(e)}")

    async def handle_audio_chunk(self, session_id: str, data: dict) -> None:
        """Buffer incoming audio chunk"""
        try:
            chunk_data = data.get("data")
            session = self.session_states[session_id]
            session.is_recording = True
            session.update_activity()

            if chunk_data:
                audio_bytes = base64.b64decode(chunk_data)
                session.audio_buffer.append(audio_bytes)

            await self.send_personal(session_id, {
                "event": "audio_received",
                "sequence": data.get("sequence", 0),
            })
        except Exception as e:
            logger.error(f"Audio chunk error: {str(e)}")

    async def handle_stop_audio(self, session_id: str) -> None:
        """
        Process buffered audio through the pipeline:
        STT → LLM (sentence by sentence) → Parallel TTS → Audio chunks
        
        Runs as a cancellable task so interruptions can abort it immediately.
        """
        session = self.session_states[session_id]
        
        # Cancel any ongoing processing task
        if session._tts_task and not session._tts_task.done():
            session._tts_task.cancel()
            try:
                await session._tts_task
            except (asyncio.CancelledError, Exception):
                pass

        # Start new processing as a task
        session._tts_task = asyncio.create_task(
            self._process_audio_pipeline(session_id)
        )

    async def _process_audio_pipeline(self, session_id: str) -> None:
        """The actual audio processing pipeline (runs as cancellable task)"""
        try:
            session = self.session_states[session_id]
            session.is_recording = False
            session.interrupted = False
            session.update_activity()

            if not session.audio_buffer:
                await self.send_personal(session_id, {
                    "event": "error",
                    "message": "No audio data received",
                })
                return

            combined_audio = b"".join(session.audio_buffer)
            session.audio_buffer = []

            logger.info(f"📦 Processing {len(combined_audio)} bytes audio")

            # === STEP 1: STT ===
            await self.send_personal(session_id, {
                "event": "status", "stage": "transcribing",
            })

            stt_result = await stt.transcribe_audio(combined_audio, session.language)
            transcript = stt_result.get("text", "").strip()
            detected_language = stt_result.get("language_code", "en-IN")

            if not transcript:
                await self.send_personal(session_id, {
                    "event": "error",
                    "message": "Could not understand. Please speak again.",
                })
                return

            # Send transcription
            await self.send_personal(session_id, {
                "event": "transcription",
                "text": transcript,
                "is_final": True,
            })

            # Filter filler words
            transcript_lower = transcript.lower().strip().rstrip('.!?,')
            if transcript_lower in FILLER_WORDS or len(transcript_lower) < 2:
                logger.info(f"⏭️ Skipping filler: '{transcript}'")
                await self.send_personal(session_id, {
                    "event": "processing_complete",
                    "timestamp": datetime.now().isoformat(),
                })
                return

            session.add_message("user", transcript)

            # === STEP 2: STREAMING LLM + PARALLEL TTS ===
            await self.send_personal(session_id, {
                "event": "status", "stage": "thinking",
            })

            # Build product context
            product_context = ""
            if session.product_config:
                pc = session.product_config
                product_context = (
                    f"\n[PRODUCT: {pc.get('productName', '')} by {pc.get('companyName', '')}. "
                    f"{pc.get('productDescription', '')} "
                    f"Features: {pc.get('keyFeatures', '')}. "
                    f"Price: {pc.get('pricing', '')}. "
                    f"Target: {pc.get('targetAudience', '')}]"
                )

            session.is_ai_speaking = True
            audio_sequence = 0

            # This callback fires for each complete sentence from LLM
            # It immediately starts TTS for that sentence (parallel processing)
            async def on_sentence_ready(sentence: str):
                nonlocal audio_sequence
                if session.interrupted:
                    return

                logger.info(f"📝 Sentence ready: '{sentence[:50]}...'")

                # Send status update on first sentence
                if audio_sequence == 0:
                    await self.send_personal(session_id, {
                        "event": "status", "stage": "speaking",
                    })

                # Generate TTS for this sentence immediately
                audio_b64 = await tts.synthesize_speech(sentence, detected_language)
                
                if audio_b64 and not session.interrupted:
                    await self.send_personal(session_id, {
                        "event": "ai_audio",
                        "audio": audio_b64,
                        "format": "mp3",
                        "sequence": audio_sequence,
                    })
                    audio_sequence += 1

            # Run streaming LLM - it calls on_sentence_ready for each sentence
            full_response = await llm.generate_response_streaming(
                prompt=transcript + product_context,
                context=session.conversation_history[:-1],
                personality=session.personality,
                language=session.language,
                sentence_callback=on_sentence_ready,
            )

            # Add full response to history
            session.add_message("assistant", full_response)

            # Send full text response
            await self.send_personal(session_id, {
                "event": "ai_response",
                "text": full_response,
                "timestamp": datetime.now().isoformat(),
            })

            session.is_ai_speaking = False

            await self.send_personal(session_id, {
                "event": "processing_complete",
                "timestamp": datetime.now().isoformat(),
            })

        except asyncio.CancelledError:
            logger.info(f"🛑 Pipeline cancelled (interrupted): {session_id}")
            session = self.session_states[session_id]
            session.is_ai_speaking = False
        except Exception as e:
            logger.error(f"Pipeline error for {session_id}: {str(e)}", exc_info=True)
            await self.send_personal(session_id, {
                "event": "error",
                "message": f"Processing error: {str(e)}",
            })

    async def handle_interrupt(self, session_id: str) -> None:
        """Handle user interrupt - cancel ongoing pipeline and stop AI immediately"""
        try:
            session = self.session_states[session_id]
            session.is_ai_speaking = False
            session.interrupted = True
            session.update_activity()

            # Cancel the running pipeline task
            if session._tts_task and not session._tts_task.done():
                session._tts_task.cancel()

            logger.info(f"🛑 Interrupted: {session_id}")

            await self.send_personal(session_id, {
                "event": "interrupt_acknowledged",
                "timestamp": datetime.now().isoformat(),
            })
        except Exception as e:
            logger.error(f"Interrupt error: {str(e)}")

    async def close_all(self) -> None:
        sessions = list(self.active_connections.keys())
        for session_id in sessions:
            try:
                websocket = self.active_connections[session_id]
                await websocket.close()
            except Exception:
                pass
            finally:
                self.disconnect(session_id)

    def get_session_count(self) -> int:
        return len(self.active_connections)

    def get_session_info(self, session_id: str) -> dict:
        if session_id not in self.session_states:
            return {}
        session = self.session_states[session_id]
        return {
            "session_id": session_id,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "is_recording": session.is_recording,
            "is_ai_speaking": session.is_ai_speaking,
            "language": session.language,
        }
