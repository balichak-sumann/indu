"""
Real-time streaming services using Sarvam WebSocket APIs
- Streaming STT via WebSocket
- Streaming TTS via WebSocket
"""

import asyncio
import base64
import json
import logging
import aiohttp

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RealtimeSTT:
    """Stream audio to Sarvam STT WebSocket and get transcription"""

    def __init__(self):
        self.api_key = settings.SARVAM_API_KEY
        self.ws_url = "wss://api.sarvam.ai/speech-to-text/ws"

    async def transcribe_stream(self, audio_data: bytes) -> str:
        """
        Send audio via WebSocket for faster transcription
        Falls back to REST if WebSocket fails
        """
        headers = {
            "api-subscription-key": self.api_key,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(
                    self.ws_url,
                    headers=headers,
                    timeout=aiohttp.ClientWSTimeout(ws_close=10)
                ) as ws:
                    # Send config
                    await ws.send_json({
                        "config": {
                            "language_code": "unknown",
                            "model": "saaras:v3",
                            "mode": "transcribe",
                        }
                    })

                    # Send audio data
                    audio_b64 = base64.b64encode(audio_data).decode('utf-8')
                    await ws.send_json({
                        "audio": {
                            "data": audio_b64,
                            "sample_rate": "16000",
                            "encoding": "audio/wav",
                        }
                    })

                    # Send end signal
                    await ws.send_json({"event": "end"})

                    # Wait for transcription
                    transcript = ""
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            if data.get("type") == "data":
                                transcript = data.get("data", {}).get("transcript", "")
                                break
                            elif data.get("type") == "error":
                                logger.error(f"STT WS error: {data}")
                                break
                        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            break

                    if transcript:
                        logger.info(f"STT WS result: '{transcript[:50]}...'")
                    return transcript

        except Exception as e:
            logger.warning(f"STT WebSocket failed: {e}, falling back to REST")
            return ""


class RealtimeTTS:
    """Stream text to Sarvam TTS WebSocket and get audio chunks"""

    def __init__(self):
        self.api_key = settings.SARVAM_API_KEY
        self.ws_url = "wss://api.sarvam.ai/text-to-speech/ws"

    async def synthesize_stream(self, text: str, language: str = "en-IN", callback=None):
        """
        Send text via WebSocket TTS and call callback with each audio chunk
        Returns full audio if no callback provided
        """
        headers = {
            "api-subscription-key": self.api_key,
        }

        # Map language
        if "-" not in language:
            lang_map = {"en": "en-IN", "hi": "hi-IN", "te": "te-IN"}
            language = lang_map.get(language, "en-IN")

        all_audio = b""

        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(
                    self.ws_url,
                    headers=headers,
                    timeout=aiohttp.ClientWSTimeout(ws_close=15)
                ) as ws:
                    # Send config
                    await ws.send_json({
                        "type": "config",
                        "data": {
                            "target_language_code": language,
                            "speaker": "suhani",
                            "model": "bulbul:v3",
                            "pace": 1.2,
                        }
                    })

                    # Send text
                    await ws.send_json({
                        "type": "text",
                        "data": {
                            "text": text,
                        }
                    })

                    # Send end signal
                    await ws.send_json({"type": "end"})

                    # Receive audio chunks
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            if data.get("type") == "audio":
                                audio_b64 = data.get("data", {}).get("audio", "")
                                if audio_b64:
                                    audio_bytes = base64.b64decode(audio_b64)
                                    all_audio += audio_bytes
                                    if callback:
                                        await callback(audio_b64)
                            elif data.get("type") == "end":
                                break
                            elif data.get("type") == "error":
                                logger.error(f"TTS WS error: {data}")
                                break
                        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            break

                    if all_audio:
                        logger.info(f"TTS WS: {len(all_audio)} bytes audio")
                        if not callback:
                            return base64.b64encode(all_audio).decode('utf-8')
                    return ""

        except Exception as e:
            logger.warning(f"TTS WebSocket failed: {e}")
            return ""


# Singletons
realtime_stt = RealtimeSTT()
realtime_tts = RealtimeTTS()
