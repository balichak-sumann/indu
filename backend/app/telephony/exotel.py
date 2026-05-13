"""
Exotel Bidirectional WebSocket Integration
Handles real-time voice calls via Exotel's Voicebot applet.

Protocol:
- Exotel sends: connected, start, media, dtmf, stop, mark events
- We send back: media (audio), mark, clear events
- Audio format: raw/slin 16-bit PCM (little-endian), base64 encoded
- Default sample rate: 8kHz (can request 16kHz via query param)
"""

import asyncio
import base64
import json
import logging
import struct
import io
import aiohttp
from typing import Optional
from fastapi import WebSocket

from app.ai.sarvam import stt, llm, tts
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Filler words (same as websocket manager)
FILLER_WORDS = {
    "hmm", "hm", "um", "uh", "ah", "oh", "okay", "ok", "yeah",
    "yes", "no", "hmm hmm", "uh huh", "mm", "mhm", "huh",
    "right", "sure", "yep", "nope", "alright", "fine", "got it",
    "i see", "wow", "cool", "nice", "great",
    "accha", "acha", "haan", "ha", "nahi", "theek", "theek hai",
    "sahi", "sahi hai", "bas", "chalo", "ji", "ji haan",
    "are", "arre", "oho", "wah", "kya", "han",
    "avunu", "kadha", "sare", "emo", "adhi", "ala",
    "aamaa", "seri", "illa", "poda", "da", "di", "pa",
    "howdu", "illa", "sari", "aitu", "ri",
    "achha", "hya", "na", "toh", "ki",
    "ho", "nahi", "bara", "chalel",
    "ha", "na", "saru", "thik", "bhai",
    "arey", "yaar", "bhai", "dude", "like", "so",
}


class ExotelCallSession:
    """Manages a single Exotel voice call session"""

    def __init__(self, websocket: WebSocket, product_config: dict = None):
        self.websocket = websocket
        self.product_config = product_config
        self.stream_sid: Optional[str] = None
        self.call_sid: Optional[str] = None
        self.sample_rate: int = 8000  # Exotel default
        self.is_active = False
        self.is_ai_speaking = False
        self.interrupted = False
        self.audio_buffer = bytearray()
        self.silence_frames = 0
        self.speech_frames = 0
        self.is_speech_active = False
        self.conversation_history = []
        self.language = "en"
        self._processing_task: Optional[asyncio.Task] = None
        self._sequence_number = 0

        # VAD settings (tuned for telephony - phone audio has more noise)
        self.vad_threshold = 500  # Higher RMS threshold for phone audio noise floor
        self.silence_duration_frames = 40  # ~1.3s of silence before ending speech
        self.min_speech_frames = 30  # ~1s minimum speech to avoid false triggers
        self.interrupt_min_frames = 15  # AI must be speaking 15+ frames before interrupt allowed
        self._ai_speaking_frames = 0  # Track how long AI has been speaking
        self._cooldown_frames = 0  # Cooldown after AI stops speaking
        self._cooldown_duration = 25  # ~800ms cooldown after AI audio ends

    async def handle_message(self, data: dict):
        """Route incoming Exotel WebSocket messages"""
        event = data.get("event")
        if event != "media":  # Don't log every media event (50/sec)
            logger.info(f"📞 Exotel event: {event}")

        try:
            if event == "connected":
                logger.info("📞 Exotel WebSocket connected")
                self.is_active = True

            elif event == "start":
                await self._handle_start(data)

            elif event == "media":
                await self._handle_media(data)

            elif event == "dtmf":
                digit = data.get("dtmf", {}).get("digit")
                logger.info(f"📱 DTMF: {digit}")

            elif event == "stop":
                reason = data.get("stop", {}).get("reason", "unknown")
                logger.info(f"📴 Call ended: {reason}")
                self.is_active = False

            elif event == "mark":
                name = data.get("mark", {}).get("name", "")
                if name == "ai_done":
                    self.is_ai_speaking = False
        except Exception as e:
            logger.error(f"Error handling event '{event}': {str(e)}", exc_info=True)

    async def _handle_start(self, data: dict):
        """Handle stream start - extract call info and send greeting"""
        start_info = data.get("start", {})
        self.stream_sid = start_info.get("stream_sid")
        self.call_sid = start_info.get("call_sid")

        media_format = start_info.get("media_format", {})
        self.sample_rate = int(media_format.get("sample_rate", 8000))

        # Extract custom params (product config passed via URL params)
        custom_params = start_info.get("custom_parameters", {})
        if custom_params.get("language"):
            self.language = custom_params["language"]

        logger.info(
            f"📞 Call started: {self.call_sid} | "
            f"From: {start_info.get('from')} → To: {start_info.get('to')} | "
            f"Sample rate: {self.sample_rate}Hz | Stream: {self.stream_sid}"
        )

        # Send greeting in background (don't block the message loop)
        asyncio.create_task(self._send_greeting_safe())

    async def _handle_media(self, data: dict):
        """Handle incoming audio from caller - VAD + buffer"""
        media = data.get("media", {})
        payload = media.get("payload", "")

        if not payload:
            return

        # Decode base64 PCM audio
        audio_bytes = base64.b64decode(payload)

        # Track AI speaking duration
        if self.is_ai_speaking:
            self._ai_speaking_frames += 1
            # Don't process caller audio while AI is speaking (echo suppression)
            # Only allow interrupt after AI has been speaking long enough
            rms = self._calculate_rms(audio_bytes)
            if rms > self.vad_threshold * 1.5 and self._ai_speaking_frames > self.interrupt_min_frames:
                # Strong speech detected during AI playback - interrupt
                self.speech_frames += 1
                if self.speech_frames >= 5:  # Need sustained speech to interrupt
                    await self._interrupt_ai()
                    self.speech_frames = 0
            else:
                self.speech_frames = 0
            return

        # Cooldown after AI stops speaking (avoid echo pickup)
        if self._cooldown_frames > 0:
            self._cooldown_frames -= 1
            return

        # Normal VAD when AI is not speaking
        rms = self._calculate_rms(audio_bytes)

        if rms > self.vad_threshold:
            # Speech detected
            self.speech_frames += 1
            self.silence_frames = 0

            if not self.is_speech_active and self.speech_frames >= 5:
                # Speech started (need 5 consecutive frames ~160ms)
                self.is_speech_active = True

            if self.is_speech_active:
                self.audio_buffer.extend(audio_bytes)
        else:
            # Silence
            self.silence_frames += 1

            if self.is_speech_active:
                self.audio_buffer.extend(audio_bytes)

                # Check if speech ended (enough silence after speech)
                if self.silence_frames >= self.silence_duration_frames:
                    if self.speech_frames >= self.min_speech_frames:
                        # Speech ended - process the audio
                        await self._process_speech()
                    else:
                        # Too short - discard
                        pass

                    # Reset
                    self.audio_buffer = bytearray()
                    self.is_speech_active = False
                    self.speech_frames = 0
                    self.silence_frames = 0
            else:
                self.speech_frames = 0

    def _calculate_rms(self, audio_bytes: bytes) -> float:
        """Calculate RMS energy of PCM audio"""
        if len(audio_bytes) < 2:
            return 0
        # 16-bit little-endian samples
        num_samples = len(audio_bytes) // 2
        total = 0
        for i in range(num_samples):
            sample = struct.unpack_from('<h', audio_bytes, i * 2)[0]
            total += sample * sample
        return (total / num_samples) ** 0.5

    async def _interrupt_ai(self):
        """Stop AI audio playback immediately"""
        self.is_ai_speaking = False
        self.interrupted = True
        self._ai_speaking_frames = 0
        self._cooldown_frames = self._cooldown_duration

        # Cancel ongoing processing
        if self._processing_task and not self._processing_task.done():
            self._processing_task.cancel()

        # Send clear event to Exotel to stop playing buffered audio
        await self._send_to_exotel({
            "event": "clear",
            "stream_sid": self.stream_sid,
        })
        logger.info("🛑 AI interrupted - cleared audio buffer")

    async def _process_speech(self):
        """Process captured speech through STT → LLM → TTS pipeline"""
        if not self.audio_buffer:
            return

        # Cancel any ongoing processing
        if self._processing_task and not self._processing_task.done():
            self._processing_task.cancel()
            try:
                await self._processing_task
            except (asyncio.CancelledError, Exception):
                pass

        # Copy buffer and start processing
        audio_data = bytes(self.audio_buffer)
        self.interrupted = False
        self._processing_task = asyncio.create_task(
            self._run_pipeline(audio_data)
        )

    async def _run_pipeline(self, audio_data: bytes):
        """Run the full STT → LLM → TTS pipeline"""
        try:
            # Convert 8kHz PCM to 16kHz WAV for Sarvam STT
            wav_data = self._pcm_to_wav(audio_data, self.sample_rate)

            # STT
            stt_result = await stt.transcribe_audio(wav_data, self.language)
            transcript = stt_result.get("text", "").strip()
            detected_language = stt_result.get("language_code", "en-IN")

            if not transcript:
                logger.info("📝 Empty transcription, skipping")
                return

            logger.info(f"📝 Caller said: '{transcript}'")

            # Filter filler words
            transcript_lower = transcript.lower().strip().rstrip('.!?,')
            if transcript_lower in FILLER_WORDS or len(transcript_lower) < 2:
                logger.info(f"⏭️ Skipping filler: '{transcript}'")
                return

            self.conversation_history.append({"role": "user", "content": transcript})

            # Build product context
            product_context = ""
            if self.product_config:
                pc = self.product_config
                product_context = (
                    f"\n[PRODUCT: {pc.get('productName', '')} by {pc.get('companyName', '')}. "
                    f"{pc.get('productDescription', '')} "
                    f"Features: {pc.get('keyFeatures', '')}. "
                    f"Price: {pc.get('pricing', '')}. "
                    f"Target: {pc.get('targetAudience', '')}]"
                )

            # LLM
            self.is_ai_speaking = True

            async def on_sentence_ready(sentence: str):
                if self.interrupted:
                    return
                # Get PCM audio directly (no ffmpeg needed)
                pcm_data = await self._tts_to_pcm(sentence, detected_language)
                if pcm_data and not self.interrupted:
                    await self._send_audio_to_caller(pcm_data)
                elif not self.interrupted:
                    # Fallback: try MP3 → PCM conversion
                    audio_b64 = await tts.synthesize_speech(sentence, detected_language)
                    if audio_b64:
                        pcm_data = await self._mp3_to_pcm(audio_b64)
                        if pcm_data and not self.interrupted:
                            await self._send_audio_to_caller(pcm_data)

            full_response = await llm.generate_response_streaming(
                prompt=transcript + product_context,
                context=self.conversation_history[:-1],
                personality="sales",
                language=self.language,
                sentence_callback=on_sentence_ready,
            )

            self.conversation_history.append({"role": "assistant", "content": full_response})

            # Send mark to know when audio finishes playing
            if not self.interrupted:
                await self._send_to_exotel({
                    "event": "mark",
                    "stream_sid": self.stream_sid,
                    "mark": {"name": "ai_done"},
                })

            logger.info(f"🤖 AI responded: '{full_response[:60]}...'")

        except asyncio.CancelledError:
            logger.info("🛑 Pipeline cancelled (interrupted)")
            self.is_ai_speaking = False
        except Exception as e:
            logger.error(f"Pipeline error: {str(e)}", exc_info=True)
            self.is_ai_speaking = False

    async def _send_greeting_safe(self):
        """Wrapper to catch errors in greeting so they don't crash the session"""
        try:
            await asyncio.sleep(0.5)
            await self._send_greeting()
        except Exception as e:
            logger.error(f"Greeting error: {str(e)}", exc_info=True)

    async def _send_greeting(self):
        """AI initiates the conversation"""
        # Default greeting if no product config
        if not self.product_config or not self.product_config.get("productName"):
            greeting = "Hello! This is your AI sales assistant. How can I help you today?"
        else:
            pc = self.product_config
            product_name = pc.get("productName", "our product")
            company_name = pc.get("companyName", "our company")

            opening_prompt = (
                f"You are calling a potential customer to introduce {product_name} from {company_name}. "
                f"Start with a warm greeting and briefly introduce yourself. Keep it to 1-2 sentences max. "
                f"Be natural like a real phone call."
            )

            greeting = await llm.generate_response(
                prompt=opening_prompt,
                context=[],
                personality="sales",
                language=self.language,
            )

        if greeting:
            self.conversation_history.append({"role": "assistant", "content": greeting})
            logger.info(f"🤖 Greeting: '{greeting[:60]}...'")

            # Determine TTS language
            detected_lang = "en-IN"
            if self.language == "hi":
                detected_lang = "hi-IN"
            elif self.language == "te":
                detected_lang = "te-IN"

            # Get PCM audio directly (no ffmpeg needed)
            self.is_ai_speaking = True
            pcm_data = await self._tts_to_pcm(greeting, detected_lang)
            if pcm_data:
                await self._send_audio_to_caller(pcm_data)
            else:
                logger.warning("TTS PCM failed for greeting, trying MP3 fallback")
                audio_b64 = await tts.synthesize_speech(greeting, detected_lang)
                if audio_b64:
                    pcm_data = await self._mp3_to_pcm(audio_b64)
                    if pcm_data:
                        await self._send_audio_to_caller(pcm_data)

            await self._send_to_exotel({
                "event": "mark",
                "stream_sid": self.stream_sid,
                "mark": {"name": "ai_done"},
            })

    async def _send_audio_to_caller(self, pcm_data: bytes):
        """Send PCM audio to Exotel in chunks"""
        # Send in chunks of 640 bytes (20ms at 8kHz, 16-bit)
        chunk_size = 640
        self._sequence_number += 1
        self._ai_speaking_frames = 0

        for i in range(0, len(pcm_data), chunk_size):
            if self.interrupted:
                break
            chunk = pcm_data[i:i + chunk_size]
            # Pad last chunk if needed
            if len(chunk) < chunk_size:
                chunk = chunk + b'\x00' * (chunk_size - len(chunk))

            payload = base64.b64encode(chunk).decode('utf-8')
            await self._send_to_exotel({
                "event": "media",
                "stream_sid": self.stream_sid,
                "media": {
                    "payload": payload,
                },
            })
            # Small delay to prevent overwhelming the connection
            await asyncio.sleep(0.018)  # ~18ms per chunk

        # Set cooldown after AI finishes speaking
        if not self.interrupted:
            self._cooldown_frames = self._cooldown_duration
            self.is_ai_speaking = False

    async def _mp3_to_pcm(self, mp3_base64: str) -> Optional[bytes]:
        """
        Convert MP3 (base64) to raw PCM (8kHz, 16-bit, mono) for Exotel.
        Uses ffmpeg if available, otherwise tries pydub/audioop fallback.
        """
        try:
            import shutil
            import glob
            mp3_bytes = base64.b64decode(mp3_base64)

            # Find ffmpeg
            ffmpeg_path = shutil.which("ffmpeg")
            if not ffmpeg_path:
                # Check common install locations
                patterns = [
                    "/usr/bin/ffmpeg",
                    "/usr/local/bin/ffmpeg",
                    r"C:\Users\*\AppData\Local\Microsoft\WinGet\Packages\*ffmpeg*\*\bin\ffmpeg.exe",
                    r"C:\ffmpeg\bin\ffmpeg.exe",
                ]
                for pattern in patterns:
                    matches = glob.glob(pattern)
                    if matches:
                        ffmpeg_path = matches[0]
                        break

            if ffmpeg_path:
                process = await asyncio.create_subprocess_exec(
                    ffmpeg_path, '-i', 'pipe:0',
                    '-f', 's16le', '-acodec', 'pcm_s16le',
                    '-ar', str(self.sample_rate), '-ac', '1',
                    'pipe:1',
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await process.communicate(input=mp3_bytes)

                if process.returncode == 0 and stdout:
                    return stdout
                else:
                    logger.warning(f"ffmpeg failed: {stderr.decode()[:100]}")

            # Fallback: use Sarvam TTS with WAV output directly
            logger.warning("ffmpeg not available, using WAV TTS fallback")
            return None
        except Exception as e:
            logger.error(f"Audio conversion error: {str(e)}")
            return None

    async def _tts_to_pcm(self, text: str, language: str) -> Optional[bytes]:
        """
        Get TTS audio as raw PCM directly (no ffmpeg needed).
        Uses Sarvam's REST endpoint which returns WAV when requested.
        """
        try:
            from app.config import get_settings
            settings = get_settings()

            url = f"{settings.SARVAM_API_BASE_URL}/text-to-speech"
            headers = {
                "api-subscription-key": settings.SARVAM_API_KEY,
                "Content-Type": "application/json",
            }
            payload = {
                "text": text[:2500],
                "target_language_code": language if "-" in language else "en-IN",
                "speaker": "suhani",
                "model": "bulbul:v3",
                "pace": 1.2,
                "speech_sample_rate": str(self.sample_rate),
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        audios = result.get("audios", [])
                        if audios:
                            # This is base64 WAV audio - decode and extract PCM
                            wav_bytes = base64.b64decode(audios[0])
                            # Skip WAV header (44 bytes) to get raw PCM
                            if wav_bytes[:4] == b'RIFF':
                                return wav_bytes[44:]
                            return wav_bytes
                    else:
                        error = await response.text()
                        logger.error(f"TTS PCM error ({response.status}): {error[:100]}")
            return None
        except Exception as e:
            logger.error(f"TTS PCM failed: {str(e)}")
            return None

    def _pcm_to_wav(self, pcm_data: bytes, sample_rate: int) -> bytes:
        """Convert raw PCM to WAV format for Sarvam STT"""
        num_channels = 1
        bits_per_sample = 16
        byte_rate = sample_rate * num_channels * (bits_per_sample // 8)
        block_align = num_channels * (bits_per_sample // 8)
        data_size = len(pcm_data)

        wav = io.BytesIO()
        # RIFF header
        wav.write(b'RIFF')
        wav.write(struct.pack('<I', 36 + data_size))
        wav.write(b'WAVE')
        # fmt chunk
        wav.write(b'fmt ')
        wav.write(struct.pack('<I', 16))
        wav.write(struct.pack('<H', 1))  # PCM
        wav.write(struct.pack('<H', num_channels))
        wav.write(struct.pack('<I', sample_rate))
        wav.write(struct.pack('<I', byte_rate))
        wav.write(struct.pack('<H', block_align))
        wav.write(struct.pack('<H', bits_per_sample))
        # data chunk
        wav.write(b'data')
        wav.write(struct.pack('<I', data_size))
        wav.write(pcm_data)

        return wav.getvalue()

    async def _send_to_exotel(self, message: dict):
        """Send JSON message to Exotel WebSocket"""
        try:
            await self.websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending to Exotel: {str(e)}")
